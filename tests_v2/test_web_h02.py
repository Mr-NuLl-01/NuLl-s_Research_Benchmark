"""H02 browser/Python parity using actual JavaScript and independent numeric controls.

These synthetic controls validate the scoring implementation; they are not
model results. The correct answer below uses 70-digit backward equations,
independent of the production Python evaluator's closed-form expressions.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from nrb_v2 import __version__, GRADER_VERSION, REPORT_SCHEMA, h02
from nrb_v2.grading import grade, identity, test_manifest_hash as manifest_hash, validate_report
from nrb_v2.packets import candidate

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
BRIDGE = r"""
const fs = require('node:fs');
const h02 = require('./web/dist/h02-grader.js');
const reports = require('./web/dist/report-validation.js');
const {release,calls} = JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(calls.map(call => {
  try {
    let result;
    if (call.op === 'parse') result = reports.parseJSON(call.text);
    else if (call.op === 'validate') result = reports.validateReport(call.report, release);
    else result = h02.evaluate(call.answer, release, call.seed === undefined ? 17 : call.seed);
    return {ok:true,result};
  } catch (error) { return {ok:false,error:String(error.message)}; }
})));
"""


def backward_values(k, no_return=False):
    """Solve four first-step backward systems with Decimal Gaussian elimination."""
    with localcontext() as context:
        context.prec = 70
        d = Decimal
        k = d(k)
        r, s = (d(0), d(0)) if no_return else (d('1.1'), d('.4'))
        matrix = [[d('.3') + d('.04') * k * k + k, -k, d(0)],
                  [-r, r + d('.2') + d('.8'), -d('.8')],
                  [d(0), -s, s + d('.6') + d('.1')]]
        def solve(rhs):
            rows = [list(row) + [value] for row, value in zip(matrix, rhs)]
            for column in range(3):
                pivot = max(range(column, 3), key=lambda i: abs(rows[i][column]))
                rows[column], rows[pivot] = rows[pivot], rows[column]
                scale = rows[column][column]
                rows[column] = [entry / scale for entry in rows[column]]
                for i in range(3):
                    if i != column:
                        factor = rows[i][column]
                        rows[i] = [x - factor * y for x, y in zip(rows[i], rows[column])]
            return [row[-1] for row in rows]
        probability = solve([d(0), d(0), d('.6')])
        first = solve(probability)
        second = solve([2 * value for value in first])
        unconditional = solve([d(1)] * 3)
        return {'yield': float(probability[0]), 'tau_abs': float(unconditional[0]),
                'tau_T': float(first[0] / probability[0]) if k else None,
                'var_T': float(second[0] / probability[0] - (first[0] / probability[0]) ** 2) if k else None}


def independent_answer(counterexample_k='20'):
    with localcontext() as context:
        context.prec = 70
        optimum = Decimal('7.5').sqrt()
        rows = [('zero', '0', False), ('slow', '.25', False), ('optimal', optimum, False),
                ('fast', '12', False), ('no_return', optimum, True)]
        counterexample = backward_values(counterexample_k)
        return {
            'task_id': 'H02',
            'cases': [{'id': label, **backward_values(k, no_return)} for label, k, no_return in rows],
            # Determinant coefficients expanded independently from the given rates.
            'yield_coefficients': {'N1': .48, 'D': [.597, .78, .0796]},
            'optimum': {'k': float(optimum), 'yield': backward_values(optimum)['yield'],
                        'derivative_numerator': [.28656, 0, -.038208],
                        'positive_stationary_points': 1, 'boundary_yields': [0, 0]},
            'counterexample': {'k': float(counterexample_k), 'yield': counterexample['yield'],
                               'tau_T': counterexample['tau_T']},
        }


@unittest.skipUnless(NODE, 'Node.js is required to execute the shipped H02 scorer')
class H02BrowserParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checks = h02.cases()
        cls.release = {'version': __version__, 'grading': {
            'schema': REPORT_SCHEMA, 'version': __version__, 'grader_version': GRADER_VERSION,
            'evaluatorFingerprint': identity()['evaluator_fingerprint'],
            'tasks': {'H02': {'seeds': {str(seed): {
                'packet_hash': candidate('H02', seed)['packet_hash'],
                'test_manifest_hash': manifest_hash('H02', seed, h02.cases(seed)),
                'checks': [{key: case[key] for key in ('id', 'tier', 'weight', 'critical')}
                           for case in h02.cases(seed)],
            } for seed in (0, 17, 2026)}}},
        }}

    def browser(self, calls):
        completed = subprocess.run([NODE, '-e', BRIDGE], cwd=ROOT, capture_output=True, text=True,
                                   input=json.dumps({'release': self.release, 'calls': calls},
                                                    ensure_ascii=False, allow_nan=False), timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        results = json.loads(completed.stdout)
        self.assertEqual(len(results), len(calls))
        return results

    def assert_parity(self, cases):
        results = self.browser([{'op': 'grade', 'answer': answer} for _, answer in cases])
        for (label, answer), reply in zip(cases, results):
            with self.subTest(case=label):
                self.assertTrue(reply['ok'], reply)
                expected = [h02.validate_output(case, answer)[0] for case in self.checks]
                got = reply['result']
                self.assertEqual([c['passed'] for c in got['checks']], expected)
                weight = sum(c['weight'] for c, passed in zip(self.checks, expected) if passed)
                self.assertEqual(got['score'], round(100 * weight / 70, 6))
                self.assertEqual(got['status'], 'passed' if all(expected) else 'failed')
                self.assertEqual(got['passedCount'], sum(expected))
                self.assertEqual(got['failedCount'], len(expected) - sum(expected))
                self.assertEqual(got['pendingCount'], 0)
                self.assertIs(got['criticalPassed'], all(expected))

    def test_independent_correct_answer_and_all_published_mutants(self):
        independent = independent_answer()
        self.assertTrue(all(h02.validate_output(c, independent)[0] for c in self.checks))
        cases = [('70-digit independent answer', independent)]
        cases += [(label, h02.strict_loads(submission['artifacts']['answer.json']))
                  for label, submission in h02.mutants().items()]
        self.assert_parity(cases)

    def test_any_valid_counterexample_and_invalid_counterexamples(self):
        cases = [(str(k), independent_answer(str(k))) for k in ('.000001', '.25', '2.7386127875258306',
                                                               '12', '15', '20', '25', '40', '90', '100')]
        for label, answer in cases:
            if label in ('12', '15', '20', '25', '40', '90', '100'):
                self.assertTrue(h02.validate_output(self.checks[-1], answer)[0], label)
        self.assert_parity(cases)

    def test_valid_json_wrong_shapes_fail_only_the_affected_checks(self):
        cases = [('root:' + repr(value), value) for value in (None, False, True, 0, 1, '', [], {})]
        for field in ('cases', 'yield_coefficients', 'optimum', 'counterexample'):
            for value in (None, False, True, 0, 1, 'wrong type', [], {}):
                answer = independent_answer(); answer[field] = value
                cases.append((field + ':' + repr(value), answer))
            answer = independent_answer(); answer.pop(field)
            cases.append(('missing:' + field, answer))
        for value in (None, False, 1, 'unknown', [], {}):
            answer = independent_answer(); answer['cases'][0]['id'] = value
            cases.append(('scenario-id:' + repr(value), answer))
        answer = independent_answer(); answer['cases'][0] = deepcopy(answer['cases'][1])
        cases.append(('duplicate-scenario', answer))
        answer = independent_answer(); answer['cases'].reverse()
        cases.append(('reversed-scenarios', answer))
        for field in ('tau_T', 'var_T'):
            answer = independent_answer(); answer['cases'][0].pop(field)
            cases.append(('missing-zero-null:' + field, answer))
        self.assert_parity(cases)

    def test_numbers_boolean_null_and_integer_valued_counts(self):
        cases = []
        for field in ('yield', 'tau_abs', 'tau_T', 'var_T'):
            for value in (True, False, '1', None, [], {}, -1, 10**400):
                answer = independent_answer(); answer['cases'][1][field] = value
                cases.append((field + ':' + repr(value), answer))
        for value in (True, False, '1', None, [], {}, -1, 0, 1.0, 1.01, 2, 10**400):
            answer = independent_answer(); answer['optimum']['positive_stationary_points'] = value
            cases.append(('stationary count:' + repr(value), answer))
        for value in (True, False, '20', None, [], {}, -1, 0, 101, 10**400):
            answer = independent_answer(); answer['counterexample']['k'] = value
            cases.append(('counterexample k:' + repr(value), answer))
        self.assert_parity(cases)

    def test_numerical_tolerance_changes_only_the_intended_group(self):
        cases = []
        for field in ('yield', 'tau_abs', 'tau_T', 'var_T'):
            for direction in (-1, 1):
                for factor in (.9, 1.1):
                    answer = independent_answer()
                    expected = answer['cases'][2][field]
                    answer['cases'][2][field] = expected + direction * factor * (2e-8 + 2e-6 * abs(expected))
                    cases.append((field + ':' + str(direction * factor), answer))
        self.assert_parity(cases)

    def test_strict_json_rejects_duplicate_keys_nonfinite_and_bad_syntax(self):
        bad = ['{"x":1,"x":2}', '{"x":{"a":1,"a":2}}', '{"x":1,"\\u0078":2}',
               '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e400}',
               '{"x":-1e400}', '{"x":01}', '{"x":1,}', '[1,]', '{', '', 'undefined']
        answers = self.browser([{'op': 'parse', 'text': text} for text in bad])
        for text, reply in zip(bad, answers):
            with self.subTest(text=text):
                with self.assertRaises((ValueError, json.JSONDecodeError)):
                    h02.strict_loads(text)
                self.assertFalse(reply['ok'], reply)
        good = ['null', '[]', '{}', '1.0', '-0', '{"x":1,"y":{"x":2}}',
                '{"note":"quotes: \\"; slash: \\\\"}', json.dumps(independent_answer(), ensure_ascii=False)]
        for text, reply in zip(good, self.browser([{'op': 'parse', 'text': text} for text in good])):
            with self.subTest(text=text[:100]):
                self.assertTrue(reply['ok'], reply)
                self.assertEqual(reply['result'], h02.strict_loads(text))

    def test_actual_offline_grade_import_preserves_missing_zero_partial_and_success(self):
        values = [('missing artifact', None), ('empty artifact', ''), ('JSON null', 'null'),
                  ('malformed JSON', '{'), ('duplicate JSON field', '{"task_id":"H02","task_id":"H02"}'),
                  ('correct independent answer', json.dumps(independent_answer()))]
        for field in ('optimum', 'counterexample'):
            answer = independent_answer(); answer[field] = None
            values.append((field + ' wrong shape', json.dumps(answer)))
        reports = []
        for label, source in values:
            artifacts = {} if source is None else {'answer.json': source}
            # H02's public grade path uses the default backend selector and
            # dispatches to answer verification without launching Docker.
            report = grade('H02', {'task_id': 'H02', 'artifacts': artifacts, 'answer': {}})
            validate_report(report)
            reports.append((label, report))
        # Refresh after importing production modules, to bind actual live sources.
        self.release['grading']['evaluatorFingerprint'] = identity()['evaluator_fingerprint']
        replies = self.browser([{'op': 'validate', 'report': report} for _, report in reports])
        for (label, report), reply in zip(reports, replies):
            with self.subTest(case=label):
                self.assertTrue(reply['ok'], reply)
                got = reply['result']
                if report['score'] is None:
                    self.assertIsNone(got['score']); self.assertFalse(got['comparisonEligible'])
                else:
                    self.assertAlmostEqual(got['score'], report['score'], delta=5.1e-7)
                self.assertEqual(got['status'], report['status'])
                self.assertEqual([c['passed'] for c in got['checks']], [c['passed'] for c in report['checks']])
        self.assertIsNone(reports[0][1]['score'])
        self.assertEqual(reports[1][1]['score'], 0)
        self.assertEqual(reports[2][1]['score'], 0)
        self.assertEqual(reports[5][1]['score'], 100)
        self.assertEqual(reports[6][1]['score'], 85.714286)

    def test_browser_envelope_requires_registered_integer_seed_and_regrades_payload(self):
        answer = independent_answer()
        def envelope(seed):
            return {'schema': 'nrb-answer-v2', 'benchmark_version': __version__, 'task_id': 'H02',
                    'seed': seed, 'answer_payload': answer, 'score': -100, 'total': 9999}
        replies = self.browser([{'op': 'validate', 'report': envelope(seed)} for seed in (0, 17, 2026)])
        for reply in replies:
            self.assertTrue(reply['ok'], reply)
            self.assertEqual(reply['result']['score'], 100)
        invalid = [envelope(seed) for seed in (None, True, False, '17', [17], {}, -1, 2**32, 19)]
        omitted = envelope(17); omitted.pop('seed'); invalid.append(omitted)
        wrong_version = envelope(17); wrong_version['benchmark_version'] = 'obsolete'; invalid.append(wrong_version)
        replies = self.browser([{'op': 'validate', 'report': report} for report in invalid])
        self.assertTrue(all(not reply['ok'] for reply in replies), replies)


if __name__ == '__main__':
    unittest.main()
