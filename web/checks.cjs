// Node-only contract and UI-state checks. Synthetic reports are not AI results.
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const NRBH02=require('./dist/h02-grader.js'),NRBSubjective=require('./dist/manual-grader.js');
const {validateReport,parseJSON}=require('./dist/report-validation.js');
const h02Answer=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/h02-author-control.json'),'utf8'));
const data=fs.readFileSync(path.join(__dirname,'dist/tasks-data.js'),'utf8');
const releaseText=fs.readFileSync(path.join(__dirname,'dist/release-data.js'),'utf8');
const historyText=fs.readFileSync(path.join(__dirname,'dist/release-history.js'),'utf8');
const app=fs.readFileSync(path.join(__dirname,'dist/app.js'),'utf8');
const plain=x=>JSON.parse(JSON.stringify(x));
const releaseContext={};vm.createContext(releaseContext);vm.runInContext(releaseText,releaseContext);const release=plain(releaseContext.NRB_RELEASE);
let checks=0;function check(label,fn){fn();checks++;}
function fixture({task='P01',seed=17,mode='pass',backend='docker'}={},contract=release){
  const release=contract;if(task==='H02'&&backend==='docker')backend='answer';
  const spec=release.grading.tasks[task].seeds[String(seed)];
  const cs=spec.checks.map(x=>({...x,passed:mode==='unscored'?null:mode==='zero'?false:true,detail:'Synthetic UI contract test; not a model run.'}));
  const status=mode==='unscored'?'unscored':mode==='zero'?'failed':'passed';
  const score=mode==='unscored'?null:mode==='zero'?0:100;
  return {schema:release.grading.schema,benchmark_version:release.version,grader_version:release.grading.grader_version,evaluator_fingerprint:release.grading.evaluatorFingerprint,task_id:task,seed,packet_hash:spec.packet_hash,test_manifest_hash:spec.test_manifest_hash,source_hash:'1'.repeat(64),checks:cs,score,total:score,status,critical_passed:mode==='unscored'?null:mode==='zero'?false:true,execution:{backend:mode==='unscored'?'none':backend,status:mode==='unscored'?'unavailable':'executed',image_id:'sha256:'+'2'.repeat(64)},control_only:backend==='trusted',comparison_eligible:mode!=='unscored'&&['docker','answer'].includes(backend),report_origin:'local_verifier',...(task==='H02'?{answer_payload:mode==='zero'?{}:h02Answer}:{})};
}
check('Strict JSON rejects duplicate keys and nonfinite numbers',()=>{for(const text of ['{"x":1,"x":2}','{"x":{"y":2,"y":3}}','[1e400]','{"x":NaN}'])assert.throws(()=>parseJSON(text));assert.deepEqual(parseJSON('{"nested":[1,{"text":"ok","nil":null}],"value":false}'),{nested:[1,{text:'ok',nil:null}],value:false});});
function rejection(label,modify){check(label,()=>{const r=fixture();modify(r);assert.throws(()=>validateReport(r,release));});}
check('20 tasks; all ready; unique IDs',()=>{assert.equal(release.tasks.length,20);assert.equal(release.tasks.filter(x=>x.status==='ready').length,20);assert.equal(release.tasks.filter(x=>x.status==='planned').length,0);assert.equal(new Set(release.tasks.map(x=>x.id)).size,20);});
check('Thirteen complete manifests',()=>{assert.equal(Object.keys(release.grading.tasks).length,13);for(const item of Object.values(release.grading.tasks)){assert.deepEqual(Object.keys(item.seeds).sort(),['0','17','2026']);}});
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
rejection('Reject grader version mismatch',r=>r.grader_version='unknown');
rejection('Reject old evaluator',r=>r.evaluator_fingerprint='0'.repeat(64));
rejection('Reject different packet',r=>r.packet_hash='0'.repeat(64));
rejection('Reject different manifest',r=>r.test_manifest_hash='0'.repeat(64));
rejection('Reject unsupported seed',r=>r.seed=19);
rejection('Reject boolean numeric seed',r=>r.seed=true);
rejection('Reject numeric passed marker',r=>r.checks[0].passed=1);
rejection('Reject boolean score',r=>r.score=true);
rejection('Reject an array masquerading as a source digest',r=>r.source_hash=['a'.repeat(64)]);
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
  function element(k){if(!elements.has(k))elements.set(k,{innerHTML:'',textContent:'',value:'',hidden:false,style:{},dataset:{},files:[],open:false,eventHandlers:{},insertAdjacentHTML(position,html){this.innerHTML=position==='afterbegin'?html+this.innerHTML:this.innerHTML+html;},addEventListener(type,fn){(this.eventHandlers[type]??=[]).push(fn);},dispatchEvent(event){for(const fn of this.eventHandlers[event.type]||[])fn(event);return true;},classList:{toggle(){},add(){},remove(){}},setAttribute(){},removeAttribute(){},showModal(){this.open=true;},close(){this.open=false;},click(){},select(){},remove(){},closest(){return null;}});return elements.get(k);}
  const ctx={console,Intl,URL,Blob,Date,Map,Set,JSON,document:{querySelector:element,querySelectorAll:selector=>selector==='[data-rating],[data-state],[data-evidence],#reviewer-id,#submission-id'?[element('#reviewer-id'),element('#submission-id')]:[],addEventListener(k,fn){listeners[k]=fn;},createElement:()=>element('created'),body:{appendChild(){}},execCommand:()=>true},location:{hash:'#overview'},localStorage:{getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v)},window:{scrollY:0,scrollTo(){},addEventListener(k,fn){listeners[k]=fn;}},setTimeout:()=>0,clearTimeout(){},crypto:cryptoCapability==="uuid"?{randomUUID:()=>crypto.randomUUID()}:cryptoCapability==="bytes"?{getRandomValues:bytes=>crypto.randomFillSync(bytes)}:undefined,navigator:{clipboard:{writeText:async()=>{}}},FormData:function(form){return Object.entries(form.testData||{});},NRBReports:{validateReport,parseJSON},NRBH02,NRBSubjective};
  vm.createContext(ctx);vm.runInContext(data+'\n'+releaseText+'\n'+historyText+'\n'+app,ctx);return {ctx,run:s=>vm.runInContext(s,ctx),element,store,listeners};
}
const ui=setup(),run=ui.run;
check('Historical 21 task identities preserved',()=>assert.equal(run('historicalTasks.length'),21));
check('No fabricated results on initial load',()=>{assert.equal(run('records.length'),0);assert.match(run('runs()'),/还没有测试记录/);assert.match(run('overview()'),/已评分记录<\/label><span class="value">0/);});
check('Current and historical library separated',()=>{assert.match(run('library(false)'),/20 道题/);assert.match(run('library(true)'),/21 道题/);});
check('Filter survives visiting details',()=>{run("filter.query='薄膜'");assert.match(run('taskTable(false)'),/1 \/ 20/);run("taskDetail('P04',false)");assert.match(run('taskTable(false)'),/1 \/ 20/);run("filter.query=''");});
check('Empty filter has a reset action',()=>{run("filter.query='no-such-task'");assert.match(run('taskTable(false)'),/empty-reset/);run("filter.query=''");});
check('Ready task has explicit next and return paths',()=>{const html=run("taskDetail('P04',false)");assert.match(html,/#submit\/P04/);assert.match(html,/#library/);assert.match(html,/完整题面/);});
check('New Fortran and Lean tasks have actual submission routes',()=>{for(const id of ['F01','F02','F03','L01'])assert.ok(run(`taskDetail('${id}',false)`).includes('#submit/'+id));});
check('Python form has no manual score field',()=>{const html=run("submissionPage('P01')");assert.ok(!/name="score"/.test(html));assert.match(html,/核验报告/);assert.match(html,/solution\.py/);});
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
check('Comparison retains missing tasks and common coverage',()=>{run("records=[{...inMetadata,schema:'nrb-browser-run-v3',task:'P01',rawReport:inReport},{...inMetadata,model:'SYNTHETIC B',schema:'nrb-browser-run-v3',task:'P01',rawReport:inReport}];selectedCohort=cohortKey(records[0],gradeRecord(records[0]));selectedModels=new Set(records.map(modelKey))");const html=run('comparison()');assert.match(html,/共同 1 \/ 20 题/);assert.match(html,/未测 \/ 无可比 #1/);});
check('Different budgets prevent paired means',()=>{run('records[1].budget=30');assert.match(run('comparison()'),/共同 0 \/ 20 题/);run('records[1].budget=15');});
check('Missing actual image identities cannot produce a matched condition',()=>{run("records[1]={...records[1],rawReport:JSON.parse(JSON.stringify(inReport))};delete records[1].rawReport.execution.image_id");assert.equal(run('comparableRecords().length'),1);assert.match(run('comparison()'),/共同 0 \/ 20 题/);});
check('Different images prevent pairing the same task',()=>{run("records[1]={...records[1],rawReport:JSON.parse(JSON.stringify(inReport))};records[1].rawReport.execution.image_id='different-image'");assert.equal(run('cohortKey(records[0],gradeRecord(records[0]))'),run('cohortKey(records[1],gradeRecord(records[1]))'));assert.match(run('comparison()'),/共同 0 \/ 20 题/);});
check('Duplicate first attempts are not cherry-picked',()=>{run("records[1].rawReport.execution.image_id=inReport.execution.image_id;records.push({...records[0],rawReport:JSON.parse(JSON.stringify(inReport))});records[2].rawReport.source_hash='9'.repeat(64)");assert.match(run('comparison()'),/重复 #1，需核对/);assert.match(run('comparison()'),/共同 0 \/ 20 题/);});
check('Unknown model metadata does not pair',()=>{run("records[0].version='未记录'");assert.equal(run('metadataComplete(records[0])'),false);});
function manualFixture(task='R01',mode=null,reviewer='SYNTHETIC REVIEWER'){
 const r=NRBSubjective.blank(task,mode,release);r.reviewer.id=reviewer;r.submission_id='synthetic-ui-control';
 r.ratings.forEach(x=>{x.level=4;x.evidence='Synthetic protocol control, not an observation of model output.';});
 r.requirements.forEach(x=>{x.status='pass';x.evidence='Synthetic protocol control.';});
 r.observations.forEach(x=>{x.status='observed';x.evidence='Synthetic protocol control.';});return r;
}
check('H02 recomputes raw answers, including a valid JSON null scored zero',()=>{
 assert.equal(validateReport(NRBH02.report(h02Answer,release),release).score,100);
 assert.equal(validateReport(NRBH02.report(null,release),release).score,0);
 for(const seed of ['17',[17],true,null,undefined]){const r=NRBH02.report(h02Answer,release);r.seed=seed;assert.throws(()=>validateReport(r,release));}
 const h=setup();h.run("submissionPage('H02')");h.element('#report-text').value='null';h.run('validateSubmission()');assert.equal(h.run('submission.result.score'),0);
});
check('Partial Python score rounded to six decimals remains importable',()=>{const r=fixture();r.checks[0].passed=false;r.score=r.total=82.857143;r.status='failed';r.critical_passed=false;assert.ok(Math.abs(validateReport(r,release).score-r.score)<5.1e-7);});
check('Manual rubric has no editable total, and pending remains null',()=>{
 const r=NRBSubjective.blank('R01',null,release);assert.equal(validateReport(r,release).score,null);
 assert.equal(validateReport(manualFixture(),release).score,100);
 const html=run("submissionPage('R01')");assert.ok(!/name="score"/.test(html));assert.match(html,/data-rating/);assert.match(html,/具体证据/);
 const draft=manualFixture('R06','A');draft.requirements.find(x=>x.id==='mode_integrity').status='fail';assert.equal(validateReport(draft,release).comparisonEligible,false);
});
check('Full twenty-task comparison requires all twenty matched protocols',()=>{
 const h=setup(),records=[];
 for(const model of ['SYNTHETIC A','SYNTHETIC B'])for(const task of release.tasks){const raw=task.scoring==='manual'?manualFixture(task.id,task.id==='R06'?'A':null):fixture({task:task.id});records.push({...metadata,model,schema:'nrb-browser-run-v3',task:task.id,rawReport:raw});}
 h.ctx.inRecords=records;h.run('records=inRecords;selectedCohort=cohortKey(records[0],gradeRecord(records[0]));selectedModels=new Set(records.map(modelKey))');
 assert.match(h.run('comparison()'),/共同 20 \/ 20 题/);assert.match(h.run('comparison()'),/完整 20 题均分/);
 h.ctx.otherMode=manualFixture('R06','B');h.run("records.find(r=>r.model==='SYNTHETIC B'&&r.task==='R06').rawReport=otherMode");assert.match(h.run('comparison()'),/共同 19 \/ 20 题/);
 h.ctx.otherReviewer=manualFixture('R01',null,'OTHER REVIEWER');h.run("records.find(r=>r.model==='SYNTHETIC B'&&r.task==='R01').rawReport=otherReviewer");assert.match(h.run('comparison()'),/共同 18 \/ 20 题/);
});
check('First-round V2 reports retain their own eight-task release identity',()=>{
 const h=setup(),oldRelease=plain(h.run("NRB_RELEASE_HISTORY['2.0.0-rc.1']")),r=fixture({},oldRelease);
 h.ctx.oldReport=r;assert.equal(h.run('validateRawReport(oldReport).version'),'2.0.0-rc.1');
 h.ctx.inMetadata=metadata;h.run("records=[{...inMetadata,schema:'nrb-browser-run-v3',task:'P01',rawReport:oldReport},{...inMetadata,model:'SYNTHETIC B',schema:'nrb-browser-run-v3',task:'P01',rawReport:oldReport}];selectedCohort=cohortKey(records[0],gradeRecord(records[0]));selectedModels=new Set(records.map(modelKey))");assert.match(h.run('comparison()'),/共同 1 \/ 8 题/);
});
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
    assert.match(h.element('#report-error').textContent,/程序源码/);
  });
  await checked('A late file read cannot overwrite another task or typed answer',async()=>{
    const h=setup();h.run("location.hash='#submit/P01';submissionPage('P01')");let finish;
    const pending=h.run('readReportFile')({target:{files:[{name:'P01.json',size:200,text:()=>new Promise(resolve=>{finish=resolve;})}]}});
    h.run("location.hash='#submit/H02';submissionPage('H02');bindPage('submit')");h.element('#report-text').value='new draft';h.element('#report-text').oninput({target:{value:'new draft'}});
    finish(JSON.stringify(fixture()));await pending;assert.equal(h.run('submission.text'),'new draft');assert.equal(h.run('submission.report'),null);
  });
  await checked('Oversized JSON never retains an old score',async()=>{
    const h=setup();h.ctx.inReport=fixture();h.run("submissionPage('P01');submission.report=inReport;submission.result=NRBReports.validateReport(inReport,RELEASE)");
    await h.run('readReportFile')({target:{files:[{name:'large.json',size:3*1024*1024,text:async()=>''}]}});
    assert.equal(h.run('submission.report'),null);assert.equal(h.element('#save-section').hidden,true);
    assert.match(h.element('#report-error').textContent,/超过 2 MB/);
  });
  function reviewUI(task='R06',mode='A'){
    const h=setup();h.ctx.reviewTask=task;h.ctx.reviewMode=mode;
    h.run("location.hash='#submit/'+reviewTask;videoMode=reviewMode;render()");
    h.element('#reviewer-id').value='EXISTING REVIEWER';h.element('#submission-id').value='existing-draft';
    return h;
  }
  function acceptOldReview(h,task='R06',mode='A'){
    h.ctx.oldReview=manualFixture(task,mode);h.run('displayReviewResult(oldReview,NRBSubjective.validate(oldReview,RELEASE))');
    assert.equal(h.element('#save-section').hidden,false);assert.notEqual(h.element('#report-preview').innerHTML,'');
  }
  const reviewFile=(read,size=200)=>({target:{files:[{name:'review.json',size,text:read}]}});
  await checked('Current manual import binds the chosen task and preserves imported evidence',async()=>{
    const h=reviewUI(),review=manualFixture('R06','A','IMPORTED REVIEWER');
    await h.element('#review-import').onchange(reviewFile(async()=>JSON.stringify(review)));
    assert.equal(h.run('submission.result.score'),100);
    assert.equal(h.run('submission.report.reviewer.id'),'IMPORTED REVIEWER');
    assert.deepEqual(plain(h.run("reviewDrafts['R06-A']")),review);
    assert.equal(h.element('#save-section').hidden,false);assert.equal(h.element('#review-error').textContent,'');
  });
  await checked('Invalid manual JSON clears the old accepted preview and save state first',async()=>{
    const h=reviewUI();acceptOldReview(h);let finish;
    const pending=h.element('#review-import').onchange(reviewFile(()=>new Promise(resolve=>{finish=resolve;})));
    assert.equal(h.run('submission.report'),null);assert.equal(h.run('submission.result'),null);
    assert.equal(h.element('#report-preview').innerHTML,'');assert.equal(h.element('#save-section').hidden,true);
    finish(JSON.stringify({schema:'bad-review',score:100}));await pending;
    assert.match(h.element('#review-error').textContent,/完整量表/);
    assert.equal(h.run('submission.report'),null);assert.equal(h.element('#save-section').hidden,true);
    assert.equal(h.element('#report-preview').innerHTML,'');
  });
  await checked('Oversized manual JSON clears accepted state without reading file bytes',async()=>{
    const h=reviewUI();acceptOldReview(h);let read=false;
    await h.element('#review-import').onchange(reviewFile(async()=>{read=true;return '{}';},3*1024*1024));
    assert.equal(read,false);assert.equal(h.run('submission.report'),null);assert.equal(h.run('submission.result'),null);
    assert.equal(h.element('#report-preview').innerHTML,'');assert.equal(h.element('#save-section').hidden,true);
    assert.match(h.element('#review-error').textContent,/超过 2 MB/);
  });
  await checked('Late manual success is ignored after switching modes and returning',async()=>{
    const h=reviewUI();let finish;
    const pending=h.element('#review-import').onchange(reviewFile(()=>new Promise(resolve=>{finish=resolve;})));
    h.element('#review-mode').onchange({target:{value:'B'}});
    h.element('#review-mode').onchange({target:{value:'A'}});
    const current=plain(h.run("reviewDrafts['R06-A']"));
    finish(JSON.stringify(manualFixture('R06','A','LATE REVIEWER')));await pending;
    assert.deepEqual(plain(h.run("reviewDrafts['R06-A']")),current);
    assert.equal(h.run('submission.report'),null);assert.equal(h.element('#save-section').hidden,true);
  });
  await checked('Late manual success cannot overwrite another task draft',async()=>{
    const h=reviewUI('R01',null);let finish;
    const pending=h.element('#review-import').onchange(reviewFile(()=>new Promise(resolve=>{finish=resolve;})));
    h.run("location.hash='#submit/R02';render()");const current=plain(h.run("reviewDrafts.R02"));
    finish(JSON.stringify(manualFixture('R01')));await pending;
    assert.equal(h.run('submission.task'),'R02');assert.equal(h.run('submission.report'),null);
    assert.deepEqual(plain(h.run('reviewDrafts.R02')),current);assert.equal(h.element('#review-error').textContent,'');
  });
  await checked('Editing a review invalidates a pending import in the same form',async()=>{
    const h=reviewUI();let finish;
    const pending=h.element('#review-import').onchange(reviewFile(()=>new Promise(resolve=>{finish=resolve;})));
    h.element('#reviewer-id').value='USER EDIT AFTER IMPORT';
    h.element('#reviewer-id').dispatchEvent({type:'input',target:h.element('#reviewer-id')});
    finish(JSON.stringify(manualFixture('R06','A','LATE REVIEWER')));await pending;
    assert.equal(h.run("reviewDrafts['R06-A'].reviewer.id"),'USER EDIT AFTER IMPORT');
    assert.equal(h.run('submission.report'),null);assert.equal(h.element('#save-section').hidden,true);
  });
  await checked('Explicit manual recalculation supersedes a pending imported file',async()=>{
    const h=reviewUI();h.ctx.currentReview=manualFixture('R06','A','CURRENT FORM REVIEWER');
    h.run("reviewDrafts['R06-A']=currentReview");
    h.element('#reviewer-id').value='CURRENT FORM REVIEWER';h.element('#submission-id').value='current-form';
    let finish;const pending=h.element('#review-import').onchange(reviewFile(()=>new Promise(resolve=>{finish=resolve;})));
    h.element('#calculate-review').onclick();
    assert.equal(h.run('submission.result.score'),100);assert.equal(h.run('submission.report.submission_id'),'current-form');
    finish(JSON.stringify(manualFixture('R06','A','LATE FILE REVIEWER')));await pending;
    assert.equal(h.run('submission.report.reviewer.id'),'CURRENT FORM REVIEWER');
    assert.equal(h.run('submission.report.submission_id'),'current-form');assert.equal(h.element('#save-section').hidden,false);
  });
  await checked('Late manual read errors are ignored when the form no longer exists',async()=>{
    const h=reviewUI();let fail;
    const pending=h.element('#review-import').onchange(reviewFile(()=>new Promise((_,reject)=>{fail=reject;})));
    h.run("location.hash='#runs';render()");
    const select=h.ctx.document.querySelector;let touched=false;
    h.ctx.document.querySelector=selector=>{if(selector==='#review-error'){touched=true;return null;}return select(selector);};
    fail(Error('LATE READ ERROR'));await pending;
    assert.equal(touched,false);assert.equal(h.run('submission.report'),null);
  });
  await checked('A later manual import wins and an older rejection cannot erase it',async()=>{
    const h=reviewUI();let fail;
    const pending=h.element('#review-import').onchange(reviewFile(()=>new Promise((_,reject)=>{fail=reject;})));
    const latest=manualFixture('R06','A','LATEST REVIEWER');
    await h.element('#review-import').onchange(reviewFile(async()=>JSON.stringify(latest)));
    fail(Error('OLD READ ERROR'));await pending;
    assert.equal(h.run('submission.report.reviewer.id'),'LATEST REVIEWER');assert.equal(h.run('submission.result.score'),100);
    assert.equal(h.element('#save-section').hidden,false);assert.equal(h.element('#review-error').textContent,'');
  });
  check('Delete requires explicit confirmation',()=>{
    const h=setup(JSON.stringify([{id:'a',task:'C01',model:'Historical'}]));h.run('deleteRecord(0)');assert.equal(h.run('records.length'),1);h.element('#confirm-action').onclick();assert.equal(h.run('records.length'),0);
  });
  console.log(`PASS: ${checks} Node contract/state checks. Includes report forgery rejection, null/zero semantics, legacy preservation, save/restore/delete handlers, comparable subsets, image/budget separation and duplicate-attempt exclusion. DOM stubs; browser QA is separate. No model was evaluated.`);
}
asyncChecks().catch(error=>{console.error(error);process.exitCode=1;});
