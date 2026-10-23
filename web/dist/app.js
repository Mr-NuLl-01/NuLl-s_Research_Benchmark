'use strict';
const KEY = 'research-benchmark-prototype-v1';
const RELEASE = globalThis.NRB_RELEASE || {version:'2.0.0-rc.1',tasks:[],downloads:{},grading:null};
const tasks = Array.isArray(RELEASE.tasks) ? RELEASE.tasks : [];
const historicalTasks = typeof REAL_TASKS === 'undefined' ? [] : REAL_TASKS;
const readyTasks = tasks.filter(t => t.status === 'ready');
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const isObject = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const badge = (text, kind='neutral') => `<span class="badge ${esc(kind)}">${esc(text)}</span>`;
const scoreText = value => value === null || value === undefined ? '—' : Number(value).toFixed(2).replace(/\.00$/, '');
const head = (eyebrow,title,description,action='') => `<div class="page-heading"><div><h1>${esc(title)}</h1>${description?`<p class="muted">${esc(description)}</p>`:''}</div>${action}</div>`;
const empty = (title,description,action='') => `<div class="empty"><div class="empty-symbol" aria-hidden="true">∅</div><h3>${esc(title)}</h3><p>${esc(description)}</p>${action}</div>`;
const taskFor = id => tasks.find(t => t.id === id);
const legacyFor = id => historicalTasks.find(t => t.id === id);
const stateNames = {reviewed:'已评阅',passed:'检查全部通过',failed:'检查有失败',unscored:'未评分 · 检查未完成'};
const tierNames = {basic:'基础功能',scientific:'科学正确性',stress:'压力与边界'};
const unknown = value => !String(value ?? '').trim() || /^(未记录|未知|unknown|n\/a)$/i.test(String(value).trim());
let records = [], storageLoaded = false, storageOK = true, unreadableStorage = null;
let filter = {query:'',category:'',level:'',status:''}, historyFilter = {query:'',category:'',level:'',status:''};
let runFilter='all', selectedModels = new Set(), selectedCohort='';
let previousPage='', libraryScroll=0, historyScroll=0, confirmAction=null;
let reportReadToken=0, reviewReadToken=0;
let videoMode='';
const reviewDrafts={};
let localIdCounter=0;
let submission = {task:'',text:'',filename:'',error:'',result:null,report:null,metadata:{}};
try {
  unreadableStorage = localStorage.getItem(KEY);
  const parsed = JSON.parse(unreadableStorage || '[]');
  if (!Array.isArray(parsed)) throw new Error('存储不是记录数组');
  records = parsed; storageLoaded = true; unreadableStorage = null;
} catch (error) { storageOK = false; }
// IDs distinguish local records; they are not authentication tokens. In HTTP
// previews randomUUID may be absent even when getRandomValues is available.
function newRecordId() {
  const provider=globalThis.crypto;
  if(provider&&typeof provider.randomUUID==='function'){
    try{const id=provider.randomUUID();if(typeof id==='string'&&id&&!records.some(r=>r?.id===id))return id;}catch(_){}
  }
  const sequence=(++localIdCounter).toString(36);
  if(provider&&typeof provider.getRandomValues==='function'){
    try{const bytes=new Uint8Array(16);provider.getRandomValues(bytes);const entropy=Array.from(bytes,x=>x.toString(16).padStart(2,'0')).join('');return `local-${entropy}-${sequence}`;}catch(_){}
  }
  return `local-${Date.now().toString(36)}-${sequence}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
}
function today() {
  const parts = new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
  const read = type => parts.find(p => p.type === type).value;
  return `${read('year')}-${read('month')}-${read('day')}`;
}
function persist() {
  if (!storageLoaded) return false;
  try { localStorage.setItem(KEY,JSON.stringify(records)); storageOK=true; return true; }
  catch (error) { storageOK=false; return false; }
}
function toast(message) {
  $('#toast').textContent=message; $('#toast').style.display='block';
  clearTimeout(toast.timer); toast.timer=setTimeout(()=>$('#toast').style.display='none',5500);
}
function safeDrive(resource) {
  if (!resource || typeof resource.url !== 'string') return null;
  try { const u = new URL(resource.url); return u.protocol === 'https:' && u.hostname === 'drive.google.com' ? u.href : null; } catch (_) { return null; }
}
function driveLink(resource,label,primary=false) {
  const url=safeDrive(resource);
  return url ? `<a class="${primary?'primary':'secondary'}" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} <span aria-hidden="true">↗</span><span class="sr-only">（在新标签页打开 Google Drive）</span></a>` : `<span class="secondary unavailable" aria-disabled="true">${esc(label)} · 暂未就绪</span>`;
}
function taskResource(task, historical=false) {
  const d=RELEASE.downloads||{};
  return historical ? (d.legacy?.[task.id] || task.media || d.legacyBundle) : (d.tasks?.[task.id] || task.download);
}
function packetPath(task) {
  const p=task?.packet;
  return typeof p==='string' && /^(packets|packets-v2)\/[A-Za-z0-9_.\/-]+$/.test(p) && !p.includes('..') ? p : null;
}
function gradeRecord(record){
  if(!isObject(record)||record.schema!=='nrb-browser-run-v3')return null;
  if(!record.rawReport)return {valid:false,error:'缺少原始报告或评阅记录。',score:null,status:'unscored'};
  try{const g=validateRawReport(record.rawReport);if(record.task&&record.task!==g.taskId)throw Error('记录题号与报告不一致。');return {valid:true,...g};}
  catch(error){return {valid:false,error:error.message,score:null,status:'unscored'};}
}
function currentRecords() { return records.filter(r => isObject(r) && r.schema === 'nrb-browser-run-v3'); }
function taskTitle(record) { return (record?.schema==='nrb-browser-run-v3'?taskFor(record.task):legacyFor(record?.task))?.title || record?.task || '未识别历史记录'; }
function recordStatus(record) {
  const g=gradeRecord(record);
  if (g) return g.valid ? badge(g.controlOnly?'验证器自检':g.reviewerKind==='llm_provisional'?'LLM 暂评':g.protocolEligible===false?'模式不符':stateNames[g.status],g.controlOnly?'demo':g.status==='passed'||g.status==='reviewed'?'success':g.status==='failed'?'failure':'neutral') : badge('报告需重新验证','failure');
  return badge('历史手工记录','neutral');
}
function recordScore(record) {
  const g=gradeRecord(record);
  if (g) return g.valid ? scoreText(g.score) : '—';
  return record?.scoreState==='scored' && typeof record.score==='number' && Number.isFinite(record.score) ? `${scoreText(record.score)} · 历史草稿` : '未评分';
}
function navigate(hash) { if (location.hash===hash) render(); else location.hash=hash; }
function route() {
  const raw=location.hash.slice(1)||'overview';
  const [page,...rest]=raw.split('/');
  return {page,id:decodeURIComponent(rest.join('/'))};
}
function render() {
  // A pending review import belongs to the form instance that started it.
  // Replacing that form, including leaving and returning, ends that import.
  reviewReadToken++;
  let r;
  try { r=route(); } catch (_) { r={page:'overview',id:''}; }
  if(previousPage==='library') libraryScroll=window.scrollY||0;
  if(previousPage==='history') historyScroll=window.scrollY||0;
  const names={overview:'总览',library:'分级题库',task:'题目详情',history:'V1.1 历史题库',historical:'历史题目',submit:'提交与评分',runs:'测试记录',run:'测试详情',compare:'模型比较',guide:'使用指南'};
  if(!names[r.page]) r={page:'overview',id:''};
  $('#breadcrumb').textContent=names[r.page];
  const active=r.page==='task'||r.page==='submit'?'library':r.page==='run'?'runs':r.page==='historical'?'history':r.page;
  document.querySelectorAll('[data-page]').forEach(a=>{a.classList.toggle('active',a.dataset.page===active); if(a.dataset.page===active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  $('#run-count').textContent=records.length;
  const views={overview,library:()=>library(false),history:()=>library(true),task:()=>taskDetail(r.id,false),historical:()=>taskDetail(r.id,true),submit:()=>submissionPage(r.id),runs,run:()=>runDetail(Number(r.id)),compare,guide};
  $('#main').innerHTML=views[r.page]();
  if(!storageOK) $('#main').insertAdjacentHTML('afterbegin',`<div class="notice error-banner" role="alert">浏览器记录${storageLoaded?'写入失败，当前改动可能仅在内存中':'无法读取，原始内容仍被保留，当前不会覆盖它'}。请先<button class="text-button" data-export>导出备份</button>。${!storageLoaded?'可在可用的浏览器中导入备份恢复。':''}</div>`);
  bindPage(r.page);
  previousPage=r.page;
  if (typeof window.scrollTo==='function') window.scrollTo(0,r.page==='library'?libraryScroll:r.page==='history'?historyScroll:0);
  if (r.page==='task'||r.page==='historical') loadPacket(r.id,r.page==='historical');
}
function overview(){
 const live=currentRecords(),scored=live.map(gradeRecord).filter(g=>g?.valid&&g.score!==null&&!g.controlOnly).length;
 return head('','科研 AI 评测','', '<a class="primary" href="#library">选择题目 →</a>')+
 `<div class="stats"><div class="stat"><label>题目</label><span class="value">20</span></div><div class="stat"><label>自动评分</label><span class="value">13</span></div><div class="stat"><label>量表评阅</label><span class="value">7</span></div><div class="stat"><label>已评分记录</label><span class="value">${scored}</span></div></div>`+
 `<div class="category-grid">${[['Python','8 题','程序与科学计算'],['Fortran','3 题','守恒离散与耦合求解'],['Lean','1 题','已有结论的形式化'],['主观科研','6 题','绘图、写作、文献与视频'],['聊天端','2 题','交互网页与定量推理']].map(([cat,n,desc])=>`<button class="category-card" data-category-link="${esc(cat)}"><span>${esc(n)}</span><h2>${esc(cat)}</h2><b aria-hidden="true">↗</b></button>`).join('')}</div>`+
 `<section class="sample-strip"><div class="section-head"><h2>最近记录</h2><a href="#runs">全部记录 →</a></div>${live.length?recordTable(records.map((r,i)=>({r,i})).filter(x=>x.r?.schema==='nrb-browser-run-v3').slice(-4).reverse()):empty('还没有测试记录','选择一道题，完成作答后在题目页面提交。','<a class="secondary" href="#task/H02">试用网页直接评分 →</a>')}</section>`;
}
function library(historical=false){
 const f=historical?historyFilter:filter,list=historical?historicalTasks:tasks;
 return head('',historical?'历史题库':'题库',historical?'V1.1 材料按原协议保留。':'',historical?'<a class="secondary" href="#library">返回 V2</a>':'<a class="secondary" href="#guide">评分指南</a>')+
 `<div class="toolbar"><input class="search" id="search" type="search" aria-label="搜索题目" placeholder="搜索题目或能力" value="${esc(f.query)}"><select id="category" aria-label="类别"><option value="">全部类别</option>${[...new Set(list.map(t=>t.category))].map(c=>`<option value="${esc(c)}" ${f.category===c?'selected':''}>${esc(c)}</option>`).join('')}</select><select id="level" aria-label="设计难度"><option value="">全部难度</option>${['1/5','2/5','3/5','4/5','5/5'].map(l=>`<option ${f.level===l?'selected':''}>${l}</option>`).join('')}</select><button class="secondary" id="reset-filter">重置</button></div><div id="task-table">${taskTable(historical)}</div>`;
}
function taskTable(historical=false){
 const f=historical?historyFilter:filter,list=historical?historicalTasks:tasks;
 const rows=list.filter(t=>(!f.category||t.category===f.category)&&(!f.level||t.level===f.level)&&`${t.id} ${t.title} ${t.brief} ${t.category}`.toLowerCase().includes(f.query.toLowerCase()));
 return `<div class="table-wrap"><table class="task-table"><thead><tr><th>题目</th><th>类别</th><th>难度</th><th>评分</th><th></th></tr></thead><tbody>${rows.map(t=>`<tr><td><a class="task-button" href="#${historical?'historical':'task'}/${esc(t.id)}"><span class="task-id">${esc(t.id)}</span>${esc(t.title)}</a></td><td>${esc(t.category)}</td><td class="mono">${esc(t.level)}</td><td>${historical?'原协议':t.scoring==='manual'?'量表':'自动'}</td><td><a class="table-arrow" aria-label="查看 ${esc(t.id)}" href="#${historical?'historical':'task'}/${esc(t.id)}">→</a></td></tr>`).join('')||'<tr><td colspan="5" class="empty-cell">没有匹配的题目。 <button class="text-button" id="empty-reset">清除筛选</button></td></tr>'}</tbody></table></div><div class="table-caption">${rows.length} / ${list.length} 道题</div>`;
}
function taskDetail(id,historical=false){
 const t=historical?legacyFor(id):taskFor(id),back=historical?'history':'library';
 if(!t)return `<a class="back-link" href="#${back}">← 返回题库</a>`+empty('未找到题目','请重新选择。');
 const manual=t.scoring==='manual',isAnswer=id==='H02',d=RELEASE.downloads||{};
 const label=manual?'开始评阅':isAnswer?'提交答案':'导入评分报告';
 let resource=taskResource(t,historical);
 if(id==='R06'&&!historical)resource=d.tasks?.['R06-'+videoMode];
 const mode=id==='R06'&&!historical?`<label class="mode-control">评测模式<select id="task-mode"><option value="">先选择模式</option><option value="A" ${videoMode==='A'?'selected':''}>A · 独立修改</option><option value="B" ${videoMode==='B'?'selected':''}>B · 参考重建</option></select></label>`:'';
 return `<a class="text-button back-link" href="#${back}">← 返回题库</a>`+head('',`${id} · ${t.title}`,'')+
 `<p class="task-context">${esc(t.category)} <span>·</span> 难度 ${esc(t.level)} ${t.budget?`<span>·</span> ${t.budget} 分钟参考预算`:''}</p>`+
 `<section class="task-action-panel">${mode}<div class="action-row">${id==='R06'&&!videoMode?'':driveLink(resource,'下载题包',true)}${!historical?`<a class="secondary" href="#submit/${id}">${label} →</a>`:''}${!historical&&!manual&&!isAnswer?driveLink(d.grader,'下载评分器'):''}</div></section>`+
 `<section class="detail-section packet-section"><div class="section-head"><h2>完整题面</h2><button class="text-button" data-copy-packet="${id}">复制题面</button></div><div id="packet-content">${t.body?`<pre class="original-text">${esc(t.body)}</pre>`:packetPath(t)?.endsWith('.html')?`<iframe class="packet-frame" title="${esc(id)} 题面" src="${esc(packetPath(t))}" sandbox loading="lazy"></iframe>`:'<p class="muted">正在载入…</p>'}</div></section>`+
 (!historical?`<details class="technical-details"><summary>${manual?'评分量表与证据':'评分与环境'}</summary>${manual?'<p>按各维度 0–4 级及权重计算。必要条件不满足时应用公开分数上限；未观察的项目保持未评。</p>':isAnswer?'<p>粘贴原始 JSON 后，网页独立计算产额、时间、最优证书和反例。</p>':`<p>本地验证器实际执行候选代码；网页核对报告与检查权重。</p>${commandBlock(id)}`}<p class="muted">版本 ${esc(RELEASE.version)} · 设计难度尚未用模型成绩标定。</p></details>`:'')+
 `<div class="bottom-actions"><a class="secondary" href="#${back}">← 返回题库</a>${!historical?`<a class="primary" href="#submit/${id}">${label} →</a>`:''}</div>`;
}
async function loadPacket(id,historical) {
  const t=historical?legacyFor(id):taskFor(id),p=packetPath(t);
  if(!t||t.body||!p||p.endsWith('.html')||(!historical&&t.status!=='ready'))return;
  try {
    const response=await fetch(p);if(!response.ok)throw new Error();const body=await response.text();
    const r=route();if(r.id!==id||r.page!==(historical?'historical':'task'))return;
    $('#packet-content').innerHTML=`<pre class="original-text">${esc(body)}</pre>`;
  }catch(_){if($('#packet-content'))$('#packet-content').innerHTML='<div class="notice" role="alert">站内题面暂时无法读取。请使用上方 Google Drive 题目材料入口，或返回题库重试。</div>';}
}
function cliCommand(id){const filename=id==='L01'?'proofs.json':id==='H02'?'answer.json':id.startsWith('F')?'solution.f90':'solution.py';return `python -m nrb_v2 grade --task ${id} --source submissions/${id}/${filename} --out results/${id}.json`;}
function commandBlock(id='P01'){return `<div class="code-block"><pre>${esc(cliCommand(id))}</pre><button class="text-button" data-copy-command="${id}">复制命令</button></div><p class="muted">在评分器目录运行。首次使用先运行 Build-Environment。</p>`;}
function defaultMetadata() {return {model:'',version:'',reasoning:'未记录',date:today(),harness:'',tools:'',environment:'',budgetPolicy:'题面建议预算',budget:'',attemptPolicy:'固定预算下的首次作答',attempt:'1',notes:''};}
function metadataFields(m,taskId,editing=false) {
 const budget=taskFor(taskId)?.budget;
 const field=(label,name,placeholder='',max=150)=>`<label>${label}<input name="${name}" maxlength="${max}" value="${esc(m[name])}" placeholder="${esc(placeholder)}"></label>`;
 return `<div class="form-grid"><label>模型名<input name="model" required maxlength="120" value="${esc(m.model)}"></label><label>版本 / 快照<input name="version" required maxlength="120" value="${esc(m.version)}" placeholder="未知填“未记录”"></label><label>推理强度<select name="reasoning">${[...new Set(['未记录','不适用','low','medium','high','xhigh','max','ultra',...(m.reasoning?[String(m.reasoning)]:[])])].map(x=>`<option ${m.reasoning===x?'selected':''}>${esc(x)}</option>`).join('')}</select></label><label>日期<input name="date" type="date" required value="${esc(m.date)}"></label></div><details class="metadata-extra" ${editing?'open':''}><summary>测试条件与备注</summary><div class="form-grid">${field('作答平台','harness','如 ChatGPT 网页或 Codex')}${field('工具与 Skills','tools','写明允许使用的工具',250)}${field('环境协议','environment','如 NRB 2.0 标准环境；实际镜像由报告记录',200)}${field('预算规则','budgetPolicy')}<label>本题预算（分钟）<input name="budget" type="number" min="1" max="100000" step="1" value="${esc(m.budget)}" placeholder="${budget||'未知留空'}"></label><label>尝试编号<input name="attempt" type="number" required min="1" max="10000" step="1" value="${esc(m.attempt||1)}"></label></div>${field('尝试规则','attemptPolicy')}<label>备注与证据位置<textarea name="notes" maxlength="12000" rows="3">${esc(m.notes)}</textarea></label><p class="muted">条件完整且相同的记录可进入模型比较。</p></details>`;
}

function readMetadata(form) {
  const fields=Object.fromEntries(new FormData(form));
  for(const k of ['model','version','reasoning','date','harness','tools','environment','budgetPolicy','attemptPolicy','notes'])fields[k]=String(fields[k]||'').trim();
  if(!fields.model||!fields.version)throw new Error('请填写模型名与版本；未知版本可填“未记录”。');
  if(!/^\d{4}-\d{2}-\d{2}$/.test(fields.date))throw new Error('请填写有效的测试日期。');
  fields.attempt=Number(fields.attempt);
  if(!Number.isInteger(fields.attempt)||fields.attempt<1||fields.attempt>10000)throw new Error('尝试编号必须是 1–10000 的整数。');
  fields.budget=fields.budget===''?null:Number(fields.budget);
  if(fields.budget!==null&&(!Number.isFinite(fields.budget)||fields.budget<1||fields.budget>100000))throw new Error('时间预算需为正数，未知请留空。');
  return fields;
}
function submissionPage(id){
 const t=taskFor(id)||readyTasks[0];if(!t)return empty('未找到题目','请返回题库。');
 if(t.scoring==='manual')return reviewPage(t.id);
 if(submission.task!==t.id)reportReadToken++;
 if(submission.task!==t.id)submission={task:t.id,text:'',filename:'',error:'',result:null,report:null,metadata:{...defaultMetadata(),budget:String(t.budget||'')}};
 const answer=t.id==='H02';
 return `<a class="text-button back-link" href="#task/${t.id}">← 返回 ${t.id}</a>`+head('',answer?'提交答案':'导入评分报告',`${t.id} · ${t.title}`)+
 `<div class="submit-layout"><section class="panel"><div class="panel-body"><label class="block-label">题目<select id="submit-task">${readyTasks.map(x=>`<option value="${x.id}" ${x.id===t.id?'selected':''}>${x.id} · ${esc(x.title)}</option>`).join('')}</select></label><label class="upload-box"><strong>${answer?'选择 answer.json':'选择评分报告 .json'}</strong><input id="report-file" type="file" accept=".json,.py,.f90,.lean,application/json"></label><p id="file-status" class="muted" aria-live="polite">${esc(submission.filename)}</p><details class="paste-details" ${answer||submission.text?'open':''}><summary>粘贴 JSON</summary><textarea id="report-text" rows="12" spellcheck="false" aria-label="${answer?'原始答案':'评分报告'} JSON">${esc(submission.text)}</textarea></details><p id="report-error" class="form-error" role="alert">${esc(submission.error)}</p><button class="primary" id="validate-report">${answer?'评分':'核验报告'}</button></div></section><aside class="panel instruction-panel"><div class="panel-body">${answer?'<h2>在此直接评分</h2><p>提交题面规定的完整答案。网页重新求解并检查每一项，结果会显示在下方。</p><p class="muted">答案只在本浏览器处理。</p>':`<h2>先运行本地验证</h2>${commandBlock(t.id)}${driveLink(RELEASE.downloads?.grader,'下载评分器')}<p class="download-note">本网页不执行 Python、Fortran 或 Lean。请上传验证器生成的报告。</p>`}</div></aside></div>`+
 `<section id="report-preview" class="report-preview">${submission.result?reportPreview(submission.result):''}</section>${saveSection(t)}`;
}
function reportPreview(g){
 if(g.kind==='manual')return reviewPreview(g);
 return `<div class="score-summary"><div><div class="score-value">${scoreText(g.score)}<small>${g.score===null?'未评分':'/ 100'}</small></div>${badge(g.controlOnly?'评分器自检':stateNames[g.status],g.controlOnly?'demo':g.status==='passed'?'success':g.status==='failed'?'failure':'neutral')}</div><div class="score-explanation"><h3>${g.taskId} · ${g.backend==='answer'?'答案验算':'本地报告'}</h3><p>${g.passedCount} 通过 · ${g.failedCount} 失败 · ${g.pendingCount} 未执行</p>${g.controlOnly?'<p class="muted">自检记录不进入模型成绩。</p>':''}</div></div><details class="checks-details" ${g.failedCount?'open':''}><summary>逐项检查 · ${g.checks.length}</summary><div class="table-wrap"><table class="checks-table"><thead><tr><th>检查</th><th>权重</th><th>结果</th><th>说明</th></tr></thead><tbody>${g.checks.map(c=>`<tr><td class="mono">${esc(c.id)}</td><td>${c.weight}</td><td>${badge(c.passed===true?'通过':c.passed===false?'失败':'未执行',c.passed===true?'success':c.passed===false?'failure':'neutral')}</td><td class="check-detail">${esc(c.detail)||'—'}</td></tr>`).join('')}</tbody></table></div></details>`;
}
function runs() {
  const list=records.map((r,i)=>({r,i})).filter(x=>runFilter==='all'||runFilter==='current'&&x.r?.schema==='nrb-browser-run-v3'||runFilter==='legacy'&&x.r?.schema!=='nrb-browser-run-v3').reverse();
  return head('TEST RECORDS / 04','测试记录','',`<a class="primary" href="#submit/${readyTasks[0]?.id||'P01'}">导入新报告</a>`)+
    `<div class="toolbar"><div class="segmented" role="group" aria-label="记录类型">${[['all','全部记录'],['current','V2 记录'],['legacy','历史记录']].map(([v,l])=>`<button data-run-filter="${v}" aria-pressed="${runFilter===v}" class="${runFilter===v?'active':''}">${l}</button>`).join('')}</div><span class="toolbar-spacer"></span><button class="secondary" data-export>导出备份</button><button class="secondary" data-import>导入备份</button></div>`+
    (list.length?recordTable(list):empty('还没有'+(runFilter==='legacy'?'历史':'测试')+'记录','选择题目并提交结果。','<a class="secondary" href="#library">选择题目 →</a>'))+
    `<div class="legend"><span>记录保存在当前浏览器，不自动云同步。</span><span>旧版手工记录与 V2 自动结果分别显示，旧分数不会被转换。</span></div>`;
}
function recordTable(list) {
  return `<div class="table-wrap"><table class="records-table"><thead><tr><th>题目</th><th>模型 / 配置</th><th>日期 / 尝试</th><th>状态</th><th>得分</th><th>操作</th></tr></thead><tbody>${list.map(({r,i})=>`<tr><td><a class="task-button" href="#run/${i}">${esc(r?.task||'未知')} · ${esc(taskTitle(r))}</a><span class="table-sub">${esc(r?.taskVersion||'历史版本')}</span></td><td>${esc(r?.model||'未记录')}<span class="table-sub">${esc(r?.version||'未记录')} · ${esc(r?.reasoning||'未记录')}</span></td><td class="mono">${esc(r?.date||'未记录')}<span class="table-sub">尝试 ${esc(r?.attempt||'未记录')}</span></td><td>${recordStatus(r)}</td><td class="mono score-cell">${esc(recordScore(r))}</td><td><a class="text-button" href="#run/${i}">查看详情 →</a></td></tr>`).join('')}</tbody></table></div>`;
}
function runDetail(index) {
  const r=records[index];if(!Number.isInteger(index)||index<0||index>=records.length)return empty('记录不存在','返回测试记录查找。','<a class="secondary" href="#runs">返回记录</a>');
  const g=gradeRecord(r),current=r?.schema==='nrb-browser-run-v3';
  return `<a class="text-button back-link" href="#runs">← 返回测试记录</a>`+head('TEST DETAIL',`${r?.task||'历史'} · ${r?.model||'未记录模型'}`,`${r?.version||'未记录快照'} · ${r?.reasoning||'未记录强度'} · ${r?.date||'未记录日期'}`)+
    `<div class="action-row record-actions"><button class="secondary" data-edit="${index}">编辑测试信息</button><button class="secondary" data-export-one="${index}">导出本条记录</button>${current?`<button class="secondary" data-export-report="${index}">导出原始报告</button>${versionTaskLink(r.task,g?.version||r.taskVersion)}`:legacyFor(r?.task)?`<a class="text-button" href="#historical/${esc(r.task)}">查看历史题目 →</a>`:''}<button class="text-button danger-text" data-delete="${index}">删除记录</button></div>`+
    (g?(g.valid?reportPreview(g):`<div class="notice error-banner" role="alert"><strong>当前报告不能计分或比较。</strong> ${esc(g.error)} 原始记录已保留，可导出后核对。</div>`):`<div class="notice"><strong>历史手工记录</strong> · ${esc(recordScore(r))}。按原协议保存，未改写为 V2 自动成绩。</div>`)+
    `<section class="detail-section"><h2>测试条件</h2><dl class="metadata-list">${[['题目',taskTitle(r)],['题面版本',r?.taskVersion],['作答平台',r?.harness],['工具与 Skills',r?.tools],['运行环境',r?.environment],['预算规则',r?.budgetPolicy],['时间预算',r?.budget?`${r.budget} 分钟`:'未记录'],['尝试规则',r?.attemptPolicy],['尝试编号',r?.attempt],['保存时间',r?.createdAt]].map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v??'未记录')}</dd>`).join('')}</dl></section>`+
    `<section class="detail-section"><h2>备注与证据</h2><p class="preserve-text">${esc(r?.notes||'未记录')}</p>${r?.output?`<h3>历史原始输出</h3><pre class="original-text">${esc(r.output)}</pre>`:''}</section>`+
    `<details class="technical-details"><summary>报告与来源标识</summary><pre class="original-text">${esc(JSON.stringify(current?{schema:r.rawReport?.schema,benchmark_version:r.rawReport?.benchmark_version,evaluator_fingerprint:r.rawReport?.evaluator_fingerprint,packet_hash:r.rawReport?.packet_hash,test_manifest_hash:r.rawReport?.test_manifest_hash,source_hash:r.rawReport?.source_hash,seed:r.rawReport?.seed,execution:r.rawReport?.execution}:r,null,2))}</pre></details><div class="bottom-actions"><a class="secondary" href="#runs">← 返回测试记录</a><a class="primary" href="#compare">查看模型比较 →</a></div>`;
}
function modelKey(r) {return JSON.stringify([r?.model||'',r?.version||'',r?.reasoning||'']);}
function metadataComplete(r) {return ['model','version','reasoning','harness','tools','environment','budgetPolicy','attemptPolicy'].every(k=>!unknown(r[k]))&&Number.isFinite(Number(r.budget))&&Number(r.budget)>0&&Number.isInteger(Number(r.attempt))&&Number(r.attempt)>0;}
function cohortKey(r,g){return JSON.stringify([g.version,g.evaluatorFingerprint,g.seed,r.harness,r.tools,r.environment,r.budgetPolicy,r.attemptPolicy]);}
function comparableRecords() {
  return records.map((r,i)=>({r,i,g:gradeRecord(r)})).filter(x=>x.g?.valid&&x.g.comparisonEligible&&metadataComplete(x.r)&&(x.g.backend!=='docker'||(typeof x.r.rawReport?.execution?.image_id==='string'&&/^sha256:[0-9a-f]{64}$/.test(x.r.rawReport.execution.image_id))));
}
function compare() {
  const all=comparableRecords();
  const cohorts=[...new Map(all.map(x=>[cohortKey(x.r,x.g),x])).entries()];
  if(!cohorts.some(([k])=>k===selectedCohort)){selectedCohort=cohorts.find(([k])=>new Set(all.filter(x=>cohortKey(x.r,x.g)===k).map(x=>modelKey(x.r))).size>=2)?.[0]||cohorts[0]?.[0]||'';selectedModels=new Set();}
  const list=all.filter(x=>cohortKey(x.r,x.g)===selectedCohort),configs=[...new Map(list.map(x=>[modelKey(x.r),x.r])).entries()];
  selectedModels=new Set([...selectedModels].filter(k=>configs.some(([key])=>key===k)));
  const current=currentRecords();const excluded=current.length-all.length;
  return head('MATCHED CONDITIONS / 05','模型比较','对齐版本、种子、工具与预算后，比较相同题目。默认展示尝试 #1，保留失败与缺测。')+
    `<section class="panel"><div class="panel-heading"><h2>1. 选择同一测试条件组</h2></div><div class="panel-body">${cohorts.length?`<label class="block-label">条件组<select id="cohort-select">${cohorts.map(([k,x],i)=>`<option value="${i}" ${k===selectedCohort?'selected':''}>${esc(x.r.harness)} · 种子 ${x.g.seed} · ${esc(x.r.tools)} · ${esc(x.r.environment)}</option>`).join('')}</select></label><p class="muted">同组：${esc(list[0]?.r.budgetPolicy)} · ${esc(list[0]?.r.attemptPolicy)} · ${esc(list[0]?.g.version)}</p>`:empty('暂无条件齐全的模型报告','保存评分记录，并填写模型快照、工具、预算和尝试规则。','<a class="secondary" href="#runs">检查已有记录 →</a>')}<p class="muted">${excluded} 条 V2 记录尚不具备本页比较条件；可能为自检、未评分、版本不一致或测试信息未完整。历史手工分单独保留。</p></div></section>`+
    `<section class="panel compare-model-panel"><div class="panel-heading"><h2>2. 选择 2–4 个模型配置</h2></div><div class="compare-picks">${configs.map(([key,r],i)=>`<label class="check-card"><input type="checkbox" data-model-index="${i}" ${selectedModels.has(key)?'checked':''}><span>${esc(r.model)}<small class="table-sub">${esc(r.version)} · ${esc(r.reasoning)}</small></span></label>`).join('')||'<p class="muted">有可比较报告后，将显示模型配置。</p>'}</div></section><div id="comparison">${comparison(list)}</div>`+
    `<div class="legend"><span>参考解与故意错误控制不计入模型成绩。</span><span>缺测显示为“未测”，环境不可用显示为“未评分”；均不填 0。</span><span>完整20题同条件配对后显示总均分。</span></div>`;
}
function comparison(list=comparableRecords().filter(x=>cohortKey(x.r,x.g)===selectedCohort)){
 const keys=[...selectedModels];if(keys.length<2)return empty('选择至少两个模型配置','只比较同题、同条件的首次作答。');
 const version=list[0]?.g.version||RELEASE.version,compareTasks=(releaseFor(version)?.tasks||tasks).filter(t=>t.status==='ready');
 const configs=keys.map(k=>list.find(x=>modelKey(x.r)===k)?.r),coverage=keys.map(()=>0),sums=keys.map(()=>0);let common=0;
 const rows=compareTasks.map(t=>{const entries=keys.map(key=>{const matches=list.filter(x=>x.r.task===t.id&&modelKey(x.r)===key&&Number(x.r.attempt)===1);const unique=[...new Map(matches.map(x=>[JSON.stringify([x.g.sourceHash,x.g.score,x.r.budget,x.g.packetHash,x.g.manifestHash,x.g.inputManifestHash||null,x.g.backend,x.r.rawReport?.execution?.image_id||null,x.g.mode,x.g.reviewerId]),x])).values()];return {item:unique.length===1?unique[0]:null,conflict:unique.length>1};});
 entries.forEach((e,i)=>{if(e.item)coverage[i]++;});
 const identity=entries.map(e=>e.item?JSON.stringify([e.item.g.packetHash,e.item.g.manifestHash,e.item.g.inputManifestHash||null,e.item.r.budget,e.item.g.backend,e.item.r.rawReport?.execution?.image_id||null,e.item.g.mode||null,e.item.g.reviewerId||null]):null);
 const paired=entries.every(e=>e.item)&&new Set(identity).size===1;if(paired){common++;entries.forEach((e,i)=>sums[i]+=e.item.g.score);}
 return `<tr><td>${versionTaskLink(t.id,version,t.id+' · '+t.title)}${entries.every(e=>e.item)&&!paired?'<span class="table-sub">本题环境、预算、评阅人或模式不同</span>':''}</td>${entries.map(e=>`<td>${e.conflict?badge('重复 #1，需核对','failure'):e.item?`<strong class="mono">${scoreText(e.item.g.score)}</strong><a class="text-button report-link" href="#run/${e.item.i}">查看</a>`:'<span class="muted">未测 / 无可比 #1</span>'}</td>`).join('')}</tr>`;});
 return `<div class="comparison"><div class="compare-summary"><h3>共同 ${common} / ${compareTasks.length} 题</h3><p class="muted">${common===compareTasks.length?'同协议完整题组；各题等权。':'下方均分仅覆盖共同题目，缺测不补零。'}</p></div><div class="table-wrap"><table><thead><tr><th>题目</th>${configs.map((r,i)=>`<th>${esc(r?.model)}<span class="table-sub">${esc(r?.version)} · 已评分 ${coverage[i]}/${compareTasks.length}</span></th>`).join('')}</tr></thead><tbody>${rows.join('')}<tr class="mean-row"><td>${common===compareTasks.length?'完整 '+compareTasks.length+' 题均分':'共同子集均分'} · ${common} 题</td>${sums.map(s=>`<td class="mono">${common?scoreText(s/common):'—'}</td>`).join('')}</tr></tbody></table></div></div>`;
}
function guide(){const d=RELEASE.downloads||{};return head('','评分指南','')+`<section class="panel"><div class="panel-body guide-body"><h2>程序题 · P01–P08、F01–F03、L01</h2><p>下载单题材料，在新会话中让模型作答。评分器由评测者保存。Python 提交 solution.py，Fortran 提交 solution.f90，Lean 提交 proofs.json。</p><p>解压评分器，首次运行 Build-Environment 构建两个容器环境。把文件放入对应 submissions 目录，再运行 Grade-Results。</p>${commandBlock('F01')}<div class="action-row">${driveLink(d.grader,'下载评分器',true)}</div><p>将单题 JSON 报告导入网页，查看结果并保存。环境不可用保留空分，代码失败按实际检查计分。本地报告可被编辑，导入核验不构成远程执行认证。</p><h2>H02 · 网页直接评分</h2><p>把题面要求的原始 JSON 粘贴到 H02 提交区。网页重新求解网络并验证答案，也接受离线评分报告。</p><h2>主观题与 H01 · 逐项评阅</h2><p>实际查看交付物，按公开锚点评级并填写证据。量表根据各维权重计算；必要条件失败时应用分数上限。未查看或无法运行的部分保留未评，不填零。视频 R06 在作答前选择 A 或 B，两个模式不混比。</p><h2>比较与备份</h2><p>保存模型、版本、工具、预算和尝试规则。比较使用尝试 #1，并逐题核对运行环境、题包、视频模式与评阅人。完整 20 题都有同条件成绩时才生成完整均分。</p><p>记录保存在当前浏览器。使用导出备份跨设备恢复；旧 V1.1 和第一轮 V2 记录继续保留，按原版本显示。</p><div class="action-row"><button class="secondary" data-export>导出备份</button><button class="secondary" data-import>导入备份</button>${driveLink(d.candidateBundle,'下载题目合集')}</div></div></section>`;}
function bindPage(page){
 if(page==='library'||page==='history'){const historic=page==='history',f=historic?historyFilter:filter;const update=()=>{$('#task-table').innerHTML=taskTable(historic);};$('#search').addEventListener('input',e=>{f.query=e.target.value;update();});$('#category').onchange=e=>{f.category=e.target.value;update();};$('#level').onchange=e=>{f.level=e.target.value;update();};$('#reset-filter').onclick=()=>resetFilter(historic);}
 if(page==='task'&&$('#task-mode'))$('#task-mode').onchange=e=>{invalidateReviewResult();videoMode=e.target.value;render();};
 if(page==='submit'){
  if(taskFor(route().id)?.scoring==='manual'){
   if($('#review-mode'))$('#review-mode').onchange=e=>{captureReview();invalidateReviewResult();videoMode=e.target.value;render();};
   if($('#calculate-review')){document.querySelectorAll('[data-rating],[data-state],[data-evidence],#reviewer-id,#submission-id').forEach(el=>el.addEventListener('input',()=>{invalidateReviewResult();captureReview();}));$('#calculate-review').onclick=calculateReview;$('#export-review').onclick=()=>exportJSON(captureReview(),reviewKey()+'-review.json');$('#artifact-preview-file').onchange=previewArtifact;$('#save-report-form').onsubmit=saveReport;$('#review-import').onchange=readReviewFile;}
  }else{$('#submit-task').onchange=e=>navigate('#submit/'+e.target.value);$('#report-file').onchange=readReportFile;$('#report-text').oninput=e=>{reportReadToken++;submission.text=e.target.value;submission.result=null;submission.report=null;$('#report-preview').innerHTML='';$('#save-section').hidden=true;};$('#validate-report').onclick=validateSubmission;$('#save-report-form').onsubmit=saveReport;}
 }
 if(page==='compare'){const all=comparableRecords(),cohorts=[...new Map(all.map(x=>[cohortKey(x.r,x.g),x])).entries()];if($('#cohort-select'))$('#cohort-select').onchange=e=>{selectedCohort=cohorts[Number(e.target.value)]?.[0]||'';selectedModels.clear();render();};const configs=[...new Map(all.filter(x=>cohortKey(x.r,x.g)===selectedCohort).map(x=>[modelKey(x.r),x.r])).entries()];document.querySelectorAll('[data-model-index]').forEach(input=>input.onchange=e=>{const k=configs[Number(input.dataset.modelIndex)]?.[0];if(!k)return;if(e.target.checked){if(selectedModels.size>=4){e.target.checked=false;toast('最多选择 4 个模型。');return;}selectedModels.add(k);}else selectedModels.delete(k);$('#comparison').innerHTML=comparison();});}
}
function resetFilter(historic) {const fresh={query:'',category:'',level:'',status:''};if(historic)historyFilter=fresh;else filter=fresh;render();}
async function readReportFile(event) {
  const file=event.target.files?.[0];if(!file)return;
  const token=++reportReadToken, task=submission.task;
  submission.result=null;submission.report=null;submission.text='';$('#report-text').value='';$('#report-preview').innerHTML='';$('#save-section').hidden=true;
  submission.filename=file.name;$('#file-status').textContent=file.name;
  if(/\.(py|f90|lean)$/i.test(file.name)){submission.error='你选择了程序源码。请先运行本地验证器，再上传生成的 JSON 报告。';submission.result=null;submission.report=null;$('#report-error').textContent=submission.error;$('#report-preview').innerHTML='';$('#save-section').hidden=true;return;}
  if(file.size>2*1024*1024){$('#report-error').textContent='报告超过 2 MB，请上传单题验证 JSON，不要上传源码包或附件。';return;}
  try{const value=await file.text();if(token!==reportReadToken||route().page!=='submit'||submission.task!==task)return;submission.text=value;$('#report-text').value=value;validateSubmission();}catch(_){if(token===reportReadToken&&submission.task===task&&$('#report-error'))$('#report-error').textContent='文件读取失败，请重选文件或粘贴 JSON。';}
}
function validateSubmission(){
 try{
  const text=$('#report-text').value;submission.text=text;if(!text.trim())throw Error('请选择文件或粘贴完整 JSON。');if(text.length>2*1024*1024)throw Error('内容超过 2 MB。');
  const parsed=NRBReports.parseJSON(text),knownReport=isObject(parsed)&&['nrb-answer-v2','nrb-auto-report-v2','nrb-v2-manual-review'].includes(parsed.schema),report=submission.task==='H02'&&!knownReport?NRBH02.report(parsed,RELEASE):parsed;
  const g=validateRawReport(report);if(g.taskId!==submission.task)throw Error(`文件属于 ${g.taskId}，请先切换题目。`);
  submission.report=report;submission.result=g;submission.error='';$('#report-error').textContent='';$('#report-preview').innerHTML=reportPreview(g);$('#save-section').hidden=false;toast('评分完成。');
 }catch(error){submission.report=null;submission.result=null;submission.error=error instanceof SyntaxError?'JSON 无法解析，请移除代码围栏并保留完整对象。':error.message;$('#report-error').textContent=submission.error;$('#report-preview').innerHTML='';$('#save-section').hidden=true;}
}
function saveReport(event){
 event.preventDefault();try{
  if(!submission.report)throw Error('请先完成评分或核验。');const g=validateRawReport(submission.report),meta=readMetadata(event.target);submission.metadata=meta;
  const r={...meta,schema:'nrb-browser-run-v3',id:newRecordId(),createdAt:new Date().toISOString(),source:g.kind==='manual'?'evidence-review':g.backend==='answer'?'answer-verification':'local-report-import',scoreKind:g.kind||'automatic-report',task:g.taskId,taskVersion:g.version,packetHash:g.packetHash,rubric:g.version,score:g.score,scoreState:g.score===null?'pending':'scored',rawReport:submission.report};
  const duplicate=records.findIndex(x=>x?.schema==='nrb-browser-run-v3'&&modelKey(x)===modelKey(r)&&x.task===r.task&&Number(x.attempt)===r.attempt&&JSON.stringify(x.rawReport)===JSON.stringify(r.rawReport)&&x.harness===r.harness&&x.tools===r.tools&&x.environment===r.environment&&x.budget===r.budget);
  if(duplicate>=0){toast('这条记录已保存。');navigate('#run/'+duplicate);return;}
  records.push(r);const ok=persist();submission={task:'',text:'',filename:'',error:'',result:null,report:null,metadata:{}};navigate('#run/'+(records.length-1));toast(ok?'记录已保存。':'暂存于内存，请导出备份。');
 }catch(error){$('#save-error').textContent=error.message;}
}
function exportJSON(value,filename) {
  try{const blob=new Blob([JSON.stringify(value,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);toast('已发起 JSON 下载。');}catch(error){toast('无法生成下载：'+error.message);}
}
function exportAll(){exportJSON({schemaVersion:3,exportedAt:new Date().toISOString(),scope:'all-records-preserved',records,unreadablePreviousStorage:unreadableStorage},'research-benchmark-records.json');}
function editRecord(index) {
  const record=records[index];if(!isObject(record)){toast('该历史项不是结构化记录，请先导出核对。');return;}
  const meta={...defaultMetadata(),...record};
  $('#metadata-body').innerHTML=`<p class="muted">${esc(record.task||'历史记录')} · 原始报告与评分不会被修改。</p><form id="edit-form">${metadataFields(meta,record.task,true)}<p id="edit-error" class="form-error" role="alert"></p><div class="form-actions"><button type="button" class="secondary" data-close="metadata-dialog">取消</button><button class="primary">保存信息</button></div></form>`;
  $('#edit-form').onsubmit=e=>{e.preventDefault();try{const fields=readMetadata(e.target);records[index]={...record,...fields,updatedAt:new Date().toISOString()};const saved=persist();$('#metadata-dialog').close();render();toast(saved?'测试信息已更新。':'信息仍在内存中，请导出备份。');}catch(error){$('#edit-error').textContent=error.message;}};
  $('#metadata-dialog').showModal();
}
function confirmDialog(title,body,action,label='确认') {
  $('#confirm-title').textContent=title;$('#confirm-body').innerHTML=body+`<div class="form-actions"><button class="secondary" data-close="confirm-dialog">取消</button><button class="primary" id="confirm-action">${esc(label)}</button></div>`;confirmAction=action;
  $('#confirm-action').onclick=()=>{const fn=confirmAction;confirmAction=null;$('#confirm-dialog').close();if(fn)fn();};$('#confirm-dialog').showModal();
}
function deleteRecord(index) {
  const record=records[index];if(index<0||index>=records.length)return;
  confirmDialog('删除这条记录？',`<p>${esc(record?.task||'历史记录')} · ${esc(record?.model||'未记录模型')} · ${esc(record?.date||'未记录日期')}</p><p class="muted">只删除当前浏览器中的此条记录。需要留档时，请先导出备份。</p>`,()=>{records.splice(index,1);const saved=persist();navigate('#runs');toast(saved?'记录已删除。':'删除尚未保存，请检查浏览器存储。');},'删除记录');
}
async function importBackup(event) {
  const file=event.target.files?.[0];if(!file)return;event.target.value='';
  try{
    if(file.size>20*1024*1024)throw new Error('备份超过 20 MB，请分批导入。');
    const data=NRBReports.parseJSON(await file.text()),incoming=Array.isArray(data)?data:data?.records;
    if(!Array.isArray(incoming)||incoming.length>10000)throw new Error('请选择导出的记录备份（records 数组，最多 10000 条）。');
    const knownIds=new Map(records.filter(isObject).filter(x=>typeof x.id==='string').map(x=>[x.id,JSON.stringify(x)]));
    const exact=new Set(records.map(x=>JSON.stringify(x))),additions=[];let duplicate=0,conflicts=0,invalid=0;
    for(const original of incoming){
      const value=JSON.stringify(original);if(exact.has(value)){duplicate++;continue;}
      let item=original;
      if(isObject(item)&&typeof item.id==='string'&&knownIds.has(item.id)){item={...item,id:newRecordId(),importedOriginalId:item.id};conflicts++;}
      if(item?.schema==='nrb-browser-run-v3'&&!gradeRecord(item)?.valid)invalid++;
      additions.push(item);exact.add(value);if(isObject(item)&&typeof item.id==='string')knownIds.set(item.id,JSON.stringify(item));
    }
    if(data?.unreadablePreviousStorage){additions.push({kind:'preserved-unreadable-storage',id:newRecordId(),raw:data.unreadablePreviousStorage,importedAt:new Date().toISOString()});}
    confirmDialog('合并记录备份',`<p>将新增 <strong>${additions.length}</strong> 条，跳过 ${duplicate} 条相同记录。</p><p class="muted">${conflicts?`${conflicts} 条 ID 相同但内容不同的记录会分开保留。`:''}${invalid?`${invalid} 条报告与当前协议不匹配，将保留原始内容并标为需重新验证，不计分或比较。`:''}现有记录不会被替换。</p>`,()=>{records.push(...additions);const saved=persist();navigate('#runs');toast(saved?`已合并 ${additions.length} 条记录。`:'导入数据仅在内存中，尚未写入浏览器，请导出备份。');},'合并导入');
  }catch(error){toast('导入失败：'+(error instanceof SyntaxError?'JSON 无法解析。':error.message));}
}
async function copyCommand(taskId) {
  const text=cliCommand(taskId);
  try{await navigator.clipboard.writeText(text);toast('命令已复制，请在评分器根目录运行。');}
  catch(_){const area=document.createElement('textarea');area.value=text;document.body.appendChild(area);area.select();let done=false;try{done=document.execCommand('copy');}catch(_){}area.remove();toast(done?'命令已复制。':'无法自动复制，请选中命令文本手动复制。');}
}
function versionTaskLink(id,version,label){const old=version&&version!==RELEASE.version,url=old?safeDrive(releaseFor(version)?.downloads?.tasks?.[id]):'#task/'+id;return url?`<a class="text-button" href="${esc(url)}" ${old?'target="_blank" rel="noopener noreferrer"':''}>${esc(label||(old?'原版本题包':'返回题目 →'))}</a>`:esc(label||id);}

function releaseFor(version){return version===RELEASE.version?RELEASE:(globalThis.NRB_RELEASE_HISTORY||{})[version];}

function validateRawReport(report){const release=releaseFor(report?.benchmark_version);if(!release)throw Error('未登记的题库版本；原始记录仍保留。');return NRBReports.validateReport(report,release);}

function saveSection(t){return `<section id="save-section" class="panel save-section" ${submission.result?'':'hidden'}><div class="panel-heading"><h2>保存记录</h2></div><form id="save-report-form" class="panel-body">${metadataFields(submission.metadata||defaultMetadata(),t.id)}<p class="form-error" id="save-error" role="alert"></p><div class="form-actions"><a class="secondary" href="#task/${t.id}">返回题目</a><button class="primary">保存 →</button></div></form></section>`;}

function reviewPage(id){
 const t=taskFor(id),mode=id==='R06'?(videoMode||null):null,key=id+(mode?'-'+mode:'');
 const top=`<a class="text-button back-link" href="#task/${id}">← 返回 ${id}</a>`+head('','评阅结果',`${id} · ${t.title}`);
 const modeSelect=id==='R06'?`<label class="mode-control">预先选定的模式<select id="review-mode"><option value="">选择模式</option><option value="A" ${mode==='A'?'selected':''}>A · 独立修改</option><option value="B" ${mode==='B'?'selected':''}>B · 参考重建</option></select></label>`:'';
 if(id==='R06'&&!mode)return top+modeSelect;
 const entry=NRBSubjective.specFor(id,mode,RELEASE),spec=entry.spec,draft=reviewDrafts[key]||(reviewDrafts[key]=NRBSubjective.blank(id,mode,RELEASE));
 if(submission.task!==key)reportReadToken++;
 if(submission.task!==key)submission={task:key,text:'',filename:'',error:'',result:null,report:null,metadata:{...defaultMetadata(),budget:String(t.budget||'')}};
 const ratings=spec.rubric.map(d=>{const r=draft.ratings.find(x=>x.id===d.id);return `<div class="rubric-row"><div class="rubric-row-head"><h3>${esc(d.name)} <small>${d.weight} 分</small></h3><select aria-label="${esc(d.name)}评级" data-rating="${d.id}"><option value="">未评</option>${[0,1,2,3,4].map(v=>`<option value="${v}" ${r.level===v?'selected':''}>${v} / 4</option>`).join('')}</select></div><details class="anchors"><summary>评级锚点</summary>${Object.entries(d.anchors).map(([v,a])=>`<p><b>${v}</b> ${esc(a)}</p>`).join('')}</details><textarea data-evidence="rating:${d.id}" aria-label="${esc(d.name)}证据" rows="2" placeholder="具体证据：文件、页码、时间点或实际操作结果">${esc(r.evidence)}</textarea></div>`;}).join('');
 const stateRows=(items,group,rows)=>items.map(d=>{const r=rows.find(x=>x.id===d.id),ob=group==='observation';return `<div class="review-check"><label>${esc(d.label||d.requirement)}<select data-state="${group}:${d.id}">${(ob?[['unassessed','未观察'],['observed','已观察'],['missing','已确认缺失']]:[['unassessed','未评'],['pass','满足'],['fail','不满足']]).map(([v,l])=>`<option value="${v}" ${r.status===v?'selected':''}>${l}</option>`).join('')}</select></label><textarea data-evidence="${group}:${d.id}" rows="2" aria-label="${esc(d.label||d.requirement)}证据" placeholder="记录具体观察；无法打开或尚未检查时保留未观察">${esc(r.evidence)}</textarea></div>`;}).join('');
 return top+modeSelect+`<section class="panel"><div class="panel-body"><div class="form-grid"><label>评阅人${draft.reviewer.kind==='llm_provisional'?' · LLM 暂评':''}<input id="reviewer-id" value="${esc(draft.reviewer.id)}"></label><label>结果编号<input id="submission-id" value="${esc(draft.submission_id)}" placeholder="对应本次模型输出的文件或记录编号"></label></div><details><summary>打开结果预览</summary><input id="artifact-preview-file" type="file" accept=".html,.svg,.png,.jpg,.jpeg,.webp,.mp4,.webm,.txt,.md"><div id="artifact-preview"></div></details><details class="technical-details"><summary>导入已有评阅 JSON</summary><input id="review-import" type="file" accept=".json"></details></div></section>`+
 `<section class="panel review-panel"><div class="panel-heading"><h2>评分维度</h2></div><div class="panel-body">${ratings}</div></section><details class="technical-details" open><summary>必要条件</summary>${stateRows(spec.requirements,'requirement',draft.requirements)}</details><details class="technical-details" open><summary>观察记录</summary>${stateRows(spec.required_observations,'observation',draft.observations)}</details><p class="form-error" id="review-error" role="alert"></p><div class="action-row review-actions"><button class="primary" id="calculate-review">计算评分</button><button class="secondary" id="export-review">导出评阅草稿</button></div><section id="report-preview" class="report-preview">${submission.result?reportPreview(submission.result):''}</section>${saveSection(t)}`;
}

function reviewKey(){const id=route().id;return id+(id==='R06'?'-'+videoMode:'');}

function invalidateReviewResult(){
 reviewReadToken++;submission.report=null;submission.result=null;submission.error='';
 const error=$('#review-error'),preview=$('#report-preview'),save=$('#save-section');
 if(error)error.textContent='';if(preview)preview.innerHTML='';if(save)save.hidden=true;
}

async function readReviewFile(event){
 const file=event.target.files?.[0];if(!file)return;
 let current;try{current=route();}catch(_){return;}
 const task=current.id,mode=task==='R06'?videoMode:null,key=reviewKey();
 if(current.page!=='submit'||taskFor(task)?.scoring!=='manual'||submission.task!==key)return;
 invalidateReviewResult();
 const token=reviewReadToken;
 const stillCurrent=()=>{
  if(token!==reviewReadToken)return false;
  let active;try{active=route();}catch(_){return false;}
  return active.page==='submit'&&active.id===task&&submission.task===key&&(task==='R06'?videoMode:null)===mode;
 };
 try{
  if(file.size>2*1024*1024)throw Error('文件超过 2 MB。');
  const text=await file.text();if(!stillCurrent())return;
  const review=NRBReports.parseJSON(text),result=NRBSubjective.validate(review,RELEASE);
  if(review.task_id!==task||review.mode!==mode)throw Error('题号或模式不匹配。');
  if(!stillCurrent())return;
  reviewDrafts[key]=review;render();displayReviewResult(review,result);
 }catch(error){
  if(!stillCurrent())return;
  const target=$('#review-error');if(target)target.textContent=error.message;
 }
}

function captureReview(){
 const review=reviewDrafts[reviewKey()];if(!review)return null;
 review.reviewer.id=$('#reviewer-id').value.trim();review.submission_id=$('#submission-id').value.trim();
 document.querySelectorAll('[data-rating]').forEach(el=>{review.ratings.find(r=>r.id===el.dataset.rating).level=el.value===''?null:Number(el.value);});
 document.querySelectorAll('[data-state]').forEach(el=>{const [group,id]=el.dataset.state.split(':');review[group==='requirement'?'requirements':'observations'].find(r=>r.id===id).status=el.value;});
 document.querySelectorAll('[data-evidence]').forEach(el=>{const [group,id]=el.dataset.evidence.split(':');review[group==='rating'?'ratings':group==='requirement'?'requirements':'observations'].find(r=>r.id===id).evidence=el.value;});return review;
}

function displayReviewResult(review,result){submission.report=JSON.parse(JSON.stringify(review));submission.result=result;$('#review-error').textContent='';$('#report-preview').innerHTML=reportPreview(result);$('#save-section').hidden=false;toast(result.score===null?'还有未评项目，完整分数保持为空。':'评分已计算。');}

function calculateReview(){reviewReadToken++;try{const r=captureReview(),g=NRBSubjective.validate(r,RELEASE);displayReviewResult(r,g);}catch(error){submission.report=null;submission.result=null;$('#review-error').textContent=error.message;$('#report-preview').innerHTML='';$('#save-section').hidden=true;}}

function reviewPreview(g){const r=g.review;return `<div class="score-summary"><div><div class="score-value">${scoreText(g.score)}<small>${g.score===null?'未评完':'/ 100'}</small></div>${badge(g.reviewerKind==='llm_provisional'?'LLM 暂评':g.score===null?'评阅未完成':'已评阅',g.score===null?'neutral':'success')}</div><div class="score-explanation"><h3>${g.taskId}${g.mode?' · '+g.mode+' 模式':''}</h3><p>已评权重 ${r.rated_weight} / 100${r.missing_items.length?' · 仍有 '+r.missing_items.length+' 项待完成':''}</p>${g.protocolEligible===false?'<p>本次视频材料不符合预先选定模式，结果不进入比较。</p>':''}${r.applied_caps.map(c=>`<p>分数上限 ${c.max_score}：${esc(c.reason)}</p>`).join('')}</div></div><details class="checks-details"><summary>评分明细与证据</summary><div class="table-wrap"><table><thead><tr><th>维度</th><th>评级</th><th>得分</th><th>证据</th></tr></thead><tbody>${r.dimension_scores.map(d=>`<tr><td>${esc(g.rubric.rubric.find(x=>x.id===d.id).name)}</td><td>${d.level===null?'未评':d.level+'/4'}</td><td>${scoreText(d.earned)} / ${d.weight}</td><td>${esc(g.rawReview.ratings.find(x=>x.id===d.id).evidence)}</td></tr>`).join('')}</tbody></table></div></details>`;}

async function previewArtifact(event){
 const file=event.target.files?.[0];if(!file)return;const target=$('#artifact-preview');target.innerHTML='';
 if(file.size>100*1024*1024){target.textContent='文件超过 100 MB，请按题面在本地打开并记录观察。';return;}
 const name=file.name.toLowerCase();
 if(name.endsWith('.html')){if(file.size>4*1024*1024){target.textContent='HTML 超过 4 MB，请本地检查。';return;}const frame=document.createElement('iframe');frame.className='artifact-frame';frame.title='候选 HTML 独立预览';frame.setAttribute('sandbox','allow-scripts allow-downloads');const csp="<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; media-src data: blob:; font-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'\">";frame.srcdoc=csp+await file.text();target.appendChild(frame);}
 else if(/\.(png|jpe?g|webp|svg)$/.test(name)){const img=document.createElement('img');img.alt=file.name;img.src=URL.createObjectURL(file);img.onload=()=>URL.revokeObjectURL(img.src);target.appendChild(img);}
 else if(/\.(mp4|webm)$/.test(name)){const video=document.createElement('video');video.controls=true;video.src=URL.createObjectURL(file);target.appendChild(video);}
 else if(/\.(md|txt)$/.test(name)&&file.size<4*1024*1024){const pre=document.createElement('pre');pre.className='original-text';pre.textContent=await file.text();target.appendChild(pre);}
 else target.textContent='请在本地打开此格式并填写观察记录。';
}

async function copyPacket(id){try{const t=taskFor(id)||legacyFor(id),p=packetPath(t);const body=t.body||await (await fetch(p)).text();await navigator.clipboard.writeText(body);toast('题面已复制。');}catch(_){toast('无法自动复制，请在题面中选择文本或下载题包。');}}

$('#backup-file').onchange=importBackup;
document.addEventListener('click',event=>{
  const el=event.target.closest('button,[data-close]');if(!el)return;
  if(el.dataset.close){$('#'+el.dataset.close).close();return;}
  if(el.hasAttribute('data-export'))return exportAll();
  if(el.hasAttribute('data-import'))return $('#backup-file').click();
  if(el.id==='empty-reset')return resetFilter(route().page==='history');
  if(el.dataset.runFilter){runFilter=el.dataset.runFilter;return render();}
  if(el.dataset.copyCommand)return copyCommand(el.dataset.copyCommand);
  if(el.dataset.copyPacket)return copyPacket(el.dataset.copyPacket);
  if(el.dataset.categoryLink){filter.category=el.dataset.categoryLink;return navigate('#library');}
  if(el.dataset.edit!==undefined)return editRecord(Number(el.dataset.edit));
  if(el.dataset.delete!==undefined)return deleteRecord(Number(el.dataset.delete));
  if(el.dataset.exportOne!==undefined){const r=records[Number(el.dataset.exportOne)];return exportJSON({schemaVersion:3,exportedAt:new Date().toISOString(),records:[r]},`benchmark-${r?.task||'record'}-record.json`);}
  if(el.dataset.exportReport!==undefined){const r=records[Number(el.dataset.exportReport)];if(r?.rawReport)return exportJSON(r.rawReport,`${r.task}-report.json`);}
});
window.addEventListener('hashchange',render);
render();
