/* Evidence-based manual scoring. Python/JavaScript parity is checked in tests_v2. */
(function (root) {
'use strict';
const SUBJECTIVE_IDS = ['R01', 'R02', 'R03', 'R04', 'R05', 'R06', 'H01'];
const obj = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const sha = /^[0-9a-f]{64}$/;
// Match Python str.strip() for evidence and identities, including U+0085.
const nonWhitespace = /[^\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/u;
const nonemptyText = value => typeof value === 'string' && nonWhitespace.test(value);
const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
const fail = message => { throw Error(message); };

function specFor(task, mode, release) {
  if (typeof task !== 'string' || !SUBJECTIVE_IDS.includes(task)) fail('未知的主观题。');
  if (task === 'R06') {
    if (mode !== 'A' && mode !== 'B') fail('请先选择视频 A 或 B 模式。');
  } else if (mode !== null && mode !== undefined) fail('本题没有可选模式。');
  const key = task + (mode == null ? '' : '-' + mode);
  if (!obj(release) || !obj(release.rubrics) || !own(release.rubrics, key)) fail('当前量表未就绪。');
  const entry = release.rubrics[key];
  if (!obj(entry) || !obj(entry.spec) || entry.spec.id !== task ||
      entry.spec.mode !== (mode ?? null) || entry.spec.benchmark_version !== release.version ||
      typeof entry.hash !== 'string' || !sha.test(entry.hash)) fail('当前量表元数据不一致。');
  return entry;
}

function bindings(taskId, entry, release) {
  const matches = Array.isArray(release.tasks) ? release.tasks.filter(t => obj(t) && t.id === taskId) : [];
  if (matches.length !== 1 || typeof matches[0].packetHash !== 'string' || !sha.test(matches[0].packetHash) ||
      typeof entry.input_manifest_hash !== 'string' || !sha.test(entry.input_manifest_hash)) {
    fail('当前题面或输入材料指纹未就绪。');
  }
  return {packet_hash: matches[0].packetHash, input_manifest_hash: entry.input_manifest_hash};
}

function blank(task, mode, release) {
  const entry = specFor(task, mode, release), spec = entry.spec;
  return {
    schema: 'nrb-v2-manual-review', benchmark_version: release.version, task_id: task, mode: mode ?? null,
    rubric_hash: entry.hash, ...bindings(task, entry, release),
    reviewer: {id: '', kind: 'human'}, submission_id: '', submission_sha256: null,
    ratings: spec.rubric.map(d => ({id: d.id, level: null, evidence: ''})),
    requirements: spec.requirements.map(d => ({id: d.id, status: 'unassessed', evidence: ''})),
    observations: spec.required_observations.map(d => ({id: d.id, status: 'unassessed', evidence: '', artifact_sha256: null})),
    notes: ''
  };
}

function index(rows, ids, label) {
  if (!Array.isArray(rows) || !rows.every(obj) || rows.length !== ids.length) fail(label + '项目不完整。');
  const result = new Map();
  for (const row of rows) {
    if (typeof row.id !== 'string' || result.has(row.id) || !ids.includes(row.id)) fail(label + '项目缺失、重复或未知。');
    result.set(row.id, row);
  }
  return result;
}
function evidence(row, label) {
  if (!nonemptyText(row.evidence)) fail(label + '需要具体观察证据。');
}
function checkHash(value, label) {
  if (value !== null && value !== undefined && (typeof value !== 'string' || !sha.test(value))) {
    fail(label + '必须为小写 SHA-256 或 null。');
  }
}

function score(review, release) {
  if (!obj(review) || review.schema !== 'nrb-v2-manual-review') fail('请选择完整量表记录。');
  if (!obj(release) || review.benchmark_version !== release.version) fail('量表版本不匹配。');
  const entry = specFor(review.task_id, review.mode, release), spec = entry.spec, digest = entry.hash;
  if (review.rubric_hash !== digest) fail('量表指纹不匹配。');
  const bound = bindings(review.task_id, entry, release);
  if (review.packet_hash !== bound.packet_hash) fail('题面指纹不匹配，须使用本轮评阅表。');
  if (review.input_manifest_hash !== bound.input_manifest_hash) fail('输入材料指纹不匹配，须使用本题及模式的评阅表。');
  const ratings = index(review.ratings, spec.rubric.map(d => d.id), '评分维度');
  const requirements = index(review.requirements, spec.requirements.map(d => d.id), '必要条件');
  const observations = index(review.observations, spec.required_observations.map(d => d.id), '观察清单');
  checkHash(review.submission_sha256, '提交物标识');
  const missing = [], dimensions = [];
  let earned = 0, rated = 0;
  for (const dimension of spec.rubric) {
    const row = ratings.get(dimension.id), level = row.level ?? null;
    let value = null;
    if (level === null) missing.push('rating:' + dimension.id);
    else {
      if (!Number.isInteger(level) || level < 0 || level > 4) fail('评级必须为 0–4 的整数或未评。');
      evidence(row, dimension.name);
      value = dimension.weight * level / 4;
      earned += value; rated += dimension.weight;
    }
    dimensions.push({id: dimension.id, weight: dimension.weight, level, earned: value});
  }
  for (const [id, row] of requirements) {
    if (!['pass', 'fail', 'unassessed'].includes(row.status)) fail('必要条件状态无效。');
    if (row.status === 'unassessed') missing.push('requirement:' + id);
    else evidence(row, id);
  }
  for (const [id, row] of observations) {
    if (!['observed', 'missing', 'unassessed'].includes(row.status)) fail('观察状态无效。');
    checkHash(row.artifact_sha256, id);
    if (row.status === 'unassessed') missing.push('observation:' + id);
    else evidence(row, id);
  }
  if (!obj(review.reviewer) || !['human', 'llm_provisional'].includes(review.reviewer.kind)) {
    fail('须标明人工评阅或 LLM 暂评。');
  }
  if (!nonemptyText(review.reviewer.id)) missing.push('reviewer:id');
  if (!nonemptyText(review.submission_id)) missing.push('submission_id');
  const applied = spec.hard_caps.filter(cap => requirements.get(cap.requirement_id).status === 'fail')
    .map(cap => ({...cap, evidence: requirements.get(cap.requirement_id).evidence}));
  const complete = missing.length === 0, raw = complete ? earned : null;
  const total = complete ? Math.min(raw, ...applied.map(cap => cap.max_score)) : null;
  const states = [...requirements.values()].map(row => row.status);
  const gate = states.includes('fail') ? false : states.includes('unassessed') ? null : true;
  const protocolStatus = requirements.get('mode_integrity')?.status ?? 'pass';
  const protocolEligible = protocolStatus === 'unassessed' ? null : protocolStatus === 'pass';
  const mode = review.mode ?? null, kind = review.reviewer.kind;
  return {
    task_id: review.task_id, mode, benchmark_version: release.version, rubric_hash: digest, ...bound,
    protocol_eligible: protocolEligible, status: complete ? 'reviewed' : 'review_incomplete',
    score: total, raw_score: raw, partial_earned: earned, rated_weight: rated, max_score: 100,
    dimension_scores: dimensions, applied_caps: applied, requirements_passed: gate, missing_items: missing,
    reviewer_kind: kind, completion_authority: kind,
    comparison_key: {task_id: review.task_id, mode, benchmark_version: release.version,
      rubric_hash: digest, ...bound, reviewer_kind: kind, reviewer_id: review.reviewer.id ?? null},
    provenance: {submission_id: review.submission_id ?? null, submission_sha256: review.submission_sha256 ?? null,
      identity_hash_present: review.submission_sha256 != null, cryptographic_authentication: false}
  };
}

function validate(review, release) {
  const result = score(review, release), entry = specFor(review.task_id, review.mode, release);
  return {
    taskId: review.task_id, version: release.version, seed: 17, kind: 'manual', mode: result.mode,
    packetHash: result.packet_hash, inputManifestHash: result.input_manifest_hash,
    manifestHash: entry.hash, evaluatorFingerprint: release.grading.evaluatorFingerprint,
    sourceHash: review.submission_sha256 ?? 'review-json:' + JSON.stringify(review),
    score: result.score, status: result.score === null ? 'unscored' : 'reviewed',
    checks: [], passedCount: 0, failedCount: 0, pendingCount: result.missing_items.length,
    criticalPassed: result.requirements_passed, protocolEligible: result.protocol_eligible,
    controlOnly: false,
    comparisonEligible: result.score !== null && result.reviewer_kind === 'human' && result.protocol_eligible === true,
    backend: 'manual', executionStatus: result.status,
    reviewerId: review.reviewer.id ?? null, reviewerKind: result.reviewer_kind,
    completionAuthority: result.completion_authority, comparisonKey: result.comparison_key,
    provenance: result.provenance, review: result, rawReview: review, rubric: entry.spec
  };
}
root.NRBSubjective = {blank, score, validate, specFor};
if (typeof module !== 'undefined' && module.exports) module.exports = root.NRBSubjective;
})(typeof globalThis !== 'undefined' ? globalThis : this);
