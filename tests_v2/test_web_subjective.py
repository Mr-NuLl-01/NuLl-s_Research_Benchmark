"""Run the shipped browser scorer against the Python protocol, without model results.

Fixtures are constructed from the real release contracts and candidate input
hashes. Node executes the same manual-grader.js served by the site; expected
scores come from Python, not a second hand-written test calculator.
"""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from nrb_v2 import __version__
from nrb_v2.packets import candidate, input_manifest
from nrb_v2.subjective import SUBJECTIVE_IDS, blank_review, rubric_hash, rubric_spec, score_review
from tests_v2.test_subjective import filled_control

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
MODES = [(tid, mode) for tid in SUBJECTIVE_IDS for mode in (('A', 'B') if tid == 'R06' else (None,))]
BRIDGE = r"""
const fs = require('node:fs');
const api = require('./web/dist/manual-grader.js');
const {release, calls} = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = calls.map(call => {
  try {
    const result = call.op === 'blank' ? api.blank(call.task_id, call.mode, release) :
      call.op === 'validate' ? api.validate(call.review, release) : api.score(call.review, release);
    return {ok: true, result};
  } catch (error) { return {ok: false, error: String(error.message)}; }
});
process.stdout.write(JSON.stringify(results));
"""


@unittest.skipUnless(NODE, 'Node.js is required to execute the shipped JavaScript scorer')
class BrowserSubjectiveParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = {
            'version': __version__,
            'tasks': [{'id': tid, 'packetHash': candidate(tid, 17)['packet_hash']} for tid in SUBJECTIVE_IDS],
            'rubrics': {tid + ('-' + mode if mode else ''): {
                'spec': rubric_spec(tid, mode), 'hash': rubric_hash(tid, mode),
                'input_manifest_hash': input_manifest(tid, 17, mode)['sha256'],
            } for tid, mode in MODES},
            # Not a model provenance claim. The scorer adapter requires a release identity.
            'grading': {'evaluatorFingerprint': 'f' * 64},
        }

    def browser(self, calls, release=None):
        result = subprocess.run(
            [NODE, '-e', BRIDGE], input=json.dumps({'release': release or self.release, 'calls': calls},
                                                 ensure_ascii=False, allow_nan=False),
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        decoded = json.loads(result.stdout)
        self.assertEqual(len(decoded), len(calls))
        return decoded

    def assert_scores_equal(self, cases):
        replies = self.browser([{'op': 'score', 'review': review} for _, review in cases])
        for (label, review), reply in zip(cases, replies):
            with self.subTest(case=label):
                self.assertTrue(reply['ok'], reply)
                self.assertEqual(reply['result'], score_review(review))

    def test_all_mode_specific_blanks_bind_same_prompt_inputs_and_rubric(self):
        results = self.browser([{'op': 'blank', 'task_id': tid, 'mode': mode} for tid, mode in MODES])
        for (tid, mode), result in zip(MODES, results):
            with self.subTest(task=tid, mode=mode):
                self.assertTrue(result['ok'], result)
                self.assertEqual(result['result'], blank_review(tid, mode))
        self.assertNotEqual(blank_review('R06', 'A')['input_manifest_hash'],
                            blank_review('R06', 'B')['input_manifest_hash'])

    def test_complete_partial_zero_and_each_rating_anchor(self):
        cases = []
        for tid, mode in MODES:
            cases += [(tid + str(mode) + ':blank', blank_review(tid, mode))]
            for level in range(5):
                review = filled_control(tid, mode)
                for row in review['ratings']:
                    row['level'] = level
                cases.append((tid + str(mode) + ':level=' + str(level), review))
            review = filled_control(tid, mode)
            for position, row in enumerate(review['ratings']):
                row['level'] = position % 5
            cases.append((tid + str(mode) + ':mixed', review))
            for dimension in review['ratings']:
                partial = deepcopy(review)
                next(row for row in partial['ratings'] if row['id'] == dimension['id'])['level'] = None
                cases.append((tid + ':unrated:' + dimension['id'], partial))
            for numeric_value in (-0.0, 0.0, 1.0, 2.0, 3.0, 4.0):
                review = filled_control(tid, mode)
                review['ratings'][0]['level'] = numeric_value
                cases.append((tid + str(mode) + ':json-integer-value=' + str(numeric_value), review))
        self.assert_scores_equal(cases)

    def test_every_requirement_cap_and_unknown_observation(self):
        cases = []
        for tid, mode in MODES:
            full = filled_control(tid, mode)
            for section, values in [('requirements', ('fail', 'unassessed')), ('observations', ('missing', 'unassessed'))]:
                for row in full[section]:
                    for status in values:
                        review = deepcopy(full)
                        next(r for r in review[section] if r['id'] == row['id'])['status'] = status
                        cases.append((tid + str(mode) + ':' + row['id'] + ':' + status, review))
            multiple = deepcopy(full)
            for row in multiple['requirements']:
                row['status'] = 'fail'
            cases.append((tid + str(mode) + ':minimum-cap', multiple))
        self.assert_scores_equal(cases)

    def test_authority_identity_order_and_claimed_totals_are_recomputed(self):
        cases = []
        for tid, mode in MODES:
            for kind in ('human', 'llm_provisional'):
                review = filled_control(tid, mode, kind)
                review.update(score=-999, total=10000, protocol_eligible=True,
                              completion_authority='automatic', comparisonEligible=True)
                review['ratings'].reverse(); review['requirements'].reverse(); review['observations'].reverse()
                review['submission_sha256'] = '0' * 64
                review['observations'][0]['artifact_sha256'] = 'a' * 64
                cases.append((tid + str(mode) + ':authority:' + kind, review))
        for value in ('', ' \n\t\u0085', 0, False, None, [], {}):
            for field in ('reviewer_id', 'submission_id'):
                review = filled_control()
                if field == 'reviewer_id':
                    review['reviewer']['id'] = value
                else:
                    review['submission_id'] = value
                cases.append((field + ':' + repr(value), review))
        for field in ('submission_id', 'submission_sha256'):
            review = filled_control(); review.pop(field)
            cases.append(('omitted:' + field, review))
        review = filled_control(); review['reviewer'].pop('id')
        cases.append(('omitted:reviewer.id', review))
        review = filled_control(); review['ratings'][0].pop('level')
        cases.append(('omitted:rating.level', review))
        self.assert_scores_equal(cases)

    def test_malformed_reviews_and_unbound_old_records_are_rejected_by_both(self):
        cases = []
        def add(label, mutate, tid='R01', mode=None):
            review = filled_control(tid, mode); mutate(review); cases.append((label, review))
        for field in ('packet_hash', 'input_manifest_hash', 'rubric_hash', 'benchmark_version'):
            add('missing:' + field, lambda r, f=field: r.pop(f))
            for value in (None, False, 0, [], {}, '0' * 64):
                add('invalid:' + field + ':' + repr(value), lambda r, f=field, v=value: r.update({f: v}))
        for value in (True, False, '4', 2.5, -1, 5, 10**1000, [], {}):
            add('level:' + repr(value), lambda r, v=value: r['ratings'][0].update(level=v))
        for value in ('', ' \n\t', '\u0085', None, False, [], {}):
            add('evidence:' + repr(value), lambda r, v=value: r['ratings'][0].update(evidence=v))
        for section in ('ratings', 'requirements', 'observations'):
            add(section + ':missing-row', lambda r, s=section: r[s].pop())
            add(section + ':duplicate-row', lambda r, s=section: r[s].append(deepcopy(r[s][0])))
            add(section + ':unknown-id', lambda r, s=section: r[s][0].update(id='unknown'))
            add(section + ':nonobject-row', lambda r, s=section: r[s].__setitem__(0, []))
            add(section + ':bad-id-type', lambda r, s=section: r[s][0].update(id={}))
        for section in ('requirements', 'observations'):
            for value in ('', None, True, 1, [], {}):
                add(section + ':status:' + repr(value), lambda r, s=section, v=value: r[s][0].update(status=v))
            add(section + ':assessed-without-evidence', lambda r, s=section: r[s][0].update(evidence=''))
        for value in ('', 'a' * 63, 'A' * 64, 5, {}, []):
            add('submission-hash:' + repr(value), lambda r, v=value: r.update(submission_sha256=v))
            add('artifact-hash:' + repr(value), lambda r, v=value: r['observations'][0].update(artifact_sha256=v))
        for value in ('', 'human ', 'automatic', None, True, []):
            add('reviewer-kind:' + repr(value), lambda r, v=value: r['reviewer'].update(kind=v))
        for value in ('A', '', False, 0, [], {}):
            add('nonvideo-mode:' + repr(value), lambda r, v=value: r.update(mode=v))
        for value in (None, '', False, 0, 'C', [], {}):
            add('video-mode:' + repr(value), lambda r, v=value: r.update(mode=v), 'R06', 'A')
        add('cross-mode-hash', lambda r: r.update(input_manifest_hash=blank_review('R06', 'B')['input_manifest_hash']), 'R06', 'A')
        replies = self.browser([{'op': 'score', 'review': review} for _, review in cases])
        for (label, review), reply in zip(cases, replies):
            with self.subTest(case=label):
                with self.assertRaises(ValueError):
                    score_review(review)
                self.assertFalse(reply['ok'], reply)

    def test_comparability_distinguishes_absence_protocol_breach_and_provisional(self):
        human = filled_control('R06', 'A')
        provisional = filled_control('R06', 'A', 'llm_provisional')
        breach = deepcopy(human)
        next(row for row in breach['requirements'] if row['id'] == 'mode_integrity')['status'] = 'fail'
        unknown = deepcopy(human)
        next(row for row in unknown['requirements'] if row['id'] == 'mode_integrity')['status'] = 'unassessed'
        absent = deepcopy(human)
        next(row for row in absent['requirements'] if row['id'] == 'actual_video')['status'] = 'fail'
        next(row for row in absent['observations'] if row['id'] == 'candidate_video')['status'] = 'missing'
        unobserved = deepcopy(absent)
        next(row for row in unobserved['observations'] if row['id'] == 'candidate_video')['status'] = 'unassessed'
        cases = [('human', human, True, 100), ('provisional', provisional, False, 100),
                 ('breach', breach, False, 0), ('protocol-unknown', unknown, False, None),
                 ('confirmed-absent', absent, True, 0), ('cannot-observe', unobserved, False, None)]
        results = self.browser([{'op': 'validate', 'review': r} for _, r, _, _ in cases])
        for (label, review, comparable, total), result in zip(cases, results):
            with self.subTest(case=label):
                self.assertTrue(result['ok'], result)
                got = result['result']; expected = score_review(review)
                self.assertEqual(got['review'], expected)
                self.assertEqual(got['score'], total)
                self.assertIs(got['comparisonEligible'], comparable)
                self.assertEqual(got['executionStatus'], expected['status'])
                self.assertEqual(got['pendingCount'], len(expected['missing_items']))
                self.assertEqual(got['protocolEligible'], expected['protocol_eligible'])
                self.assertEqual(got['completionAuthority'], expected['completion_authority'])
                self.assertEqual(got['comparisonKey'], expected['comparison_key'])
                self.assertEqual(got['provenance'], expected['provenance'])
                self.assertFalse(got['provenance']['cryptographic_authentication'])
                self.assertEqual(got['packetHash'], review['packet_hash'])
                self.assertEqual(got['inputManifestHash'], review['input_manifest_hash'])

    def test_mode_and_named_reviewer_remain_in_comparison_identity(self):
        first = filled_control('R06', 'A')
        other_reviewer = deepcopy(first); other_reviewer['reviewer']['id'] = 'second-reviewer'
        other_mode = filled_control('R06', 'B')
        replies = self.browser([{'op': 'validate', 'review': r} for r in (first, other_reviewer, other_mode)])
        self.assertTrue(all(reply['ok'] for reply in replies), replies)
        a, b, c = [reply['result'] for reply in replies]
        self.assertNotEqual(a['reviewerId'], b['reviewerId'])
        self.assertNotEqual(a['comparisonKey'], b['comparisonKey'])
        self.assertNotEqual(a['mode'], c['mode'])
        self.assertNotEqual(a['comparisonKey'], c['comparisonKey'])
        self.assertNotEqual(a['inputManifestHash'], c['inputManifestHash'])

    def test_blank_never_silently_coerces_invalid_mode_or_unbound_release(self):
        calls = [{'op': 'blank', 'task_id': 'R01', 'mode': mode} for mode in ('', 0, False, 'A', [], {})]
        calls += [{'op': 'blank', 'task_id': 'R06', 'mode': mode} for mode in (None, '', 0, False, 'C', [], {})]
        calls += [{'op': 'blank', 'task_id': task, 'mode': None} for task in ('__proto__', 'constructor', 'P01', [], {})]
        self.assertTrue(all(not reply['ok'] for reply in self.browser(calls)))
        for field in ('packet', 'inputs'):
            release = deepcopy(self.release)
            if field == 'packet':
                release['tasks'][0].pop('packetHash')
            else:
                release['rubrics']['R01'].pop('input_manifest_hash')
            reply = self.browser([{'op': 'blank', 'task_id': 'R01', 'mode': None}], release)[0]
            self.assertFalse(reply['ok'], field)


if __name__ == '__main__':
    unittest.main()
