import copy
import json
import math
import unittest
from nrb_v2 import h02

class H02Tests(unittest.TestCase):
    def test_analytic_and_backward_equations(self):
        for k in [0,1e-6,0.25,math.sqrt(7.5),12,20,100]:
            for p in [h02.PARAMETERS,{**h02.PARAMETERS,"r":0,"s":0}]:
                a,b=h02.analytical(k,p),h02.linear_oracle(k,p)
                for key in a:
                    if a[key] is None: self.assertIsNone(b[key])
                    else: self.assertAlmostEqual(a[key],b[key],delta=1e-10*max(1,abs(a[key])))
    def test_reference_and_all_mutants(self):
        for label,submission in h02.mutants().items():
            value=json.loads(submission["artifacts"]["answer.json"])
            results=[h02.validate_output(c,value)[0] for c in h02.cases()]
            self.assertEqual(all(results),label=="reference",label)
    def test_alternative_counterexamples(self):
        for k in [12,15,25,40,90]:
            a=h02.answer(); a["counterexample"]={"k":k,**{n:h02.analytical(k)[n] for n in ("yield","tau_T")}}
            self.assertTrue(h02.validate_output(h02.cases()[-1],a)[0])
    def test_shapes_types_and_duplicates(self):
        a=h02.answer(); a["cases"][1]["yield"]=True
        self.assertFalse(h02.validate_output(h02.cases()[0],a)[0])
        a=h02.answer(); a["cases"][0]=a["cases"][1]
        self.assertFalse(h02.validate_output(h02.cases()[0],a)[0])
        for text in ['{"x":1,"x":2}','{"x":NaN}']:
            with self.assertRaises(ValueError): h02.strict_loads(text)
    def test_optimum_derivative(self):
        r=h02.answer(); k=r["optimum"]["k"]
        self.assertGreater(h02.analytical(k)["yield"],h02.analytical(k*0.99)["yield"])
        self.assertGreater(h02.analytical(k)["yield"],h02.analytical(k*1.01)["yield"])
        n0,n1,n2=r["optimum"]["derivative_numerator"]
        self.assertAlmostEqual(n0+n1*k+n2*k*k,0)

if __name__=="__main__": unittest.main()
