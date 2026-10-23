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
const head = (eyebrow,title,description,action='') => `<div class="page-heading"><div><span class="eyebrow">${esc(eyebrow)}</span><h1>${esc(title)}</h1><p class="muted">${esc(description)}</p></div>${action}</div>`;
const empty = (title,description,action='') => `<div class="empty"><div class="empty-symbol" aria-hidden="true">∅</div><h3>${esc(title)}</h3><p>${esc(description)}</p>${action}</div>`;
const taskFor = id => tasks.find(t => t.id === id);
const legacyFor = id => historicalTasks.find(t => t.id === id);
const stateNames = {passed:'检查全部通过',failed:'检查有失败',unscored:'未评分 · 检查未完成'};
const tierNames = {basic:'基础功能',scientific:'科学正确性',stress:'压力与边界'};
const unknown = value => !String(value ?? '').trim() || /^(未记录|未知|unknown|n\/a)$/i.test(String(value).trim());
let records = [], storageLoaded = false, storageOK = true, unreadableStorage = null;
let filter = {query:'',category:'',level:'',status:''}, historyFilter = {query:'',category:'',level:'',status:''};
let runFilter='all', selectedModels = new Set(), selectedCohort='';
let previousPage='', libraryScroll=0, historyScroll=0, confirmAction=null;
let reportReadToken=0;
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
function gradeRecord(record) {
  if (!isObject(record) || record.schema !== 'nrb-browser-run-v3') return null;
  if (!record.rawReport) return {valid:false,error:'缺少原始自动评分报告。',score:null,status:'unscored'};
  try { return {valid:true,...NRBReports.validateReport(record.rawReport,RELEASE)}; }
  catch (error) { return {valid:false,error:error.message,score:null,status:'unscored'}; }
}
function currentRecords() { return records.filter(r => isObject(r) && r.schema === 'nrb-browser-run-v3'); }
function taskTitle(record) { return (record?.schema==='nrb-browser-run-v3'?taskFor(record.task):legacyFor(record?.task))?.title || record?.task || '未识别历史记录'; }
function recordStatus(record) {
  const g=gradeRecord(record);
  if (g) return g.valid ? badge(g.controlOnly?'验证器自检 · 不计模型成绩':stateNames[g.status],g.controlOnly?'demo':g.status==='passed'?'success':g.status==='failed'?'failure':'neutral') : badge('报告需重新验证','failure');
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
  let r;
  try { r=route(); } catch (_) { r={page:'overview',id:''}; }
  if(previousPage==='library') libraryScroll=window.scrollY||0;
  if(previousPage==='history') historyScroll=window.scrollY||0;
  const names={overview:'总览',library:'分级题库',task:'题目详情',history:'V1.1 历史题库',historical:'历史题目',submit:'导入自动评分报告',runs:'测试记录',run:'测试详情',compare:'模型比较',guide:'使用指南'};
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
function overview() {
  const live=currentRecords(), scored=live.map(gradeRecord).filter(g=>g?.valid&&g.score!==null&&!g.controlOnly).length;
  const modelCount=new Set(live.filter(r=>!gradeRecord(r)?.controlOnly).map(modelKey)).size;
  return head('LAB NOTEBOOK / 01','让每次评测有据可查','从题目到验证报告，再到相同条件下的模型比较。','<a class="primary" href="#library">开始一次评测 →</a>')+
    `<div class="stats"><div class="stat"><label>完整题库规划</label><span class="value">${tasks.length||20}</span><small>8 Python · 3 Fortran · 1 Lean · 6 主观 · 2 聊天</small></div><div class="stat"><label>本轮可测试</label><span class="value">${readyTasks.length}</span><small>Python 全自动评分，满分 100</small></div><div class="stat"><label>已导入模型报告</label><span class="value">${scored}</span><small>逐项重算；自检报告单独标记</small></div><div class="stat"><label>模型配置</label><span class="value">${modelCount||'—'}</span><small>${records.length-live.length} 条历史记录完整保留</small></div></div>`+
    `<div class="workflow-strip"><div><span>01</span><h3>获取题目</h3><p>选择难度，将候选题包交给模型。</p></div><div><span>02</span><h3>运行自动验证</h3><p>本地验证器执行 solution.py，生成 JSON 报告。</p></div><div><span>03</span><h3>导入与比较</h3><p>网页核对版本与检查项，重算分数并保存记录。</p></div></div>`+
    `<div class="overview-grid"><section class="panel"><div class="panel-heading section-head"><h3>从不同难度开始</h3><a href="#library">全部题目 →</a></div><div class="start-tasks">${[readyTasks[0],readyTasks[3],readyTasks[7]].filter(Boolean).map(t=>`<a href="#task/${esc(t.id)}" class="start-task"><span class="id">${esc(t.id)}<small>设计难度 ${esc(t.level)}</small></span><div><h3>${esc(t.title)}</h3><p>${esc(t.brief)}</p></div><b aria-hidden="true">→</b></a>`).join('')||empty('题目清单载入中','当前版本尚未提供可用题目清单。')}</div></section><section class="panel"><div class="panel-heading"><h3>本轮更新</h3></div><div class="steps"><div class="step"><b>✓</b><div><strong>程序题无需人工分</strong><p>分数由固定检查权重计算，失败与未执行分开显示。</p></div></div><div class="step"><b>↗</b><div><strong>材料统一由 Drive 获取</strong><p>使用你的 Google 账号下载题面和评分器。</p></div></div><div class="step"><b>02</b><div><strong>其余 12 题进入第二轮</strong><p>保留完整结构与历史材料，未完成题目不进入本轮成绩。</p></div></div><a class="text-button" href="#guide">查看操作指南 →</a></div></section></div>`+
    (live.length?`<section class="sample-strip"><div class="section-head"><h3>最近记录</h3><a href="#runs">全部记录 →</a></div>${recordTable(records.map((r,i)=>({r,i})).filter(x=>x.r?.schema==='nrb-browser-run-v3').slice(-3).reverse())}</section>`:'');
}
function library(historical=false) {
  const f=historical?historyFilter:filter, list=historical?historicalTasks:tasks;
  return head(historical?'ARCHIVE / V1.1':'TASK LIBRARY / 02',historical?'历史题库':'分级题库',historical?'原有 21 道题目与材料保留；旧评分协议单独归档。':'本轮开放 8 道 Python 题，其余 12 题将在第二轮完成。设计难度尚未经过真实模型校准。',historical?'<a class="secondary" href="#library">返回 V2 题库</a>':'<a class="secondary" href="#guide">如何评分</a>')+
    `<div class="toolbar"><input class="search" id="search" type="search" aria-label="搜索题目" placeholder="搜索题号、标题或能力…" value="${esc(f.query)}"><select id="category" aria-label="按类别筛选"><option value="">全部类别</option>${[...new Set(list.map(t=>t.category))].map(c=>`<option value="${esc(c)}" ${f.category===c?'selected':''}>${esc(c)}</option>`).join('')}</select><select id="level" aria-label="按难度筛选"><option value="">全部难度</option>${['1/5','2/5','3/5','4/5','5/5'].map(l=>`<option ${f.level===l?'selected':''}>${l}</option>`).join('')}</select>${historical?'':`<select id="availability" aria-label="按开放状态筛选"><option value="">全部状态</option><option value="ready" ${f.status==='ready'?'selected':''}>本轮已开放</option><option value="planned" ${f.status==='planned'?'selected':''}>第二轮计划</option></select>`}<button class="secondary" id="reset-filter">重置筛选</button></div><div id="task-table">${taskTable(historical)}</div>`+
    `<div class="legend"><span>${historical?'V1.1 的自动 70 + 人工 30 仅适用于历史协议；不与 V2 混合。':'当前 Python 子集总分为 8 题均分；完整 20 题总分暂不生成。'}</span><span>每次测试使用独立会话，并保留第一次结果与重试记录。</span></div>`;
}
function taskTable(historical=false) {
  const f=historical?historyFilter:filter,list=historical?historicalTasks:tasks;
  const rows=list.filter(t=>(!f.category||t.category===f.category)&&(!f.level||t.level===f.level)&&(!f.status||t.status===f.status)&&`${t.id} ${t.title} ${t.brief} ${t.category}`.toLowerCase().includes(f.query.toLowerCase()));
  return `<div class="table-wrap"><table class="task-table"><thead><tr><th>题目 / 能力</th><th>类别</th><th>设计难度</th><th>参考预算</th><th>评分方式</th><th>状态</th></tr></thead><tbody>${rows.map(t=>`<tr><td><a class="task-button" href="#${historical?'historical':'task'}/${esc(t.id)}">${esc(t.id)} · ${esc(t.title)}</a><span class="table-sub task-brief">${esc(t.brief)}</span></td><td>${esc(t.category)}</td><td>${badge(t.level)}</td><td class="mono">${t.budget?esc(t.budget)+' 分钟':'待定'}</td><td>${historical?(t.id.startsWith('C')?'旧版混合评分':'原量表人工评阅'):(t.id.startsWith('P')||t.id.startsWith('F')||t.id.startsWith('L')?'全自动 · 100 分':t.id==='H02'?'客观验证（计划）':'人工量表（计划）')}</td><td>${historical?badge('历史材料'):t.status==='ready'?badge('本轮已开放','success'):badge('第二轮计划','demo')}</td></tr>`).join('')||'<tr><td colspan="6" class="empty-cell">没有匹配的题目。<button class="text-button" id="empty-reset">清除筛选</button></td></tr>'}</tbody></table></div><div class="table-caption"><span>${rows.length} / ${list.length} 道题</span><span>${historical?'历史记录不会自动迁入新版':'点击题目查看材料与下一步'}</span></div>`;
}
function taskDetail(id,historical=false) {
  const t=historical?legacyFor(id):taskFor(id),back=historical?'history':'library';
  if(!t)return `<a class="text-button back-link" href="#${back}">← 返回题库</a>`+empty('未找到题目','请从题库重新选择一道题。');
  const available=!historical&&t.status==='ready';
  const legacyId=t.legacyId||({P01:'C01',P02:'C02',P03:'C03',P04:'C04',P05:'C05',P06:'C07',P07:'C08',P08:'C10',F01:'C06',F03:'C09',R01:'R01',R02:'R02',R03:'R03',R04:'R04',R05:'R05',R06:'X04',H01:'X01'})[t.id];
  const title=head(`${historical?'ARCHIVE':'TASK'} / ${t.id}`,t.title,t.brief);
  const meta=`<div class="task-meta">${badge(t.category)}${badge('设计难度 '+t.level)}${badge(historical?'历史协议':RELEASE.version)}${badge(t.budget?t.budget+' 分钟参考预算':'预算待定')}${badge(historical?'历史材料':available?'本轮已开放':'第二轮计划',available?'success':'neutral')}</div>`;
  if(!historical&&!available)return `<a class="text-button back-link" href="#library">← 返回题库，保留筛选</a>${title}${meta}<section class="panel planned-panel"><span class="eyebrow">ROUND 02</span><h2>本题将在第二轮完成</h2><p>${esc(t.plan||t.brief||'第二轮将完成题面、材料与评分规则。')}</p><p class="muted">当前仅确定题库位置，不开放作答提交或计分。</p><div class="action-row">${legacyId&&legacyFor(legacyId)?`<a class="secondary" href="#historical/${legacyId}">查看相关历史材料</a>`:''}<a class="primary" href="#library">选择已开放的 Python 题</a></div></section>`;
  const d=RELEASE.downloads||{};
  return `<a class="text-button back-link" href="#${back}">← 返回${historical?'历史':''}题库，保留筛选</a>${title}${meta}`+
    `<section class="task-action-panel"><div><h2>${historical?'获取历史材料':'准备好后，从这里开始'}</h2><p class="muted">${historical?'按原题协议阅读与归档，旧结果不会自动变成 V2 成绩。':'候选模型只接收题包。评分器由你保管，候选程序完成后在本地验证。'}</p><div class="action-row">${driveLink(taskResource(t,historical),'Drive · 题目材料',true)}${historical?'':driveLink(d.grader,'Drive · 自动评分器')}${available?`<a class="secondary" href="#submit/${t.id}">导入评分报告 →</a>`:''}</div><p class="download-note">下载会打开 Google Drive，请使用有权限的账号。网页不会跨域读取你的私有 Drive 文件。</p></div></section>`+
    (available?`<div class="compact-workflow"><span>1 获取题包</span><span>2 模型交付 solution.py</span><span>3 本地验证</span><span>4 导入报告</span></div>`:'')+
    `${t.knownIssue?`<div class="notice">历史版本说明：${esc(t.knownIssue)}</div>`:''}<section class="detail-section"><div class="section-head"><h2>完整题面</h2>${available?'<a class="text-button" href="#guide">提交与评分说明</a>':''}</div><div id="packet-content">${t.body?`<pre class="original-text">${esc(t.body)}</pre>`:packetPath(t)?.endsWith('.html')?`<iframe class="packet-frame" title="${esc(t.id)} 完整题面" src="${esc(packetPath(t))}" sandbox loading="lazy"></iframe>`:'<p class="muted">正在读取题面…</p>'}</div></section>`+
    (available?`<section class="detail-section"><h2>评分方法</h2><p>所有检查由程序判定。总分 = 已通过检查权重 ÷ 全部检查权重 × 100。存在未执行检查时保持“未评分”，不补零，也不进入模型比较。</p><p class="muted">网页核验报告的版本、题包、验证器和检查清单，再按已登记权重重算分数。本地报告可以编辑，因此这里不提供不可伪造的执行认证。</p><details class="technical-details"><summary>本地验证命令</summary>${commandBlock(t.id)}</details></section>`:'')+
    `<details class="technical-details"><summary>版本与材料标识</summary><dl class="metadata-list"><dt>题号</dt><dd>${esc(t.id)}</dd><dt>题面版本</dt><dd>${esc(historical?t.version:RELEASE.version)}</dd><dt>题包 SHA-256</dt><dd class="mono break">${esc(t.packetHash||'见下载包清单')}</dd>${t.sourceCommit?`<dt>来源提交</dt><dd class="mono break">${esc(t.sourceCommit)}</dd>`:''}</dl></details><div class="bottom-actions"><a class="secondary" href="#${back}">← 返回题库</a>${available?`<a class="primary" href="#submit/${t.id}">导入 ${t.id} 评分报告 →</a>`:''}</div>`;
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
function cliCommand(taskId) { return `python -m nrb_v2 grade --task ${taskId} --source submissions/${taskId}/solution.py --execution docker --out results/${taskId}.json`; }
function commandBlock(taskId='P01') {
  return `<div class="code-block"><pre>${esc(cliCommand(taskId))}</pre><button class="text-button" data-copy-command="${esc(taskId)}">复制命令</button></div><p class="muted">解压评分器后在其根目录运行。先按包内 README 安装环境、构建 Docker 镜像，将候选实现保存到包内的 submissions/${esc(taskId)}/solution.py。</p>`;
}
function defaultMetadata() {return {model:'',version:'',reasoning:'未记录',date:today(),harness:'',tools:'',environment:'',budgetPolicy:'题面建议预算',budget:'',attemptPolicy:'固定预算下的首次作答',attempt:'1',notes:''};}
function metadataFields(m,taskId,editing=false) {
  const budget=taskFor(taskId)?.budget;
  return `<div class="form-grid"><label>精确模型名<input name="model" required maxlength="120" value="${esc(m.model)}" placeholder="如供应商 / 模型完整标识"></label><label>模型版本 / 快照<input name="version" required maxlength="120" value="${esc(m.version)}" placeholder="未知请填“未记录”"></label><label>推理强度<select name="reasoning">${['未记录','不适用','low','medium','high','xhigh','max','ultra'].map(x=>`<option ${m.reasoning===x?'selected':''}>${x}</option>`).join('')}</select></label><label>测试日期<input name="date" type="date" required value="${esc(m.date)}"></label><label>作答平台 / Harness<input name="harness" maxlength="150" value="${esc(m.harness)}" placeholder="如 ChatGPT 网页 / Codex，未知填未记录"></label><label>允许的工具与 Skills<input name="tools" maxlength="250" value="${esc(m.tools)}" placeholder="如 Python，无网络，无额外 Skills"></label><label>运行环境 / 镜像标识<input name="environment" maxlength="200" value="${esc(m.environment)}" placeholder="如固定 Docker 镜像摘要"></label><label>预算规则<input name="budgetPolicy" maxlength="150" value="${esc(m.budgetPolicy)}" placeholder="如按题面建议预算"></label><label>本题时间预算（分钟）<input name="budget" type="number" min="1" max="100000" step="1" value="${esc(m.budget)}" placeholder="${budget||'未知留空'}"></label><label>尝试编号<input name="attempt" type="number" required min="1" max="10000" step="1" value="${esc(m.attempt||1)}"></label></div><label>尝试规则<input name="attemptPolicy" maxlength="150" value="${esc(m.attemptPolicy)}" placeholder="在测试前确定，例如首次作答"></label><label>备注与证据位置<textarea name="notes" maxlength="12000" rows="3" placeholder="记录人工干预、实际工具、原始输出位置与未完成事项。">${esc(m.notes)}</textarea></label><p class="muted">${editing?'这里只编辑测试信息，分数仍由原始报告检查项决定。':'模型信息与测试条件由你填写；未知项可以保留，条件不完整的记录不会自动并入同条件比较。'}</p>`;
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
function submissionPage(id) {
  const t=taskFor(id)||readyTasks[0];
  if(!t||t.status!=='ready')return empty('本题尚未开放提交','请先选择本轮已开放的 Python 题。','<a class="primary" href="#library">返回题库</a>');
  if(submission.task!==t.id){submission={task:t.id,text:'',filename:'',error:'',result:null,report:null,metadata:{...defaultMetadata(),budget:String(t.budget||'')}};}
  return `<a class="text-button back-link" href="#task/${t.id}">← 返回 ${t.id} 题目</a>`+
    head('AUTOMATIC GRADING / 03','导入自动评分报告','先运行下载的验证器，再上传它生成的 JSON。程序题不再填写人工分。')+
    `<div class="submit-layout"><section class="panel"><div class="panel-heading"><h2>1. 选择题目与报告</h2></div><div class="panel-body"><label class="block-label">题目<select id="submit-task">${readyTasks.map(x=>`<option value="${x.id}" ${x.id===t.id?'selected':''}>${x.id} · ${esc(x.title)}</option>`).join('')}</select></label><label class="upload-box"><span class="upload-symbol" aria-hidden="true">↑</span><strong>选择本地验证报告 .json</strong><span>在本浏览器解析，不上传到服务器 · 最大 2 MB</span><input id="report-file" type="file" accept=".json,.py,application/json,text/x-python"></label><p id="file-status" class="muted" aria-live="polite">${esc(submission.filename)}</p><details class="paste-details" ${submission.text?'open':''}><summary>也可以直接粘贴 JSON 报告</summary><textarea id="report-text" rows="9" spellcheck="false" aria-label="评分报告 JSON" placeholder="粘贴 nrb-auto-report-v2 格式的完整报告">${esc(submission.text)}</textarea></details><p id="report-error" class="form-error" role="alert">${esc(submission.error)}</p><div class="action-row"><button class="primary" id="validate-report">核验报告并重算分数</button><a class="text-button" href="#guide">没有报告？</a></div></div></section><aside class="panel instruction-panel"><div class="panel-heading"><h3>还只有 solution.py？</h3></div><div class="panel-body"><p>下载自动评分器，将候选源码保存为 submissions/${esc(t.id)}/solution.py，运行：</p>${commandBlock(t.id)}${driveLink(RELEASE.downloads?.grader,'Drive · 下载评分器')}<p class="download-note">本网页不执行 Python。检查通过表示报告格式与当前协议一致；导入报告不等同于重新运行程序。</p></div></aside></div>`+
    `<section id="report-preview" class="report-preview">${submission.result?reportPreview(submission.result):''}</section>`+
    `<section id="save-section" class="panel save-section" ${submission.result?'':'hidden'}><div class="panel-heading"><h2>2. 补充模型信息并保存</h2></div><form id="save-report-form" class="panel-body">${metadataFields(submission.metadata,t.id)}<p class="form-error" id="save-error" role="alert"></p><div class="form-actions"><a class="secondary" href="#task/${t.id}">返回题目</a><button class="primary">保存到测试记录 →</button></div></form></section>`;
}
function reportPreview(g) {
  return `<div class="score-summary"><div><span class="eyebrow">${esc(g.taskId)} · ${g.controlOnly?'CONTROL REPORT':'LOCAL REPORT'}</span><div class="score-value">${scoreText(g.score)}<small>${g.score===null?'未评分':'/ 100'}</small></div>${badge(g.controlOnly?'验证器自检 · 不计模型成绩':stateNames[g.status],g.controlOnly?'demo':g.status==='passed'?'success':g.status==='failed'?'failure':'neutral')}</div><div class="score-explanation"><h3>已按当前检查权重重算</h3><p>${g.passedCount} 通过 · ${g.failedCount} 失败 · ${g.pendingCount} 未执行</p><p>关键检查：${g.criticalPassed===true?'全部通过':g.criticalPassed===false?'存在失败':'未完成'} · 种子 ${g.seed} · 执行方式 ${esc(g.backend)}</p><p class="muted">来源：本地验证报告导入。${g.controlOnly?'该报告用于验证器自检，保留在记录中但不进入模型比较。':g.comparisonEligible?'填写完整条件后可按相同协议比较。':'此报告不具备模型比较资格。'}</p></div></div><details class="checks-details" open><summary>逐项检查（${g.checks.length} 项）</summary><div class="table-wrap"><table class="checks-table"><thead><tr><th>检查项</th><th>分组</th><th>权重</th><th>结果</th><th>说明</th></tr></thead><tbody>${g.checks.map(c=>`<tr><td class="mono">${esc(c.id)}${c.critical?'<span class="table-sub">关键检查</span>':''}</td><td>${esc(tierNames[c.tier]||c.tier)}</td><td>${esc(c.weight)}</td><td>${badge(c.passed===true?'通过':c.passed===false?'失败':'未执行',c.passed===true?'success':c.passed===false?'failure':'neutral')}</td><td class="check-detail">${esc(c.detail)||(c.passed===true?'符合要求':'无额外说明')}</td></tr>`).join('')}</tbody></table></div></details>`;
}
function runs() {
  const list=records.map((r,i)=>({r,i})).filter(x=>runFilter==='all'||runFilter==='current'&&x.r?.schema==='nrb-browser-run-v3'||runFilter==='legacy'&&x.r?.schema!=='nrb-browser-run-v3').reverse();
  return head('TEST RECORDS / 04','测试记录','程序评分报告、运行条件和历史记录均保留。分数由检查项决定。',`<a class="primary" href="#submit/${readyTasks[0]?.id||'P01'}">导入新报告</a>`)+
    `<div class="toolbar"><div class="segmented" role="group" aria-label="记录类型">${[['all','全部记录'],['current','V2 自动报告'],['legacy','历史记录']].map(([v,l])=>`<button data-run-filter="${v}" aria-pressed="${runFilter===v}" class="${runFilter===v?'active':''}">${l}</button>`).join('')}</div><span class="toolbar-spacer"></span><button class="secondary" data-export>导出备份</button><button class="secondary" data-import>导入备份</button></div>`+
    (list.length?recordTable(list):empty('还没有'+(runFilter==='legacy'?'历史':'测试')+'记录','下载题目与评分器，完成一次程序测试后，将生成的报告导入这里。','<a class="secondary" href="#library">选择题目 →</a>'))+
    `<div class="legend"><span>记录保存在当前浏览器，不自动云同步。</span><span>旧版手工记录与 V2 自动结果分别显示，旧分数不会被转换。</span></div>`;
}
function recordTable(list) {
  return `<div class="table-wrap"><table class="records-table"><thead><tr><th>题目</th><th>模型 / 配置</th><th>日期 / 尝试</th><th>状态</th><th>得分</th><th>操作</th></tr></thead><tbody>${list.map(({r,i})=>`<tr><td><a class="task-button" href="#run/${i}">${esc(r?.task||'未知')} · ${esc(taskTitle(r))}</a><span class="table-sub">${esc(r?.taskVersion||'历史版本')}</span></td><td>${esc(r?.model||'未记录')}<span class="table-sub">${esc(r?.version||'未记录')} · ${esc(r?.reasoning||'未记录')}</span></td><td class="mono">${esc(r?.date||'未记录')}<span class="table-sub">尝试 ${esc(r?.attempt||'未记录')}</span></td><td>${recordStatus(r)}</td><td class="mono score-cell">${esc(recordScore(r))}</td><td><a class="text-button" href="#run/${i}">查看详情 →</a></td></tr>`).join('')}</tbody></table></div>`;
}
function runDetail(index) {
  const r=records[index];if(!Number.isInteger(index)||index<0||index>=records.length)return empty('记录不存在','返回测试记录查找。','<a class="secondary" href="#runs">返回记录</a>');
  const g=gradeRecord(r),current=r?.schema==='nrb-browser-run-v3';
  return `<a class="text-button back-link" href="#runs">← 返回测试记录</a>`+head('TEST DETAIL',`${r?.task||'历史'} · ${r?.model||'未记录模型'}`,`${r?.version||'未记录快照'} · ${r?.reasoning||'未记录强度'} · ${r?.date||'未记录日期'}`)+
    `<div class="action-row record-actions"><button class="secondary" data-edit="${index}">编辑测试信息</button><button class="secondary" data-export-one="${index}">导出本条记录</button>${current?`<button class="secondary" data-export-report="${index}">导出原始报告</button><a class="text-button" href="#task/${esc(r.task)}">返回题目 →</a>`:legacyFor(r?.task)?`<a class="text-button" href="#historical/${esc(r.task)}">查看历史题目 →</a>`:''}<button class="text-button danger-text" data-delete="${index}">删除记录</button></div>`+
    (g?(g.valid?reportPreview(g):`<div class="notice error-banner" role="alert"><strong>当前报告不能计分或比较。</strong> ${esc(g.error)} 原始记录已保留，可导出后核对。</div>`):`<div class="notice"><strong>历史手工记录</strong> · ${esc(recordScore(r))}。按原协议保存，未改写为 V2 自动成绩。</div>`)+
    `<section class="detail-section"><h2>测试条件</h2><dl class="metadata-list">${[['题目',taskTitle(r)],['题面版本',r?.taskVersion],['作答平台',r?.harness],['工具与 Skills',r?.tools],['运行环境',r?.environment],['预算规则',r?.budgetPolicy],['时间预算',r?.budget?`${r.budget} 分钟`:'未记录'],['尝试规则',r?.attemptPolicy],['尝试编号',r?.attempt],['保存时间',r?.createdAt]].map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v??'未记录')}</dd>`).join('')}</dl></section>`+
    `<section class="detail-section"><h2>备注与证据</h2><p class="preserve-text">${esc(r?.notes||'未记录')}</p>${r?.output?`<h3>历史原始输出</h3><pre class="original-text">${esc(r.output)}</pre>`:''}</section>`+
    `<details class="technical-details"><summary>报告与来源标识</summary><pre class="original-text">${esc(JSON.stringify(current?{schema:r.rawReport?.schema,benchmark_version:r.rawReport?.benchmark_version,evaluator_fingerprint:r.rawReport?.evaluator_fingerprint,packet_hash:r.rawReport?.packet_hash,test_manifest_hash:r.rawReport?.test_manifest_hash,source_hash:r.rawReport?.source_hash,seed:r.rawReport?.seed,execution:r.rawReport?.execution}:r,null,2))}</pre></details><div class="bottom-actions"><a class="secondary" href="#runs">← 返回测试记录</a><a class="primary" href="#compare">查看模型比较 →</a></div>`;
}
function modelKey(r) {return JSON.stringify([r?.model||'',r?.version||'',r?.reasoning||'']);}
function metadataComplete(r) {return ['model','version','reasoning','harness','tools','environment','budgetPolicy','attemptPolicy'].every(k=>!unknown(r[k]))&&Number.isFinite(Number(r.budget))&&Number(r.budget)>0&&Number.isInteger(Number(r.attempt))&&Number(r.attempt)>0;}
function cohortKey(r,g) {return JSON.stringify([g.version,g.evaluatorFingerprint,g.seed,r.harness,r.tools,r.environment,r.budgetPolicy,r.attemptPolicy,g.backend,r.rawReport?.execution?.image_id||null]);}
function comparableRecords() {
  return records.map((r,i)=>({r,i,g:gradeRecord(r)})).filter(x=>x.g?.valid&&x.g.comparisonEligible&&metadataComplete(x.r));
}
function compare() {
  const all=comparableRecords();
  const cohorts=[...new Map(all.map(x=>[cohortKey(x.r,x.g),x])).entries()];
  if(!cohorts.some(([k])=>k===selectedCohort)){selectedCohort=cohorts.find(([k])=>new Set(all.filter(x=>cohortKey(x.r,x.g)===k).map(x=>modelKey(x.r))).size>=2)?.[0]||cohorts[0]?.[0]||'';selectedModels=new Set();}
  const list=all.filter(x=>cohortKey(x.r,x.g)===selectedCohort),configs=[...new Map(list.map(x=>[modelKey(x.r),x.r])).entries()];
  selectedModels=new Set([...selectedModels].filter(k=>configs.some(([key])=>key===k)));
  const current=currentRecords();const excluded=current.length-all.length;
  return head('MATCHED CONDITIONS / 05','模型比较','对齐版本、种子、工具与预算后，比较相同题目。默认展示尝试 #1，保留失败与缺测。')+
    `<section class="panel"><div class="panel-heading"><h2>1. 选择同一测试条件组</h2></div><div class="panel-body">${cohorts.length?`<label class="block-label">条件组<select id="cohort-select">${cohorts.map(([k,x],i)=>`<option value="${i}" ${k===selectedCohort?'selected':''}>${esc(x.r.harness)} · 种子 ${x.g.seed} · ${esc(x.r.tools)} · ${esc(x.r.environment)}</option>`).join('')}</select></label><p class="muted">同组：${esc(list[0]?.r.budgetPolicy)} · ${esc(list[0]?.r.attemptPolicy)} · ${esc(list[0]?.g.version)}</p>`:empty('暂无条件齐全的模型报告','导入 Docker 验证报告，并填写模型快照、作答平台、工具、运行环境、预算与尝试规则。','<a class="secondary" href="#runs">检查已有记录 →</a>')}<p class="muted">${excluded} 条 V2 记录尚不具备本页比较条件；可能为自检、未评分、版本不一致或测试信息未完整。历史手工分单独保留。</p></div></section>`+
    `<section class="panel compare-model-panel"><div class="panel-heading"><h2>2. 选择 2–4 个模型配置</h2></div><div class="compare-picks">${configs.map(([key,r],i)=>`<label class="check-card"><input type="checkbox" data-model-index="${i}" ${selectedModels.has(key)?'checked':''}><span>${esc(r.model)}<small class="table-sub">${esc(r.version)} · ${esc(r.reasoning)}</small></span></label>`).join('')||'<p class="muted">有可比较报告后，将显示模型配置。</p>'}</div></section><div id="comparison">${comparison(list)}</div>`+
    `<div class="legend"><span>参考解与故意错误控制不计入模型成绩。</span><span>缺测显示为“未测”，环境不可用显示为“未评分”；均不填 0。</span><span>本轮仅报告 8 道 Python 题的覆盖率与共同子集均分。</span></div>`;
}
function comparison(list=comparableRecords().filter(x=>cohortKey(x.r,x.g)===selectedCohort)) {
  const keys=[...selectedModels];
  if(keys.length<2)return empty('请选择至少两个模型配置','比较只使用双方都已评分且条件一致的题目。不会以最好一次覆盖首次结果。');
  const configurations=keys.map(k=>list.find(x=>modelKey(x.r)===k)?.r);
  const coverage=keys.map(()=>0),sums=keys.map(()=>0);let common=0;
  const rows=readyTasks.map(t=>{
    const entries=keys.map(key=>{
      const matches=list.filter(x=>x.r.task===t.id&&modelKey(x.r)===key&&Number(x.r.attempt)===1);
      const distinct=[...new Map(matches.map(x=>[JSON.stringify([x.g.sourceHash,x.g.score,x.r.budget,x.g.packetHash,x.g.manifestHash]),x])).values()];
      return {item:distinct.length===1?distinct[0]:null,count:matches.length,conflict:distinct.length>1};
    });
    entries.forEach((e,i)=>{if(e.item)coverage[i]++;});
    const identity=entries.map(e=>e.item?JSON.stringify([e.item.g.packetHash,e.item.g.manifestHash,e.item.r.budget]):null);
    const paired=entries.every(e=>e.item)&&new Set(identity).size===1;
    if(paired){common++;entries.forEach((e,i)=>sums[i]+=e.item.g.score);}
    const mismatch=entries.every(e=>e.item)&&!paired;
    return `<tr><td><a class="task-button" href="#task/${t.id}">${t.id} · ${esc(t.title)}</a><span class="table-sub">${paired?'共同可比题目':mismatch?'预算或题包不同，不计共同均分':'缺少可比的尝试 #1'}</span></td>${entries.map(e=>`<td>${e.conflict?badge('重复 #1，需核对','failure'):e.item?`<strong class="mono">${scoreText(e.item.g.score)}</strong><span class="muted"> / 100</span><span class="table-sub">${e.item.r.budget} 分钟 · ${e.item.g.passedCount}/${e.item.g.checks.length} 检查通过</span><a class="text-button" href="#run/${e.item.i}">查看报告</a>`:'<span class="muted">未测 / 无可比 #1</span>'}</td>`).join('')}</tr>`;
  });
  return `<div class="comparison"><div class="compare-summary"><h3>共同 ${common} / ${readyTasks.length} 题</h3><p class="muted">${common===readyTasks.length?'8 道 Python 题已完整配对，可报告本轮子集均分。':common?'均分只覆盖下方共同题目，不代表完整 8 题或 20 题成绩。':'当前没有可计算共同均分的题目。'}</p></div><div class="table-wrap"><table><thead><tr><th>题目 / 配对状态</th>${configurations.map((r,i)=>`<th>${esc(r?.model)}<span class="table-sub">${esc(r?.version)} · ${esc(r?.reasoning)}</span><span class="table-sub">已评分 ${coverage[i]}/${readyTasks.length}</span></th>`).join('')}</tr></thead><tbody>${rows.join('')}<tr class="mean-row"><td>共同题目均分<span class="table-sub">${common} 题 · 尝试 #1</span></td>${sums.map(v=>`<td class="mono">${common?scoreText(v/common):'—'}</td>`).join('')}</tr></tbody></table></div></div>`;
}
function guide() {
  const d=RELEASE.downloads||{};
  return head('HOW TO USE','一次评测的完整流程','本轮的 Python 题由本地验证器自动评分，网页保存报告与模型配置。')+
    `<div class="guide-layout"><section class="panel"><div class="panel-body guide-body"><h2>1. 把题面交给模型</h2><p>在题库选择 P01–P08，打开 Google Drive 下载题包。每题使用一个新会话，并记下精确模型名、版本、推理强度、工具和预算。</p><p>候选模型只接收题面及允许的输入材料；评分器和参考程序由你保管。</p><div class="action-row">${driveLink(d.candidateBundle,'Drive · Python 候选包')}<a class="secondary" href="#library">浏览题库 →</a></div><h2>2. 本地运行验证器</h2><p>将模型的完整实现保存为 <code>submissions/P01/solution.py</code>。按评分器 README 安装依赖、准备 Docker 镜像，然后运行：</p>${commandBlock('P01')}<p>需要评分其他题时，将命令中的 P01 换成对应题号。默认种子为 17；网页也接受清单内的 0 与 2026。使用非默认题包种子时，应给候选相同种子的题面。</p><p>运行失败与环境不可用会保留在报告中。环境缺失不会伪造一个零分。<code>trusted</code> 只用于作者受控自检，不用于未知候选程序或模型排行榜。</p><div class="action-row">${driveLink(d.grader,'Drive · 自动评分器',true)}</div><h2>3. 导入报告，核对分数</h2><p>打开题目详情中的“导入评分报告”，选择验证器生成的 <code>results/P01.json</code>。网页检查题号、版本、种子、题包与验证器指纹，并按白名单中的检查权重重算分数。</p><p>每题满分 100，无人工评分环节。报告中有未执行检查时显示“未评分”；有已执行失败时保留部分分和失败说明。</p><p>本地 JSON 是可编辑文件。网页校验能发现格式与协议不一致，但不能证明文件未被人为构造；当前属于私人可复算的评测记录。</p><h2>4. 保存信息与同条件比较</h2><p>填写模型配置与测试条件后保存。比较页按相同版本、验证器、种子、平台、工具、运行环境与预算规则分组，再核对每题预算与题包。默认比较尝试 #1，不自动选最好一次。</p><p>缺测保持为空。部分题目的共同均分会注明覆盖数，完整 20 题总分留到第二轮完成后建立。</p><h2>5. 备份与恢复</h2><p>记录存在当前浏览器。使用“测试记录 → 导出备份”获得 JSON，再用“导入备份”恢复到另一个浏览器。导入采用合并，保留旧记录；同一记录的相同内容会跳过，不同内容会保留为独立记录。</p><div class="action-row"><button class="secondary" data-export>导出记录备份</button><button class="secondary" data-import>导入记录备份</button></div></div></section><aside class="panel"><div class="panel-heading"><h3>第二轮范围</h3></div><div class="panel-body"><p>3 道 Fortran、1 道 Lean、6 道主观题和 2 道聊天端题。</p><p class="muted">视频制作与参考重建将合并为同一题的 A/B 条件。聊天端保留单 HTML 工作台，另设可直接核验的推理题。</p><a class="text-button" href="#history">查看历史材料 →</a></div></aside></div>`;
}
function bindPage(page) {
  if(page==='library'||page==='history'){
    const historic=page==='history',f=historic?historyFilter:filter;
    const update=()=>{$('#task-table').innerHTML=taskTable(historic);};
    $('#search').addEventListener('input',e=>{f.query=e.target.value;update();});
    $('#category').addEventListener('change',e=>{f.category=e.target.value;update();});
    $('#level').addEventListener('change',e=>{f.level=e.target.value;update();});
    if($('#availability'))$('#availability').addEventListener('change',e=>{f.status=e.target.value;update();});
    $('#reset-filter').onclick=()=>resetFilter(historic);
  }
  if(page==='submit'){
    $('#submit-task').onchange=e=>navigate('#submit/'+e.target.value);
    $('#report-file').onchange=readReportFile;
    $('#report-text').oninput=e=>{submission.text=e.target.value;submission.result=null;submission.report=null;$('#report-preview').innerHTML='';$('#save-section').hidden=true;};
    $('#validate-report').onclick=validateSubmission;
    $('#save-report-form').onsubmit=saveReport;
  }
  if(page==='compare'){
    const all=comparableRecords(),cohorts=[...new Map(all.map(x=>[cohortKey(x.r,x.g),x])).entries()];
    if($('#cohort-select'))$('#cohort-select').onchange=e=>{selectedCohort=cohorts[Number(e.target.value)]?.[0]||'';selectedModels.clear();render();};
    const configs=[...new Map(all.filter(x=>cohortKey(x.r,x.g)===selectedCohort).map(x=>[modelKey(x.r),x.r])).entries()];
    document.querySelectorAll('[data-model-index]').forEach(input=>input.onchange=e=>{
      const key=configs[Number(input.dataset.modelIndex)]?.[0];if(!key)return;
      if(e.target.checked){if(selectedModels.size>=4){e.target.checked=false;toast('一次请选择至多 4 个模型配置。');return;}selectedModels.add(key);}else selectedModels.delete(key);
      $('#comparison').innerHTML=comparison();
    });
  }
}
function resetFilter(historic) {const fresh={query:'',category:'',level:'',status:''};if(historic)historyFilter=fresh;else filter=fresh;render();}
async function readReportFile(event) {
  const file=event.target.files?.[0];if(!file)return;
  const token=++reportReadToken;
  submission.result=null;submission.report=null;submission.text='';$('#report-text').value='';$('#report-preview').innerHTML='';$('#save-section').hidden=true;
  submission.filename=file.name;$('#file-status').textContent=file.name;
  if(/\.py$/i.test(file.name)){submission.error='你选择了 Python 源码。请先用右侧命令运行本地验证器，再上传生成的 JSON 报告。';submission.result=null;submission.report=null;$('#report-error').textContent=submission.error;$('#report-preview').innerHTML='';$('#save-section').hidden=true;return;}
  if(file.size>2*1024*1024){$('#report-error').textContent='报告超过 2 MB，请上传单题验证 JSON，不要上传源码包或附件。';return;}
  try{const value=await file.text();if(token!==reportReadToken||route().page!=='submit')return;submission.text=value;$('#report-text').value=value;validateSubmission();}catch(_){if(token===reportReadToken&&$('#report-error'))$('#report-error').textContent='文件读取失败，请重选文件或粘贴 JSON。';}
}
function validateSubmission() {
  try{
    const value=$('#report-text').value;submission.text=value;
    if(!value.trim())throw new Error('请选择或粘贴验证器生成的 JSON 报告。');
    if(value.length>2*1024*1024)throw new Error('报告内容超过 2 MB。');
    const report=JSON.parse(value),result=NRBReports.validateReport(report,RELEASE);
    if(result.taskId!==submission.task)throw new Error(`这份报告属于 ${result.taskId}。请在上方将题目切换为 ${result.taskId} 后再上传。`);
    submission.report=report;submission.result=result;submission.error='';
    $('#report-error').textContent='';$('#report-preview').innerHTML=reportPreview(result);$('#save-section').hidden=false;
    toast('报告核验完成，分数已按逐项检查重算。');
  }catch(error){submission.report=null;submission.result=null;submission.error=error instanceof SyntaxError?'JSON 无法解析，请上传完整报告，勿包含 Markdown 代码围栏。':error.message;$('#report-error').textContent=submission.error;$('#report-preview').innerHTML='';$('#save-section').hidden=true;}
}
function saveReport(event) {
  event.preventDefault();
  try{
    if(!submission.report)throw new Error('请先核验报告。');
    const g=NRBReports.validateReport(submission.report,RELEASE),meta=readMetadata(event.target);submission.metadata=meta;
    const r={...meta,schema:'nrb-browser-run-v3',id:newRecordId(),createdAt:new Date().toISOString(),source:'local-report-import',scoreKind:'automatic-report',task:g.taskId,taskVersion:g.version,packetHash:g.packetHash,rubric:g.version,score:g.score,scoreState:g.score===null?'pending':'scored',rawReport:submission.report};
    const duplicate=records.findIndex(x=>x?.schema==='nrb-browser-run-v3'&&modelKey(x)===modelKey(r)&&x.task===r.task&&Number(x.attempt)===r.attempt&&JSON.stringify(x.rawReport)===JSON.stringify(r.rawReport)&&x.harness===r.harness&&x.tools===r.tools&&x.environment===r.environment&&x.budget===r.budget);
    if(duplicate>=0){toast('该报告和模型配置已保存，已打开原记录。');navigate('#run/'+duplicate);return;}
    records.push(r);const saved=persist();submission={task:'',text:'',filename:'',error:'',result:null,report:null,metadata:{}};navigate('#run/'+(records.length-1));toast(saved?'评分报告已保存到本浏览器。':'保存失败：报告仍在内存中，请立即导出备份。');
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
    const data=JSON.parse(await file.text()),incoming=Array.isArray(data)?data:data?.records;
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
$('#backup-file').onchange=importBackup;
document.addEventListener('click',event=>{
  const el=event.target.closest('button,[data-close]');if(!el)return;
  if(el.dataset.close){$('#'+el.dataset.close).close();return;}
  if(el.hasAttribute('data-export'))return exportAll();
  if(el.hasAttribute('data-import'))return $('#backup-file').click();
  if(el.id==='empty-reset')return resetFilter(route().page==='history');
  if(el.dataset.runFilter){runFilter=el.dataset.runFilter;return render();}
  if(el.dataset.copyCommand)return copyCommand(el.dataset.copyCommand);
  if(el.dataset.edit!==undefined)return editRecord(Number(el.dataset.edit));
  if(el.dataset.delete!==undefined)return deleteRecord(Number(el.dataset.delete));
  if(el.dataset.exportOne!==undefined){const r=records[Number(el.dataset.exportOne)];return exportJSON({schemaVersion:3,exportedAt:new Date().toISOString(),records:[r]},`benchmark-${r?.task||'record'}-record.json`);}
  if(el.dataset.exportReport!==undefined){const r=records[Number(el.dataset.exportReport)];if(r?.rawReport)return exportJSON(r.rawReport,`${r.task}-report.json`);}
});
window.addEventListener('hashchange',render);
render();
