"""C06/C08 output-binding regressions; no compiler or candidate execution needed."""
from __future__ import annotations

import copy
import math
import unittest
from unittest.mock import patch

from nrb_v1.grading import compare_value, grade
from nrb_v1.tasks import c06, c08


class ResidualBindingRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {module.TASK['id']: module.cases(17) for module in (c06, c08)}

    def case(self, module, name):
        return next(c for c in self.cases[module.TASK['id']] if c['id'] == name)

    def assert_legacy_match(self, case, output):
        ok, detail = compare_value(output, case['expected'], case['rtol'], case['atol'])
        self.assertTrue(ok, detail)

    def assert_valid(self, module, case, output):
        ok, detail = module.validate_output(case, output)
        self.assertTrue(ok, detail)

    def assert_rejected(self, module, case, output, reason=None):
        ok, detail = module.validate_output(case, output)
        self.assertFalse(ok, detail)
        if reason is not None:
            self.assertIn(reason, detail)

    def test_reference_and_exact_manufactured_outputs_multiple_seeds(self):
        for module, solve in ((c06, c06._reference), (c08, c08._solve)):
            for seed in (0, 17, 91, 2026):
                for case in module.cases(seed):
                    if 'expected' not in case:
                        continue
                    with self.subTest(task=module.TASK['id'], seed=seed, case=case['id']):
                        self.assert_valid(module, case, solve(case['input']))
                        self.assert_valid(module, case, case['expected'])

    def test_c06_independent_nonuniform_exponential_solution(self):
        x = [0., .03, .13, .5, 1.]
        diffusion, velocity, left, right = .4, 1.3, .7, 1.4
        p = dict(x=x, diffusion=[diffusion]*4, velocity=[velocity]*4,
                 source=[0.]*3, decay=[0.]*3, left=left, right=right)
        u = [left+(right-left)*math.expm1(velocity*t/diffusion)
             /math.expm1(velocity/diffusion) for t in x]
        current = velocity*left-velocity*(right-left)/math.expm1(velocity/diffusion)
        exact = dict(density=u, flux=[current]*4,
                     mass=sum((b-a)*(ua+ub)/2 for a, b, ua, ub in zip(x, x[1:], u, u[1:])),
                     residual_inf=0.)
        case = c06._case('analytic_exponential', 'basic', p, 1)
        self.assert_valid(c06, case, exact)

    def test_c08_independent_nonuniform_affine_flux_and_ignored_interior_boundary(self):
        x, y = [0., .07, .3, 1.], [0., .1, .4, 1.4]
        nx, ny = len(x), len(y)
        kx, ky, bx, by = 7., .3, .4, -.2
        field = [[.6+bx*xx+by*yy for xx in x] for yy in y]
        boundary = [[value if i in (0, nx-1) or j in (0, ny-1) else 12345.
                     for i, value in enumerate(row)] for j, row in enumerate(field)]
        p = dict(x=x, y=y, kx=[[kx]*nx for _ in y], ky=[[ky]*nx for _ in y],
                 source=[[0.]*nx for _ in y], boundary=boundary)
        # The outer faces enclose only the interior control-volume union.
        width = (x[-1]+x[-2]-x[0]-x[1])/2
        height = (y[-1]+y[-2]-y[0]-y[1])/2
        exact = dict(field=field, boundary_flux=[kx*bx*height, -kx*bx*height,
                                                ky*by*width, -ky*by*width],
                     integrated_source=0., residual_inf=0.)
        case = dict(input=p, expected=exact, rtol=3e-7, atol=4e-7)
        self.assert_valid(c08, case, exact)

    def test_c06_rejects_small_density_error_with_self_reported_zero(self):
        case = self.case(c06, 'peclet_2250_positive')
        wrong = copy.deepcopy(case['expected'])
        wrong['density'][20] += 1e-8
        wrong['residual_inf'] = 0.
        self.assert_legacy_match(case, wrong)
        self.assert_rejected(c06, case, wrong, 'recomputed transport residual')

    def test_c08_rejects_small_interior_error_with_self_reported_zero(self):
        case = self.case(c08, 'refined_manufactured')
        wrong = copy.deepcopy(case['expected'])
        wrong['field'][9][12] += 1e-8
        wrong['residual_inf'] = 0.
        self.assert_legacy_match(case, wrong)
        self.assert_rejected(c08, case, wrong, 'recomputed elliptic residual')

    def test_residual_limits_allow_roundoff_but_reject_larger_equation_error(self):
        for module, name, small, large in (
                (c06, 'peclet_2250_positive', 1e-13, 1e-12),
                (c08, 'refined_manufactured', 1e-11, 1e-10)):
            case = self.case(module, name)
            for delta, accepted in ((small, True), (large, False)):
                with self.subTest(task=module.TASK['id'], delta=delta):
                    output = copy.deepcopy(case['expected'])
                    if module is c06:
                        output['density'][20] += delta
                    else:
                        output['field'][9][12] += delta
                    self.assert_legacy_match(case, output)
                    ok, detail = module.validate_output(case, output)
                    self.assertEqual(ok, accepted, detail)
                    if not accepted:
                        self.assertIn('recomputed', detail)

    def test_c06_flux_is_bound_to_returned_density(self):
        case = self.case(c06, 'zero_drift_linear')
        wrong = copy.deepcopy(case['expected'])
        # Both outputs remain close to the reference, but lie on opposite
        # sides of it and no longer satisfy the same constitutive law.
        wrong['density'] = [u+1.8e-8*x for u, x in zip(wrong['density'], case['input']['x'])]
        wrong['flux'] = [flux+3e-8 for flux in wrong['flux']]
        self.assert_legacy_match(case, wrong)
        self.assert_rejected(c06, case, wrong, 'reported flux')

    def test_c06_mass_is_bound_to_returned_density(self):
        case = self.case(c06, 'zero_drift_linear')
        wrong = copy.deepcopy(case['expected'])
        wrong['density'] = [u+2e-8 for u in wrong['density']]
        wrong['mass'] -= 3e-8
        self.assert_legacy_match(case, wrong)
        self.assert_rejected(c06, case, wrong, 'reported mass')

    def test_c08_boundary_flux_is_bound_to_returned_field(self):
        case = self.case(c08, 'affine_harmonic')
        wrong = copy.deepcopy(case['expected'])
        wrong['field'] = [[u+1e-7*x for u, x in zip(row, case['input']['x'])]
                          for row in wrong['field']]
        flux = wrong['boundary_flux'][0]
        wrong['boundary_flux'][0] -= .95*(case['atol']+case['rtol']*abs(flux))
        self.assert_legacy_match(case, wrong)
        self.assert_rejected(c08, case, wrong, 'reported boundary flux')

    def test_incorrect_boundaries_and_integrated_quantities_are_rejected(self):
        for module, name, field, quantity in (
                (c06, 'zero_drift_linear', 'density', 'mass'),
                (c08, 'affine_harmonic', 'field', 'integrated_source')):
            case = self.case(module, name)
            for target in ('boundary', 'integral'):
                with self.subTest(task=module.TASK['id'], target=target):
                    wrong = copy.deepcopy(case['expected'])
                    if target == 'integral':
                        wrong[quantity] += .01
                    elif module is c06:
                        wrong[field][0] += .01
                    else:
                        wrong[field][0][0] += .01
                    self.assert_rejected(module, case, wrong)

    def test_negative_reported_residual_is_not_a_norm(self):
        for module, name in ((c06, 'zero_drift_linear'), (c08, 'affine_harmonic')):
            case = self.case(module, name)
            wrong = copy.deepcopy(case['expected'])
            wrong['residual_inf'] = -case['atol']/2
            self.assert_legacy_match(case, wrong)
            self.assert_rejected(module, case, wrong, 'reported residual')

    def test_malformed_nonfinite_and_boolean_outputs_fail_closed(self):
        for module, name, field in ((c06, 'zero_drift_linear', 'density'),
                                     (c08, 'affine_harmonic', 'field')):
            case = self.case(module, name)
            for wrong in (None, [], {}, {field: []}):
                with self.subTest(task=module.TASK['id'], malformed=wrong):
                    self.assert_rejected(module, case, wrong)
            wrong = copy.deepcopy(case['expected'])
            wrong[field].pop()
            self.assert_rejected(module, case, wrong)
            for value in (True, '0', float('nan'), float('inf'), -float('inf'), 10**1000):
                for target in ('field', 'residual'):
                    with self.subTest(task=module.TASK['id'], bad_type=type(value), target=target):
                        wrong = copy.deepcopy(case['expected'])
                        if target == 'residual':
                            wrong['residual_inf'] = value
                        elif module is c06:
                            wrong[field][1] = value
                        else:
                            wrong[field][1][1] = value
                        self.assert_rejected(module, case, wrong)

    def test_grading_uses_each_validator_for_returned_records(self):
        # Mock only the execution transport.  Exercise real grade dispatch,
        # reference matching, validators, check results, and point aggregation.
        for module, target, loss in ((c06, 'peclet_2250_positive', 8),
                                     (c08, 'refined_manufactured', 10)):
            records = []
            for case in self.cases[module.TASK['id']]:
                if 'error' in case:
                    records.append(dict(ok=False, error=case['error']))
                    continue
                output = copy.deepcopy(case['expected'])
                if case['id'] == target:
                    if module is c06:
                        output['density'][20] += 1e-8
                    else:
                        output['field'][9][12] += 1e-8
                records.append(dict(ok=True, value=output))
            execution = dict(status='executed', records=records)
            with patch('nrb_v1.grading.execute', return_value=execution) as execute:
                report = grade(module.TASK['id'], module.reference_submission(), backend='trusted')
            execute.assert_called_once()
            self.assertEqual(report['auto_points'], 70-loss)
            failures = [check['id'] for check in report['checks'] if not check['passed']]
            self.assertEqual(failures, [target])


if __name__ == '__main__':
    unittest.main()
