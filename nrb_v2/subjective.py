"""Evidence-based V2 manual protocols; no automatic quality or model-judge claim.

The evaluator owns this module and subjective_rubrics.json. Candidate bundles are
built only from candidate_inputs(), never by copying evaluator directories.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path, PurePosixPath

from . import __version__

SUBJECTIVE_IDS = ('R01', 'R02', 'R03', 'R04', 'R05', 'R06', 'H01')
SCHEMA = 'nrb-v2-manual-review'
_REVIEW_STATUSES = {'pass', 'fail', 'unassessed'}
_OBSERVATION_STATUSES = {'observed', 'missing', 'unassessed'}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def _valid_relative(value):
    if not isinstance(value, str) or not value or '\\' in value:
        return False
    p = PurePosixPath(value)
    return not p.is_absolute() and '..' not in p.parts and '.' != value


def _validate_spec(spec):
    dimensions = spec['rubric']
    if not dimensions or len({d['id'] for d in dimensions}) != len(dimensions):
        raise ValueError('Empty or duplicate rubric dimensions')
    if any(type(d['weight']) is not int or d['weight'] <= 0 for d in dimensions):
        raise ValueError('Rubric weights must be positive integers')
    if sum(d['weight'] for d in dimensions) != 100:
        raise ValueError('Manual rubric weights must total 100')
    if any(set(d['anchors']) != {'0', '2', '4'} or
           not all(isinstance(a, str) and a.strip() for a in d['anchors'].values())
           for d in dimensions):
        raise ValueError('Each dimension needs nonempty 0/2/4 anchors')
    for key in ('requirements', 'required_observations'):
        rows = spec[key]
        if not rows or len({x['id'] for x in rows}) != len(rows):
            raise ValueError('Empty or duplicate ' + key)
    requirement_ids = {r['id'] for r in spec['requirements']}
    if len({c['requirement_id'] for c in spec['hard_caps']}) != len(spec['hard_caps']):
        raise ValueError('Duplicate hard-cap requirement')
    for c in spec['hard_caps']:
        if c['requirement_id'] not in requirement_ids or type(c['max_score']) is not int or not 0 <= c['max_score'] <= 100:
            raise ValueError('Invalid hard cap')
    destinations = []
    for f in spec['input_files']:
        if not _valid_relative(f['source']) or not _valid_relative(f['path']):
            raise ValueError('Unsafe candidate input path')
        destinations.append(f['path'])
        if any(part in {'evaluator', 'demo_project', 'nrb_v1', 'nrb_v2'} for part in PurePosixPath(f['source']).parts):
            raise ValueError('Evaluator/implementation source cannot enter a candidate bundle')
    if len(destinations) != len(set(destinations)):
        raise ValueError('Duplicate candidate destination')
    if spec['id'] == 'R06':
        references = [f for f in spec['input_files'] if PurePosixPath(f['path']).name == 'reference.mp4']
        if spec['mode'] == 'A' and references:
            raise ValueError('R06-A may not receive the reference')
        if spec['mode'] == 'B' and len(references) != 1:
            raise ValueError('R06-B requires exactly one reference')


@lru_cache(maxsize=1)
def _definitions():
    data = json.loads(Path(__file__).with_name('subjective_rubrics.json').read_text(encoding='utf-8'))
    if data.get('schema') != 'nrb-v2-manual-rubrics' or tuple(data['tasks']) != SUBJECTIVE_IDS:
        raise ValueError('Unexpected subjective task definitions')
    for task_id, spec in data['tasks'].items():
        if task_id == 'R06':
            if set(spec['mode_specs']) != {'A', 'B'}:
                raise ValueError('R06 requires exactly A and B modes')
            for mode in ('A', 'B'):
                _validate_spec(spec['mode_specs'][mode])
        else:
            _validate_spec(spec)
    return data['tasks']


def get_task(task_id, mode=None):
    """Return independent task metadata. R06 without mode returns both mode_specs.

    No mode is silently selected for R06. Use rubric_spec/candidate_inputs with
    an explicit A or B for an actual run.
    """
    if task_id not in SUBJECTIVE_IDS:
        raise ValueError('Unknown subjective task: ' + str(task_id))
    spec = deepcopy(_definitions()[task_id])
    if task_id == 'R06':
        if mode is not None:
            if mode not in ('A', 'B'):
                raise ValueError('R06 mode must be A or B')
            spec = deepcopy(spec['mode_specs'][mode])
    elif mode is not None:
        raise ValueError(task_id + ' has no selectable mode')
    spec['benchmark_version'] = __version__
    return spec


def tasks():
    """The seven manually rated tasks, with R06 counted only once."""
    return [get_task(task_id) for task_id in SUBJECTIVE_IDS]


def rubric_spec(task_id, mode=None):
    """Return the exact evaluator protocol used for hashing and score validation."""
    spec = get_task(task_id, mode)
    if task_id == 'R06' and mode is None:
        raise ValueError('Declare R06 mode A or B before constructing a rubric')
    keys = ('id', 'mode', 'benchmark_version', 'protocol_version', 'rubric', 'requirements',
            'hard_caps', 'required_observations', 'required_artifacts', 'rating_scale', 'reviewer_checks')
    result = {k: deepcopy(spec[k]) for k in keys}
    result['schema'] = 'nrb-v2-manual-rubric'
    return result


def rubric_hash(task_id, mode=None):
    return hashlib.sha256(_canonical(rubric_spec(task_id, mode))).hexdigest()


def candidate_inputs(task_id, mode=None):
    """Allowlisted {source: repo-relative, path: packet-relative} mappings.

    Caller resolves source from the confirmed repository/install data root and
    copies bytes without adding evaluator, author solution or unrelated inputs.
    """
    spec = get_task(task_id, mode)
    if task_id == 'R06' and mode is None:
        raise ValueError('Declare R06 mode A or B before exposing candidate inputs')
    return deepcopy(spec['input_files'])


def blank_review(task_id, mode=None, *, reviewer_id='', reviewer_kind='human',
                 submission_id='', submission_sha256=None):
    if reviewer_kind not in ('human', 'llm_provisional'):
        raise ValueError('reviewer_kind must be human or llm_provisional')
    spec = rubric_spec(task_id, mode)
    # Packets import candidate_inputs; keep this dependency lazy to avoid a
    # module cycle. The review binds the candidate's prompt and media bytes in
    # addition to the evaluator's scoring contract.
    from .packets import candidate, input_manifest
    packet_digest = candidate(task_id, 17)['packet_hash']
    input_digest = input_manifest(task_id, 17, mode)['sha256']
    return {
        'schema': SCHEMA, 'benchmark_version': __version__, 'task_id': task_id, 'mode': mode,
        'rubric_hash': rubric_hash(task_id, mode),
        'packet_hash': packet_digest, 'input_manifest_hash': input_digest,
        'submission_id': submission_id, 'submission_sha256': submission_sha256,
        'reviewer': {'id': reviewer_id, 'kind': reviewer_kind},
        'ratings': [{'id': d['id'], 'level': None, 'evidence': ''} for d in spec['rubric']],
        'requirements': [{'id': r['id'], 'status': 'unassessed', 'evidence': ''} for r in spec['requirements']],
        'observations': [{'id': o['id'], 'status': 'unassessed', 'evidence': '',
                          'artifact_sha256': None} for o in spec['required_observations']],
        'notes': '',
    }


def _indexed(rows, expected_ids, label):
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(label + ' must be a list of objects')
    ids = [row.get('id') for row in rows]
    if any(not isinstance(i, str) for i in ids) or len(ids) != len(set(ids)) or set(ids) != set(expected_ids):
        raise ValueError(label + ' IDs must exactly match the rubric; missing/duplicate/unknown IDs are not accepted')
    return {row['id']: row for row in rows}


def _evidence(row, label):
    evidence = row.get('evidence')
    if not isinstance(evidence, str):
        raise ValueError(label + ' evidence must be a string')
    if not evidence.strip():
        raise ValueError(label + ' requires specific observed evidence')


def _check_hash(value, label):
    if value is None:
        return
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError(label + ' must be a lowercase SHA-256 digest or null')


def score_review(review):
    """Recompute an anchored manual review; never trusts a supplied total.

    Any unassessed rating, requirement or required observation makes score null.
    Verified absence (observation status 'missing') can support a genuine zero
    or cap. Environment inability remains 'unassessed', not 'missing'.
    """
    if not isinstance(review, dict) or review.get('schema') != SCHEMA:
        raise ValueError('Invalid manual review schema')
    if review.get('benchmark_version') != __version__:
        raise ValueError('Manual review benchmark version mismatch')
    tid, mode = review.get('task_id'), review.get('mode')
    spec = rubric_spec(tid, mode)
    digest = rubric_hash(tid, mode)
    if review.get('rubric_hash') != digest:
        raise ValueError('Manual review rubric fingerprint mismatch')
    from .packets import candidate, input_manifest
    packet_digest = candidate(tid, 17)['packet_hash']
    input_digest = input_manifest(tid, 17, mode)['sha256']
    if review.get('packet_hash') != packet_digest:
        raise ValueError('Manual review candidate packet fingerprint mismatch')
    if review.get('input_manifest_hash') != input_digest:
        raise ValueError('Manual review input manifest fingerprint mismatch')
    ratings = _indexed(review.get('ratings'), [d['id'] for d in spec['rubric']], 'ratings')
    requirements = _indexed(review.get('requirements'), [r['id'] for r in spec['requirements']], 'requirements')
    observations = _indexed(review.get('observations'), [o['id'] for o in spec['required_observations']], 'observations')
    _check_hash(review.get('submission_sha256'), 'submission_sha256')
    missing, dimension_scores = [], []
    partial_earned, rated_weight = 0.0, 0
    for d in spec['rubric']:
        row = ratings[d['id']]
        level = row.get('level')
        if level is None:
            missing.append('rating:' + d['id'])
            earned = None
        else:
            # JSON has one numeric type: 4 and 4.0 denote the same integer
            # value. Match Number.isInteger in the browser without accepting
            # bools, strings, nonfinite values or fractional ratings.
            if type(level) not in (int, float) or not 0 <= level <= 4 or level != int(level):
                raise ValueError('Rating level must be a finite integer value 0–4 or null; booleans are not levels')
            level = int(level)
            _evidence(row, 'rating ' + d['id'])
            earned = d['weight'] * level / 4
            partial_earned += earned
            rated_weight += d['weight']
        dimension_scores.append({'id': d['id'], 'weight': d['weight'], 'level': level, 'earned': earned})
    for key, row in requirements.items():
        status = row.get('status')
        if not isinstance(status, str) or status not in _REVIEW_STATUSES:
            raise ValueError('Requirement status must be pass/fail/unassessed')
        if status == 'unassessed':
            missing.append('requirement:' + key)
        else:
            _evidence(row, 'requirement ' + key)
    for key, row in observations.items():
        status = row.get('status')
        if not isinstance(status, str) or status not in _OBSERVATION_STATUSES:
            raise ValueError('Observation status must be observed/missing/unassessed')
        _check_hash(row.get('artifact_sha256'), 'observation artifact_sha256')
        if status == 'unassessed':
            missing.append('observation:' + key)
        else:
            _evidence(row, 'observation ' + key)
    reviewer = review.get('reviewer')
    if not isinstance(reviewer, dict) or reviewer.get('kind') not in ('human', 'llm_provisional'):
        raise ValueError('A human or explicitly provisional LLM reviewer must be identified')
    if not isinstance(reviewer.get('id'), str) or not reviewer['id'].strip():
        missing.append('reviewer:id')
    if not isinstance(review.get('submission_id'), str) or not review['submission_id'].strip():
        missing.append('submission_id')
    applied = [{**c, 'evidence': requirements[c['requirement_id']]['evidence']}
               for c in spec['hard_caps'] if requirements[c['requirement_id']]['status'] == 'fail']
    complete = not missing
    raw = partial_earned if complete else None
    score = min([raw] + [c['max_score'] for c in applied]) if complete else None
    states = [r['status'] for r in requirements.values()]
    gate = False if 'fail' in states else (None if 'unassessed' in states else True)
    protocol_status = requirements.get('mode_integrity', {}).get('status', 'pass')
    protocol_eligible = None if protocol_status == 'unassessed' else protocol_status == 'pass'
    return {
        'task_id': tid, 'mode': mode, 'benchmark_version': __version__, 'rubric_hash': digest,
        'packet_hash': packet_digest, 'input_manifest_hash': input_digest,
        'protocol_eligible': protocol_eligible,
        'status': 'reviewed' if complete else 'review_incomplete', 'score': score, 'raw_score': raw,
        'partial_earned': partial_earned, 'rated_weight': rated_weight, 'max_score': 100,
        'dimension_scores': dimension_scores, 'applied_caps': applied,
        'requirements_passed': gate, 'missing_items': missing,
        'reviewer_kind': reviewer['kind'], 'completion_authority': reviewer['kind'],
        'comparison_key': {'task_id': tid, 'mode': mode, 'benchmark_version': __version__,
                           'rubric_hash': digest, 'packet_hash': packet_digest,
                           'input_manifest_hash': input_digest,
                           'reviewer_kind': reviewer['kind'], 'reviewer_id': reviewer.get('id')},
        'provenance': {'submission_id': review.get('submission_id'),
                       'submission_sha256': review.get('submission_sha256'),
                       'identity_hash_present': review.get('submission_sha256') is not None,
                       'cryptographic_authentication': False},
    }
