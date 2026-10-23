/* H02 evaluates original answers locally. It does not accept a claimed score. */
(function(root){
'use strict';
const p={a0:.3,a2:.04,r:1.1,b:.2,h:.8,s:.4,t:.6,c:.1};
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const close=(a,b)=>b===null?a===null:typeof a==='number'&&Number.isFinite(a)&&Math.abs(a-b)<=2e-8+2e-6*Math.abs(b);
function solve(M,b){
  const a=M.map((r,i)=>[...r,b[i]]);
  for(let c=0;c<3;c++){
    let j=c;for(let i=c+1;i<3;i++)if(Math.abs(a[i][c])>Math.abs(a[j][c]))j=i;
    [a[c],a[j]]=[a[j],a[c]];
    if(Math.abs(a[c][c])<1e-15)throw Error('评分器矩阵退化');
    for(let i=c+1;i<3;i++){const f=a[i][c]/a[c][c];for(let k=c;k<=3;k++)a[i][k]-=f*a[c][k];}
  }
  const x=[0,0,0];for(let i=2;i>=0;i--){let v=a[i][3];for(let j=i+1;j<3;j++)v-=a[i][j]*x[j];x[i]=v/a[i][i];}return x;
}
function values(k,q=p){
  const M=[[q.a0+q.a2*k*k+k,-k,0],[-q.r,q.r+q.b+q.h,-q.h],[0,-q.s,q.s+q.t+q.c]];
  const y=solve(M,[0,0,q.t]),u=solve(M,y),v=solve(M,u.map(x=>2*x)),a=solve(M,[1,1,1]);
  return {yield:y[0],tau_abs:a[0],tau_T:k?u[0]/y[0]:null,var_T:k?v[0]/y[0]-(u[0]/y[0])**2:null};
}
const kstar=Math.sqrt(p.a0/p.a2);
const scenarios=[['zero',0,p],['slow',.25,p],['optimal',kstar,p],['fast',12,p],['no_return',kstar,{...p,r:0,s:0}]];
function same(a,b){
  if(Array.isArray(b))return Array.isArray(a)&&a.length===b.length&&a.every((x,i)=>same(x,b[i]));
  if(object(b))return object(a)&&Object.keys(a).length===Object.keys(b).length&&Object.keys(b).every(k=>same(a[k],b[k]));
  return close(a,b);
}
function check(name,a){
  if(!object(a)||a.task_id!=='H02')return [false,'需要包含 task_id: H02 的原始答案对象。'];
  const keys={target_yields:'yield',absorption_times:'tau_abs',conditional_times:'tau_T',conditional_variances:'var_T'};
  if(keys[name]){
    const rows=a.cases,key=keys[name];
    if(!Array.isArray(rows)||rows.length!==5||!rows.every(object))return [false,'需要五个情形的数据。'];
    const ids=new Set(rows.map(r=>r.id));if(ids.size!==5||!scenarios.every(([id])=>ids.has(id)))return [false,'情形 id 缺失或重复。'];
    for(const [id,k,q] of scenarios)if(!close(rows.find(r=>r.id===id)[key],values(k,q)[key]))return [false,`${id} / ${key} 不符合数值或 null 约定。`];
    return [true,''];
  }
  if(name==='global_optimum_certificate'){
    const C=p.s+p.t+p.c,minor=(p.r+p.b+p.h)*C-p.h*p.s,N=p.h*p.t,D=[p.a0*minor,minor-p.r*C,p.a2*minor];
    const expected={k:kstar,yield:values(kstar).yield,derivative_numerator:[N*D[0],0,-N*D[2]],positive_stationary_points:1,boundary_yields:[0,0]};
    const ok=Number.isSafeInteger(a.optimum?.positive_stationary_points)&&same(a.yield_coefficients,{N1:N,D})&&same(a.optimum,expected);
    return [ok,ok?'':'产额有理式、导数证书或全局最优结果不一致。'];
  }
  if(name==='valid_counterexample'){
    const c=a.counterexample,k=c?.k;
    if(typeof k!=='number'||!Number.isFinite(k)||k<1e-6||k>100)return [false,'反例 k 必须在 [1e−6,100] 内。'];
    const v=values(k),o=values(kstar),ok=close(c.yield,v.yield)&&close(c.tau_T,v.tau_T)&&v.yield<=.99*o.yield&&v.tau_T<=.99*o.tau_T;
    return [ok,ok?'':'反例需准确计算，且产额和条件时间均比产额最优点低至少 1%。'];
  }
  return [false,'未知检查项。'];
}
function evaluate(answer,release,seed=17){
  if(!Number.isSafeInteger(seed)||seed<0||seed>=2**32)throw Error('测试种子必须是范围内的整数。');
  const entry=release.grading?.tasks?.H02?.seeds?.[String(seed)];if(!entry)throw Error('未登记的 H02 版本或种子。');
  const checks=entry.checks.map(c=>{const [passed,detail]=check(c.id,answer);return {...c,passed,detail};});
  const total=checks.reduce((s,c)=>s+c.weight,0),earned=checks.filter(c=>c.passed).reduce((s,c)=>s+c.weight,0),failed=checks.filter(c=>!c.passed).length;
  return {taskId:'H02',version:release.version,seed,packetHash:entry.packet_hash,manifestHash:entry.test_manifest_hash,
    evaluatorFingerprint:release.grading.evaluatorFingerprint,sourceHash:'answer-json:'+JSON.stringify(answer),
    score:Math.round(1e6*100*earned/total)/1e6,status:failed?'failed':'passed',earned,totalWeight:total,checks,
    passedCount:checks.length-failed,failedCount:failed,pendingCount:0,criticalPassed:!failed,
    controlOnly:false,comparisonEligible:true,backend:'answer',executionStatus:'executed',origin:'browser-answer'};
}
function report(answer,release){return {schema:'nrb-answer-v2',benchmark_version:release.version,task_id:'H02',seed:17,answer_payload:answer};}
root.NRBH02={evaluate,report,values};if(typeof module!=='undefined'&&module.exports)module.exports=root.NRBH02;
})(typeof globalThis!=='undefined'?globalThis:this);
