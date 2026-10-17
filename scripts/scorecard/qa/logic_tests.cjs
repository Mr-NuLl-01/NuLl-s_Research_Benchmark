/* Dependency-free JS state/validation tests with a minimal DOM stub.
 * This does NOT validate layout, browser behavior, downloads or printing.
 * All review content below is explicitly synthetic QA input, not assessment.
 */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(path.join(__dirname,'../../../docs/v1.1/scorecard.html'),'utf8');
const catalog=JSON.parse(html.match(/<script id="catalog-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const script=html.split('<script>')[1].split('</script>')[0];
const fixtureRoot=process.argv[2];if(!fixtureRoot)throw Error('Pass synthetic fixture directory.');
const elements=new Map(),downloads=[];
class Element{constructor(){this.textContent='';this.innerHTML='';this.value='';this.dataset={};this.classList={toggle(){}};}addEventListener(){}appendChild(){}remove(){}click(){} }
const document={documentElement:{lang:''},body:new Element(),getElementById(id){if(!elements.has(id))elements.set(id,new Element());return elements.get(id);},querySelectorAll(){return[]},createElement(){return new Element()}};
document.getElementById('catalog-data').textContent=JSON.stringify(catalog);
const context=vm.createContext({document,window:{addEventListener(){},scrollTo(){},print(){}},console,Blob,URL:{createObjectURL(blob){downloads.push(blob);return 'blob:synthetic-test';},revokeObjectURL(){}},setTimeout(){},confirm(){return true}});
vm.runInContext(script,context);
const run=code=>vm.runInContext(code,context);
const json=code=>JSON.parse(run(`JSON.stringify(${code})`));
const checks=[];function ok(name){checks.push(name);console.log('PASS',name)}
function fixture(tid,name='review.json'){return JSON.parse(fs.readFileSync(path.join(fixtureRoot,tid,name),'utf8'));}
async function load(tid,includeAuto=true){const values=[['review.json',fixture(tid)],...(includeAuto?[['automatic.json',fixture(tid,'automatic.json')]]:[])];for(const[name,obj]of values){context.syntheticFiles=[{name, size:JSON.stringify(obj).length,text:async()=>JSON.stringify(obj)}];await run('importFiles(syntheticFiles)');assert(!document.getElementById('messages').className.includes('error'),document.getElementById('messages').textContent);}}
function edit(kind,index,key,value){context.target={dataset:{kind,index:String(index),key},type:typeof value==='boolean'?'checkbox':'text',checked:value,value:String(value)};run('edit(target)');}
function fillQuality(tid,type='human'){edit('reviewer',0,'type',type);edit('reviewer',0,'id','SYNTHETIC QA ONLY — not an actual reviewer');const n=fixture(tid).criteria.length;for(let i=0;i<n;i++){edit('criterion',i,'score','2');edit('criterion',i,'evidence','Synthetic serialization test; not scientific evidence.');edit('criterion',i,'rationale','Test fixture only; do not publish as an assessment.');}for(let i=0;i<fixture(tid).essential_review.length;i++){edit('essential',i,'outcome','fail');edit('essential',i,'evidence','No actual candidate output was evaluated.');edit('essential',i,'rationale','Explicit synthetic QA fail.');}}
async function exportFile(name,strict){const old=downloads.length;run(`downloadReview(${strict})`);assert.equal(downloads.length,old+1,document.getElementById('messages').textContent);const raw=await downloads.at(-1).text();fs.writeFileSync(path.join(fixtureRoot,name),raw);return JSON.parse(raw);}
(async()=>{
assert.equal(catalog.tasks.length,21);assert.equal(document.getElementById('manual-value').textContent,'未评');assert(document.getElementById('main').innerHTML.includes(' disabled'));
ok('21 actual task rubrics loaded; untouched preview remains unassessed');
for(const t of catalog.tasks){run(`taskId=${JSON.stringify(t.id)};track=${JSON.stringify(t.track)};lang='zh';render();`);assert(document.getElementById('main').innerHTML.includes('逐项质量评分'));run("lang='en';render();");assert(document.getElementById('main').innerHTML.includes('Criterion-level quality ratings'));}
ok('All 21 task views render in both languages without runtime errors');
await load('R03');assert.equal(json('scoreInfo().manual'),null);let draft=await exportFile('R03/browser-draft.json',false);assert.deepEqual(draft,fixture('R03'));
ok('Untouched nrb-review-v1 draft round-trip exactly preserves metadata and nulls');
assert(json('check(true)').some(e=>e.includes('Record actual reviewer')));assert(json('check(true)').some(e=>e.includes('level, evidence')));
ok('Checked export requires reviewer, levels, evidence and rationale');
fillQuality('R03');assert.equal(json('scoreInfo().manual'),50);assert.equal(json('scoreInfo().total'),50);assert.equal(json('scoreInfo().failed'),true);assert.deepEqual(json('check(true)'),[]);await exportFile('R03/browser-checked.json',true);
ok('Manual weighted score is 50/100 while core failure remains independent');
edit('criterion',0,'score','');assert.equal(json('scoreInfo().manual'),null);assert.equal(json('records.get("R03").ledger.criteria[0].score'),null);edit('criterion',0,'score','2');
ok('Clearing a score restores null and removes the complete numeric total');
edit('reviewer',0,'type','llm');assert(json('check(true)').some(e=>e.includes('LLM review needs')));assert.equal(document.getElementById('authority-label').textContent,'LLM · provisional');edit('reviewer',0,'model','synthetic-model');edit('reviewer',0,'prompt_hash','synthetic-prompt-fingerprint');assert.deepEqual(json('check(true)'),[]);
ok('LLM authority is provisional and model/prompt identity are mandatory');
await load('C01');assert.equal(json('records.get("C01").auto.auto_points'),0);assert.equal(json('scoreInfo().auto'),null);fillQuality('C01');assert.equal(json('scoreInfo().manual'),15);assert.equal(json('scoreInfo().total'),null);
ok('C manual maximum is 30; unavailable automatic zero is never a known score');
run("records.get('C01').auto.checks.forEach(c=>c.passed=true);records.get('C01').auto.auto_points=70;records.get('C01').auto.auto_scored_max=70;records.get('C01').auto.auto_percent=100");assert.equal(json('scoreInfo().total'),85);run("records.get('C01').auto.comparison_eligible=false");assert.equal(json('scoreInfo().total'),null);
ok('Complete C total uses 70+30; explicit comparison ineligibility suppresses ranking total');
await load('R01');context.bad=fixture('R01');run('bad.criteria[0].weight+=1');assert(json('ledgerErrors(bad)').some(e=>e.includes('Canonical rubric changed')));context.bad=fixture('R01');run('bad.criteria[0].score=false');assert(json('ledgerErrors(bad)').some(e=>e.includes('integer 0..4')));context.bad=fixture('R01');run('bad.criteria[0].score=0.5');assert(json('ledgerErrors(bad)').some(e=>e.includes('integer 0..4')));
ok('Tampered weights, fractional scores and boolean scores rejected');
context.bad=fixture('R01');run('bad.criteria[0].anchors["4"]="altered"');assert(json('ledgerErrors(bad)').some(e=>e.includes('Canonical rubric changed')));context.bad=fixture('R01');run('bad.packet_hash="0".repeat(64)');assert(json('bindingErrors(bad,records.get("R01").auto)').some(e=>e.includes('packet_hash')));
ok('Canonical anchor edits and mismatched automatic-report bindings rejected');
edit('essential',0,'outcome','pass');assert(json('check(true)').some(e=>e.includes('requires actual observation')));
ok('Core pass requires genuine modality observation fields');
edit('criterion',0,'evidence','<img src="https://example.invalid" onerror="window.PWNED=1">');run('render()');assert(document.getElementById('main').innerHTML.includes('&lt;img'));assert(!document.getElementById('main').innerHTML.includes('<img'));assert(run('forbiddenKeys(JSON.parse(\'{"__proto__":{"polluted":true}}\'))'));
ok('Candidate markup is escaped and prototype-pollution keys rejected');
assert(run('invalidNumbers({x:Infinity})'));assert(run('invalidNumbers({x:9007199254740993})'));assert(!run('invalidNumbers({x:0.25})'));
ok('Nonfinite/unsafe JSON numbers cannot be silently reserialized');
await load('X04');assert.equal(run('track'),'optional_video_a');draft=await exportFile('X04/browser-draft.json',false);assert.deepEqual(draft,fixture('X04'));assert.equal(json('records.get("X04").ledger.media_review.scenes.length'),6);assert.equal(json('records.get("X04").ledger.media_review.observations.length'),2);fillQuality('X04');assert(json('check(true)').some(e=>e.includes('requires actual observation')));
ok('Video A stays separate, preserves full blank protocol, and requires output watching even if all core gates fail');
edit('media-scene',0,'timecodes_seconds','9');assert(json('check(false)').some(e=>e.includes('timecodes must be finite')));edit('media-scene',0,'timecodes_seconds','0.1, invalid');assert(json('check(false)').some(e=>e.includes('timecodes must be finite')));edit('media-scene',0,'timecodes_seconds','0.1, 1.2');assert(!json('check(false)').some(e=>e.includes('timecodes must be finite')));
ok('Video timecodes must be finite and inside the fixed scene interval, including drafts');
await load('X05');assert.equal(run('track'),'optional_video_b');assert.equal(json('records.get("X05").ledger.criteria.length'),8);assert.equal(json('records.get("X05").ledger.media_review.observations.length'),3);fillQuality('X05');edit('media-audio',0,'status','missing');edit('essential',3,'outcome','pass');assert(json('check(true)').some(e=>e.includes('Missing soundtrack requires')));edit('essential',3,'outcome','fail');edit('media-audio',0,'evidence','Synthetic test of missing-audio branch only.');
edit('observation',0,'performed',true);edit('observation',0,'evidence','Synthetic test boolean; not an actual observation.');
for(let i=0;i<3;i++){edit('media-observation',i,'performed',i!==1);edit('media-observation',i,'evidence','Synthetic test fixture observation; not real viewing.');}
const intervals=fixture('X05').media_review.scenes.map(s=>s.interval_seconds);for(let i=0;i<6;i++){edit('media-scene',i,'observed',true);edit('media-scene',i,'timecodes_seconds',String((intervals[i][0]+intervals[i][1])/2));edit('media-scene',i,'evidence','Synthetic UI validation scene; no assessed candidate.');}
assert.deepEqual(json('check(true)'),[]);await exportFile('X05/browser-checked.json',true);
ok('Video B reference protocol and missing-audio/fail branch serialize for real CLI validation');
const snapshot=json('records.get("X05").ledger');run("lang='zh';render();lang='en';render()");assert.deepEqual(json('records.get("X05").ledger'),snapshot);
ok('Language switches never mutate canonical rubric or ledger content');
assert(!/fetch\(|XMLHttpRequest|localStorage\.|sessionStorage\.|https?:\/\//.test(script));assert(html.includes("connect-src 'none'"));assert(html.includes('@media print'));
ok('Static inspection: no network/storage calls; CSP and print stylesheet present (browser behavior unverified)');
const result={scope:'Synthetic software QA only. Minimal DOM stub, not actual browser/visual/printing tests.',checks_passed:checks.length,checks,browser_verification:'Blocked: local Chromium socket unavailable; escalation mount setup failed; cloud browser rejects file://. No bypass attempted.'};fs.writeFileSync(path.join(__dirname,'../../../validation/v1.1/scorecard-test-results.json'),JSON.stringify(result,null,2)+'\n');
console.log(`${checks.length} logic checks passed`);
})().catch(error=>{console.error(error);process.exit(1)});
