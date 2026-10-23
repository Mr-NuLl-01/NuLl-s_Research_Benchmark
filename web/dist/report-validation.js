/* Report parsing is an integrity check for local reports, not execution attestation. */
(function (root) {
  'use strict';
  const SHA = /^[0-9a-f]{64}$/;
  const object = x => x !== null && typeof x === 'object' && !Array.isArray(x);
  const finite = x => typeof x === 'number' && Number.isFinite(x);
  function fail(message) { throw new Error(message); }
  function same(actual, expected, label) { if (actual !== expected) fail(label + '不匹配，请使用当前题包和验证器重新评分。'); }
  function close(actual, expected, label) {
    if (expected === null) { if (actual !== null) fail(label + '应为空：存在未执行检查。'); return; }
    if (!finite(actual) || Math.abs(actual - expected) > 1e-8) fail(label + '与逐项检查重算结果不一致。');
  }
  function validateReport(report, release) {
    if (!object(report)) fail('请上传验证器生成的 JSON 对象。');
    const manifest = release && release.grading;
    if (!object(manifest) || !object(manifest.tasks)) fail('当前评分白名单尚未就绪，请稍后刷新。');
    same(report.schema, manifest.schema, '报告格式');
    same(report.benchmark_version, manifest.version, '题库版本');
    same(report.grader_version, manifest.grader_version || manifest.version, '验证器版本');
    if (!SHA.test(report.evaluator_fingerprint || '')) fail('验证器指纹缺失或格式错误。');
    same(report.evaluator_fingerprint, manifest.evaluatorFingerprint, '验证器内容指纹');
    const task = manifest.tasks[report.task_id];
    if (!task) fail('该报告不属于本轮已开放的 8 道 Python 题。');
    if (!Number.isSafeInteger(report.seed)) fail('测试种子必须是整数。');
    const expected = task.seeds && task.seeds[String(report.seed)];
    if (!expected) fail('此测试种子尚未登记。当前支持：' + Object.keys(task.seeds || {}).join('、') + '。');
    same(report.packet_hash, expected.packet_hash || task.packet_hash, '题包指纹');
    same(report.test_manifest_hash, expected.test_manifest_hash, '检查清单指纹');
    if (!SHA.test(report.source_hash || '') && !(report.source_hash === null && report.status === 'unscored')) fail('候选源码指纹缺失或格式错误。');
    same(report.report_origin, 'local_verifier', '报告来源');
    if (!Array.isArray(expected.checks) || !expected.checks.length) fail('站点检查清单不完整。');
    if (!Array.isArray(report.checks) || report.checks.length !== expected.checks.length) fail('检查项数量不匹配；不能省略失败或未执行检查。');
    const supplied = new Map();
    for (const check of report.checks) {
      if (!object(check) || typeof check.id !== 'string' || supplied.has(check.id)) fail('报告包含无效或重复检查项。');
      if (![true, false, null].includes(check.passed)) fail('检查结果只能为 true、false 或 null。');
      if (typeof check.detail !== 'string' || check.detail.length > 30000) fail('检查说明格式不正确。');
      supplied.set(check.id, check);
    }
    let earned = 0, total = 0;
    const checks = expected.checks.map(entry => {
      const check = supplied.get(entry.id);
      if (!check) fail('缺少检查项：' + entry.id + '。');
      if (!finite(entry.weight) || entry.weight <= 0) fail('站点检查权重无效。');
      same(check.weight, entry.weight, '检查 ' + entry.id + ' 的权重');
      same(check.tier, entry.tier, '检查 ' + entry.id + ' 的分组');
      same(check.critical, entry.critical, '检查 ' + entry.id + ' 的关键标记');
      total += entry.weight;
      if (check.passed === true) earned += entry.weight;
      return {id:entry.id, tier:entry.tier, weight:entry.weight, critical:entry.critical, passed:check.passed, detail:check.detail};
    });
    const pending = checks.filter(x => x.passed === null).length;
    const failed = checks.filter(x => x.passed === false).length;
    const score = pending ? null : 100 * earned / total;
    const status = pending ? 'unscored' : failed ? 'failed' : 'passed';
    const critical = checks.filter(x => x.critical);
    const criticalPassed = critical.some(x => x.passed === false) ? false : critical.some(x => x.passed === null) ? null : true;
    same(report.status, status, '评分状态');
    close(report.score, score, '得分');
    close(report.total, score, '总分');
    same(report.critical_passed, criticalPassed, '关键检查结论');
    if (!object(report.execution) || !['docker','trusted','none'].includes(report.execution.backend) || !['executed','failed','unavailable'].includes(report.execution.status)) fail('执行环境或执行状态无效。');
    if (report.execution.status === 'unavailable' && status !== 'unscored') fail('环境不可用的报告不能登记为已评分。');
    if (report.execution.status === 'failed' && (pending !== 0 || failed !== checks.length || score !== 0)) fail('执行进程失败时，本版协议要求全部检查失败且得分为 0。');
    if (report.execution.backend === 'none' && status !== 'unscored') fail('未执行程序的报告不能登记为已评分。');
    if (typeof report.control_only !== 'boolean' || typeof report.comparison_eligible !== 'boolean') fail('缺少报告用途及比较资格标记。');
    if (report.execution.backend === 'trusted' && !report.control_only) fail('trusted 自检报告必须保留控制用途标记。');
    const eligible = report.execution.backend === 'docker' && report.execution.status !== 'unavailable' && !report.control_only && status !== 'unscored';
    if (report.comparison_eligible && !eligible) fail('该执行方式或状态不能进入模型比较。');
    const tiers = {};
    for (const check of checks) {
      const tier = tiers[check.tier] || (tiers[check.tier] = {earned:0, total:0, pending:0});
      tier.total += check.weight;
      if (check.passed) tier.earned += check.weight;
      if (check.passed === null) tier.pending += 1;
    }
    return {taskId:report.task_id, version:manifest.version, seed:report.seed, packetHash:report.packet_hash,
      manifestHash:report.test_manifest_hash, evaluatorFingerprint:report.evaluator_fingerprint,
      sourceHash:report.source_hash, score, status, earned, totalWeight:total, checks, tiers,
      passedCount:checks.length-pending-failed, failedCount:failed, pendingCount:pending,
      criticalPassed, controlOnly:report.control_only, comparisonEligible:eligible && report.comparison_eligible,
      backend:report.execution.backend, executionStatus:report.execution.status};
  }
  const api = {validateReport};
  root.NRBReports = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
