// Node-only contract and UI-state checks. Synthetic reports are not AI results.
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {validateReport}=require('./dist/report-validation.js');
const data=fs.readFileSync(path.join(__dirname,'dist/tasks-data.js'),'utf8');
const releaseText=fs.readFileSync(path.join(__dirname,'dist/release-data.js'),'utf8');
const app=fs.readFileSync(path.join(__dirname,'dist/app.js'),'utf8');
const plain=x=>JSON.parse(JSON.stringify(x));
const releaseContext={};vm.createContext(releaseContext);vm.runInContext(releaseText,releaseContext);const release=plain(releaseContext.NRB_RELEASE);
let checks=0;function check(label,fn){fn();checks++;}
function fixture({task='P01',seed=17,mode='pass',backend='docker'}={}){
  const spec=release.grading.tasks[task].seeds[String(seed)];
  const cs=spec.checks.map(x=>({...x,passed:mode==='unscored'?null:mode==='zero'?false:true,detail:'Synthetic UI contract test; not a model run.'}));
  const status=mode==='unscored'?'unscored':mode==='zero'?'failed':'passed';
  const score=mode==='unscored'?null:mode==='zero'?0:100;
  return {schema:release.grading.schema,benchmark_version:release.version,grader_version:release.grading.grader_version,evaluator_fingerprint:release.grading.evaluatorFingerprint,task_id:task,seed,packet_hash:spec.packet_hash,test_manifest_hash:spec.test_manifest_hash,source_hash:'1'.repeat(64),checks:cs,score,total:score,status,critical_passed:mode==='unscored'?null:mode==='zero'?false:true,execution:{backend:mode==='unscored'?'none':backend,status:mode==='unscored'?'unavailable':'executed',image_id:'sha256:'+'2'.repeat(64)},control_only:backend==='trusted',comparison_eligible:mode!=='unscored'&&backend==='docker',report_origin:'local_verifier'};
}
function rejection(label,modify){check(label,()=>{const r=fixture();modify(r);assert.throws(()=>validateReport(r,release));});}
check('20 tasks; 8 ready; 12 planned; unique IDs',()=>{assert.equal(release.tasks.length,20);assert.equal(release.tasks.filter(x=>x.status==='ready').length,8);assert.equal(release.tasks.filter(x=>x.status==='planned').length,12);assert.equal(new Set(release.tasks.map(x=>x.id)).size,20);});
check('Eight complete manifests',()=>{assert.equal(Object.keys(release.grading.tasks).length,8);for(const item of Object.values(release.grading.tasks)){assert.deepEqual(Object.keys(item.seeds).sort(),['0','17','2026']);}});
check('100 is recomputed from complete checks',()=>{const g=validateReport(fixture(),release);assert.equal(g.score,100);assert.equal(g.status,'passed');assert.equal(g.comparisonEligible,true);});
check('Executed zero remains zero',()=>{const g=validateReport(fixture({mode:'zero'}),release);assert.equal(g.score,0);assert.equal(g.status,'failed');});
check('Unavailable is null, never zero',()=>{const g=validateReport(fixture({mode:'unscored'}),release);assert.equal(g.score,null);assert.equal(g.comparisonEligible,false);});
check('Trusted author control does not enter model comparison',()=>{const g=validateReport(fixture({backend:'trusted'}),release);assert.equal(g.score,100);assert.equal(g.controlOnly,true);assert.equal(g.comparisonEligible,false);});
check('P01 weighted partial score',()=>{const r=fixture();assert.equal(r.checks[0].weight,12);r.checks[0].passed=false;r.score=r.total=82.85714285714286;r.status='failed';r.critical_passed=false;const g=validateReport(r,release);assert.equal(g.failedCount,1);assert.ok(Math.abs(g.score-82.85714285714286)<1e-10);});
check('Check order is not a hidden output requirement',()=>{const r=fixture();r.checks.reverse();assert.equal(validateReport(r,release).score,100);});
rejection('Reject forged total',r=>r.total=99);
rejection('Reject forged score',r=>r.score=99);
rejection('Reject forged weight',r=>r.checks[0].weight=700);
rejection('Reject duplicate checks',r=>r.checks[1]=plain(r.checks[0]));
rejection('Reject omitted checks',r=>r.checks.pop());
rejection('Reject extra check',r=>r.checks.push({id:'free-points',weight:10,passed:true}));
rejection('Reject unknown check',r=>r.checks[0].id='not-in-manifest');
rejection('Reject wrong task',r=>r.task_id='F01');
rejection('Reject wrong version',r=>r.benchmark_version='1.1.0');
rejection('Reject grader version mismatch',r=>r.grader_version='2.0.0');
rejection('Reject old evaluator',r=>r.evaluator_fingerprint='0'.repeat(64));
rejection('Reject different packet',r=>r.packet_hash='0'.repeat(64));
rejection('Reject different manifest',r=>r.test_manifest_hash='0'.repeat(64));
rejection('Reject unsupported seed',r=>r.seed=19);
rejection('Reject boolean numeric seed',r=>r.seed=true);
rejection('Reject numeric passed marker',r=>r.checks[0].passed=1);
rejection('Reject boolean score',r=>r.score=true);
rejection('Reject missing provenance',r=>delete r.report_origin);
rejection('Reject unavailable with passing score',r=>r.execution.status='unavailable');
rejection('Reject failed process with full pass',r=>r.execution.status='failed');
rejection('Reject failed process with partial passing checks',r=>{r.checks[0].passed=false;r.score=r.total=82.85714285714286;r.status='failed';r.critical_passed=false;r.execution.status='failed';});
check('Worker failure is a complete executed zero',()=>{const r=fixture({mode:'zero'});r.execution.status='failed';const g=validateReport(r,release);assert.equal(g.score,0);assert.equal(g.failedCount,g.checks.length);});
rejection('Reject trusted promoted to model result',r=>{r.execution.backend='trusted';r.control_only=true;r.comparison_eligible=true;});
rejection('Reject trusted without control flag',r=>r.execution.backend='trusted');
check('All supported task/seed identities are accepted',()=>{for(const task of Object.keys(release.grading.tasks))for(const seed of [0,17,2026])assert.equal(validateReport(fixture({task,seed}),release).score,100);});
function setup(saved=null,cryptoCapability="uuid"){
  const elements=new Map(),store=new Map(saved===null?[]:[["research-benchmark-prototype-v1",saved]]),listeners={};
  function element(k){if(!elements.has(k))elements.set(k,{innerHTML:'',textContent:'',value:'',hidden:false,style:{},dataset:{},files:[],open:false,insertAdjacentHTML(position,html){this.innerHTML=position==='afterbegin'?html+this.innerHTML:this.innerHTML+html;},addEventListener(){},classList:{toggle(){},add(){},remove(){}},setAttribute(){},removeAttribute(){},showModal(){this.open=true;},close(){this.open=false;},click(){},select(){},remove(){},closest(){return null;}});return elements.get(k);}
  const ctx={console,Intl,URL,Blob,Date,Map,Set,JSON,document:{querySelector:element,querySelectorAll:()=>[],addEventListener(k,fn){listeners[k]=fn;},createElement:()=>element('created'),body:{appendChild(){}},execCommand:()=>true},location:{hash:'#overview'},localStorage:{getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v)},window:{scrollY:0,scrollTo(){},addEventListener(k,fn){listeners[k]=fn;}},setTimeout:()=>0,clearTimeout(){},crypto:cryptoCapability==="uuid"?{randomUUID:()=>crypto.randomUUID()}:cryptoCapability==="bytes"?{getRandomValues:bytes=>crypto.randomFillSync(bytes)}:undefined,navigator:{clipboard:{writeText:async()=>{}}},FormData:function(form){return Object.entries(form.testData||{});},NRBReports:{validateReport}};
  vm.createContext(ctx);vm.runInContext(data+'\n'+releaseText+'\n'+app,ctx);return {ctx,run:s=>vm.runInContext(s,ctx),element,store,listeners};
}
const ui=setup(),run=ui.run;
check('Historical 21 task identities preserved',()=>assert.equal(run('historicalTasks.length'),21));
check('No fabricated results on initial load',()=>{assert.equal(run('records.length'),0);assert.match(run('runs()'),/还没有测试记录/);assert.match(run('overview()'),/已导入模型报告<\/label><span class="value">0/);});
check('Current and historical library separated',()=>{assert.match(run('library(false)'),/20 道题/);assert.match(run('library(true)'),/21 道题/);});
check('Filter survives visiting details',()=>{run("filter.query='薄膜'");assert.match(run('taskTable(false)'),/1 \/ 20/);run("taskDetail('P04',false)");assert.match(run('taskTable(false)'),/1 \/ 20/);run("filter.query=''");});
check('Empty filter has a reset action',()=>{run("filter.query='no-such-task'");assert.match(run('taskTable(false)'),/empty-reset/);run("filter.query=''");});
check('Ready task has explicit next and return paths',()=>{const html=run("taskDetail('P04',false)");assert.match(html,/#submit\/P04/);assert.match(html,/#library/);assert.match(html,/完整题面/);});
check('Planned tasks cannot submit',()=>{const html=run("taskDetail('F01',false)");assert.match(html,/第二轮完成/);assert.ok(!html.includes('#submit/F01'));});
check('Python form has no manual score field',()=>{const html=run("submissionPage('P01')");assert.ok(!/name="score"/.test(html));assert.match(html,/核验报告并重算分数/);assert.match(html,/不执行 Python/);});
check('Commands match the delivered submission directories',()=>{assert.match(run("cliCommand('P08')"),/--source submissions\/P08\/solution\.py/);assert.ok(!run('guide()').includes('received/'));assert.match(run("submissionPage('P01')"),/submissions\/P01\/solution\.py/);});
check('All current task detail views are renderable',()=>{for(const t of release.tasks){const html=run(`taskDetail('${t.id}',false)`);assert.ok(html.includes(t.title));assert.ok(html.includes('返回'));}});
check('Missing raw report cannot smuggle a manual score',()=>{const g=run("gradeRecord({schema:'nrb-browser-run-v3',score:100,scoreState:'scored'})");assert.equal(g.valid,false);assert.equal(g.score,null);});
check('Escaping untrusted content',()=>assert.equal(run("esc('<img src=x onerror=alert(1)>')"),'&lt;img src=x onerror=alert(1)&gt;'));
check('Google Drive resource scheme is allowlisted',()=>{assert.equal(run("safeDrive({url:'javascript:alert(1)'})"),null);assert.equal(run("safeDrive({url:'https://drive.google.com.attacker.test/file'})"),null);assert.equal(run("safeDrive({url:'https://drive.google.com/file/d/id/view'})"),'https://drive.google.com/file/d/id/view');});
const old=[{id:'old',task:'C04',model:'Old model',score:71,scoreState:'scored',extra:{preserve:true}},{id:'unknown',task:'UNKNOWN',note:'Keep without rewriting'}];
check('Legacy storage stays byte-equivalent as data',()=>{const h=setup(JSON.stringify(old));assert.deepEqual(plain(h.run('records')),old);h.run('persist()');assert.deepEqual(JSON.parse(h.store.get('research-benchmark-prototype-v1')),old);});
check('Malformed storage is not overwritten',()=>{const h=setup('{bad-json');assert.equal(h.run('storageLoaded'),false);assert.equal(h.run('persist()'),false);assert.equal(h.store.get('research-benchmark-prototype-v1'),'{bad-json');assert.equal(h.run('unreadableStorage'),'{bad-json');});
const metadata={model:'SYNTHETIC A',version:'test-fixture-only',reasoning:'high',date:'2026-10-23',harness:'unit-test',tools:'none',environment:'test-image',budgetPolicy:'fixed',budget:15,attemptPolicy:'first attempt',attempt:1,notes:'Synthetic UI test, not a model run.'};
ui.ctx.inReport=fixture();ui.ctx.inMetadata=metadata;
check('Real save handler persists a revalidated report',()=>{run("submissionPage('P01');submission.report=inReport;submission.result=NRBReports.validateReport(inReport,RELEASE)");const form=ui.element('#save-report-form');form.testData=metadata;run('saveReport')({preventDefault(){},target:form});assert.equal(run('records.length'),1);assert.equal(run('records[0].score'),100);assert.equal(run('gradeRecord(records[0]).valid'),true);assert.equal(JSON.parse(ui.store.get('research-benchmark-prototype-v1')).length,1);});
check('Saving works without randomUUID in an HTTP context',()=>{const h=setup(null,'bytes');h.ctx.inReport=fixture();h.run("submissionPage('P01');submission.report=inReport;submission.result=NRBReports.validateReport(inReport,RELEASE)");const f=h.element('#save-report-form');f.testData=metadata;h.run('saveReport')({preventDefault(){},target:f});assert.equal(h.run('records.length'),1);assert.match(h.run('records[0].id'),/^local-/);assert.equal(JSON.parse(h.store.get('research-benchmark-prototype-v1')).length,1);});
check('Fallback IDs work with no crypto API and stay distinct',()=>{const h=setup(null,'none');const ids=h.run('Array.from({length:100},()=>newRecordId())');assert.equal(new Set(ids).size,100);assert.ok(ids.every(x=>x.startsWith('local-')));});
check('Zero and unscored records render differently',()=>{ui.ctx.inZero=fixture({mode:'zero'});ui.ctx.inNull=fixture({mode:'unscored'});assert.equal(run("recordScore({schema:'nrb-browser-run-v3',rawReport:inZero})"),'0');assert.equal(run("recordScore({schema:'nrb-browser-run-v3',rawReport:inNull})"),'—');});
check('Comparison retains missing tasks and common coverage',()=>{run("records=[{...inMetadata,schema:'nrb-browser-run-v3',task:'P01',rawReport:inReport},{...inMetadata,model:'SYNTHETIC B',schema:'nrb-browser-run-v3',task:'P01',rawReport:inReport}];selectedCohort=cohortKey(records[0],gradeRecord(records[0]));selectedModels=new Set(records.map(modelKey))");const html=run('comparison()');assert.match(html,/共同 1 \/ 8 题/);assert.match(html,/未测 \/ 无可比 #1/);});
check('Different budgets prevent paired means',()=>{run('records[1].budget=30');assert.match(run('comparison()'),/共同 0 \/ 8 题/);run('records[1].budget=15');});
check('Different images separate cohorts',()=>{run("records[1]={...records[1],rawReport:JSON.parse(JSON.stringify(inReport))};records[1].rawReport.execution.image_id='different-image'");assert.notEqual(run('cohortKey(records[0],gradeRecord(records[0]))'),run('cohortKey(records[1],gradeRecord(records[1]))'));});
check('Duplicate first attempts are not cherry-picked',()=>{run("records[1].rawReport.execution.image_id=inReport.execution.image_id;records.push({...records[0],rawReport:JSON.parse(JSON.stringify(inReport))});records[2].rawReport.source_hash='9'.repeat(64)");assert.match(run('comparison()'),/重复 #1，需核对/);assert.match(run('comparison()'),/共同 0 \/ 8 题/);});
check('Unknown model metadata does not pair',()=>{run("records[0].version='未记录'");assert.equal(run('metadataComplete(records[0])'),false);});
const historicalManifest=JSON.parse(fs.readFileSync(path.join(__dirname,'import-manifest.json'),'utf8'));
check('Historical packet bytes untouched',()=>{for(const t of historicalManifest.tasks){const bytes=fs.readFileSync(path.join(__dirname,'dist',t.packet));assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),t.sha256);}});
check('Current packet paths exist',()=>{for(const t of release.tasks.filter(x=>x.status==='ready'))assert.ok(fs.statSync(path.join(__dirname,'dist',t.packet)).size>0);});
async function asyncChecks(){
  async function checked(label,fn){await fn();checks++;}
  await checked('Backup import merges and preserves conflicting IDs',async()=>{
    const saved=[{id:'same-id',task:'C01',model:'Historical',notes:'Original'}];
    const h=setup(JSON.stringify(saved));
    const input={records:[saved[0],{...saved[0],notes:'Revised in another browser'}]};
    await h.run('importBackup')({target:{files:[{size:200,text:async()=>JSON.stringify(input)}],value:'file'}});
    assert.equal(h.run('records.length'),1);
    h.element('#confirm-action').onclick();
    assert.equal(h.run('records.length'),2);
    assert.equal(h.run('records[0].notes'),'Original');
    assert.equal(h.run('records[1].importedOriginalId'),'same-id');
    assert.notEqual(h.run('records[1].id'),'same-id');
  });
  await checked('Backup conflict recovery works without randomUUID',async()=>{
    const original={id:'same-id',task:'C01',model:'Historical',notes:'Original'};const h=setup(JSON.stringify([original]),'bytes');
    await h.run('importBackup')({target:{files:[{size:200,text:async()=>JSON.stringify({records:[{...original,notes:'Changed'}],unreadablePreviousStorage:'preserved raw text'})}],value:'file'}});
    h.element('#confirm-action').onclick();assert.equal(h.run('records.length'),3);assert.notEqual(h.run('records[1].id'),h.run('records[2].id'));assert.equal(h.run('records[1].importedOriginalId'),'same-id');assert.equal(h.run('records[2].raw'),'preserved raw text');
  });
  await checked('Backup invalid automated reports stay unscored',async()=>{
    const h=setup();
    const record={schema:'nrb-browser-run-v3',task:'P01',score:100,scoreState:'scored',id:'bad-report',model:'Synthetic'};
    await h.run('importBackup')({target:{files:[{size:200,text:async()=>JSON.stringify({records:[record]})}],value:'file'}});
    h.element('#confirm-action').onclick();
    assert.equal(h.run('records.length'),1);
    assert.equal(h.run('gradeRecord(records[0]).valid'),false);
    assert.equal(h.run('recordScore(records[0])'),'—');
  });
  await checked('Selecting Python source clears a stale accepted report',async()=>{
    const h=setup();h.ctx.inReport=fixture();h.run("submissionPage('P01');submission.report=inReport;submission.result=NRBReports.validateReport(inReport,RELEASE)");
    await h.run('readReportFile')({target:{files:[{name:'solution.py',size:200,text:async()=>''}]}});
    assert.equal(h.run('submission.report'),null);assert.equal(h.element('#save-section').hidden,true);
    assert.match(h.element('#report-error').textContent,/Python 源码/);
  });
  await checked('Oversized JSON never retains an old score',async()=>{
    const h=setup();h.ctx.inReport=fixture();h.run("submissionPage('P01');submission.report=inReport;submission.result=NRBReports.validateReport(inReport,RELEASE)");
    await h.run('readReportFile')({target:{files:[{name:'large.json',size:3*1024*1024,text:async()=>''}]}});
    assert.equal(h.run('submission.report'),null);assert.equal(h.element('#save-section').hidden,true);
    assert.match(h.element('#report-error').textContent,/超过 2 MB/);
  });
  check('Delete requires explicit confirmation',()=>{
    const h=setup(JSON.stringify([{id:'a',task:'C01',model:'Historical'}]));h.run('deleteRecord(0)');assert.equal(h.run('records.length'),1);h.element('#confirm-action').onclick();assert.equal(h.run('records.length'),0);
  });
  console.log(`PASS: ${checks} Node contract/state checks. Includes report forgery rejection, null/zero semantics, legacy preservation, save/restore/delete handlers, comparable subsets, image/budget separation and duplicate-attempt exclusion. DOM stubs; browser QA is separate. No model was evaluated.`);
}
asyncChecks().catch(error=>{console.error(error);process.exitCode=1;});
