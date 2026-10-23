"""H02: closed continuous-time absorption network, with independent oracles."""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path

TASK = {"id":"H02", "title":"有回流网络：产额、条件寿命、最优与反例", "language":"json",
        "difficulty":5, "time_budget_s":2400, "required_artifacts":["answer.json"]}
PARAMETERS = {"a0":0.3, "a2":0.04, "r":1.1, "b":0.2, "h":0.8, "s":0.4, "t":0.6, "c":0.1}
RTOL, ATOL = 2e-6, 2e-8

def analytical(k, p=None):
    p = dict(PARAMETERS if p is None else p)
    a = p["a0"] + p["a2"]*k*k
    A, B, C = a+k, p["r"]+p["b"]+p["h"], p["s"]+p["t"]+p["c"]
    minor = B*C-p["h"]*p["s"]
    d0 = A*minor-k*p["r"]*C
    d1 = minor+A*(B+C)-k*p["r"]
    d2 = A+B+C
    target = k*p["h"]*p["t"]/d0
    return {"yield":target, "tau_abs":(minor+k*(C+p["h"]))/d0,
            "tau_T":d1/d0 if k else None,
            "var_T":(d1/d0)**2-2*d2/d0 if k else None}

def linear_oracle(k, p=None):
    """Independent backward equations; used to audit the closed form."""
    import numpy as np
    p = PARAMETERS if p is None else p
    M = np.array([[p["a0"]+p["a2"]*k*k+k,-k,0],
                  [-p["r"],p["r"]+p["b"]+p["h"],-p["h"]],
                  [0,-p["s"],p["s"]+p["t"]+p["c"]]],dtype=float)
    y = np.linalg.solve(M, [0,0,p["t"]])
    u = np.linalg.solve(M, y)
    v = np.linalg.solve(M, 2*u)
    life = np.linalg.solve(M, np.ones(3))
    return {"yield":float(y[0]), "tau_abs":float(life[0]),
            "tau_T":float(u[0]/y[0]) if k else None,
            "var_T":float(v[0]/y[0]-(u[0]/y[0])**2) if k else None}

def scenarios():
    optimum=math.sqrt(PARAMETERS["a0"]/PARAMETERS["a2"])
    return [("zero",0,PARAMETERS),("slow",0.25,PARAMETERS),("optimal",optimum,PARAMETERS),
            ("fast",12,PARAMETERS),("no_return",optimum,{**PARAMETERS,"r":0,"s":0})]

def coefficients():
    p=PARAMETERS
    C=p["s"]+p["t"]+p["c"]
    minor=(p["r"]+p["b"]+p["h"])*C-p["h"]*p["s"]
    return {"N1":p["h"]*p["t"], "D":[p["a0"]*minor, minor-p["r"]*C, p["a2"]*minor]}

def answer():
    co=coefficients(); n=co["N1"]; d0,d1,d2=co["D"]
    k=math.sqrt(d0/d2)
    fast=analytical(20)
    return {"task_id":"H02", "cases":[{"id":label,**analytical(k0,p)} for label,k0,p in scenarios()],
            "yield_coefficients":co,
            "optimum":{"k":k,"yield":analytical(k)["yield"],
                       "derivative_numerator":[n*d0,0,-n*d2],
                       "positive_stationary_points":1,"boundary_yields":[0,0]},
            "counterexample":{"k":20,"yield":fast["yield"],"tau_T":fast["tau_T"]}}

def _close(a,b):
    if b is None: return a is None
    return type(a) in (int,float) and math.isfinite(a) and abs(a-b)<=ATOL+RTOL*abs(b)

def _same(a,b):
    if isinstance(b,dict): return isinstance(a,dict) and set(a)==set(b) and all(_same(a[k],v) for k,v in b.items())
    if isinstance(b,list): return isinstance(a,list) and len(a)==len(b) and all(_same(x,y) for x,y in zip(a,b))
    return _close(a,b)

def cases(seed=17):
    if type(seed) is not int or not 0<=seed<2**32: raise ValueError("Invalid seed")
    return [{"id":name,"tier":tier,"weight":weight,"critical":True,"input":{"seed":seed},"expected":{},
             "rtol":RTOL,"atol":ATOL} for name,tier,weight in [
        ("target_yields","basic",10),("absorption_times","basic",10),
        ("conditional_times","scientific",15),("conditional_variances","scientific",15),
        ("global_optimum_certificate","stress",10),("valid_counterexample","stress",10)]]

def validate_output(case,value):
    try:
        if not isinstance(value,dict) or value.get("task_id")!="H02": return False,"Expected task_id H02 and an answer object"
        name=case["id"]
        if name in ("target_yields","absorption_times","conditional_times","conditional_variances"):
            key={"target_yields":"yield","absorption_times":"tau_abs","conditional_times":"tau_T","conditional_variances":"var_T"}[name]
            rows=value.get("cases")
            if not isinstance(rows,list) or len(rows)!=5 or not all(isinstance(r,dict) for r in rows):
                return False,"Exactly five named scenario rows are required"
            by_id={r.get("id"):r for r in rows}
            if set(by_id)!={x[0] for x in scenarios()}: return False,"Scenario IDs missing or duplicated"
            for label,k,p in scenarios():
                if key not in by_id[label] or not _close(by_id[label][key],analytical(k,p)[key]):
                    return False,label+" / "+key+" is outside the published tolerance or null contract"
            return True,""
        if name=="global_optimum_certificate":
            ref=answer()
            o=value.get("optimum",{})
            if not isinstance(o, dict): return False,"Optimum certificate must be an object"
            count=o.get("positive_stationary_points")
            if type(count) not in (int,float) or not math.isfinite(count) or int(count)!=count:
                return False,"Stationary-point count must be an integer-valued JSON number"
            valid=_same(value.get("yield_coefficients"),ref["yield_coefficients"]) and _same(o,ref["optimum"])
            return valid,"" if valid else "Rational yield, derivative certificate or global optimum is inconsistent"
        if name=="valid_counterexample":
            ce=value.get("counterexample",{})
            if not isinstance(ce, dict): return False,"Counterexample must be an object"
            k=ce.get("k")
            if type(k) not in (int,float) or not math.isfinite(k) or not 1e-6<=k<=100:
                return False,"Counterexample k must lie in [1e-6,100]"
            expected=analytical(k); opt=analytical(math.sqrt(PARAMETERS["a0"]/PARAMETERS["a2"]))
            valid=all(_close(ce.get(key),expected[key]) for key in ("yield","tau_T"))
            valid=valid and expected["yield"]<=0.99*opt["yield"] and expected["tau_T"]<=0.99*opt["tau_T"]
            return valid,"" if valid else "Need an accurately computed example with both yield and conditional time at least 1% below the yield optimum"
        return False,"Unknown check"
    except (KeyError,TypeError,ValueError,OverflowError,ZeroDivisionError):
        return False,"Malformed numeric answer"

def strict_loads(text):
    def constant(s): raise ValueError("Nonfinite JSON: "+s)
    def number(s):
        value=float(s)
        if not math.isfinite(value): raise ValueError("Nonfinite JSON number")
        return value
    def pairs(items):
        result={}
        for k,v in items:
            if k in result: raise ValueError("Duplicate JSON key: "+k)
            result[k]=v
        return result
    return json.loads(text, parse_constant=constant, parse_float=number, object_pairs_hook=pairs)

def execute(submission,test_cases,backend="answer",timeout=120,image=None):
    if backend == "none": return {"backend":"none","language":"json","status":"unavailable","error":"Verification disabled","records":[]}
    try:
        from nrb_v1.artifacts import decode
        raw=decode(submission["artifacts"]["answer.json"]).decode("utf-8")
        value=strict_loads(raw)
        records=[{"ok":True,"value":value} for _ in test_cases]
    except (KeyError,ValueError,TypeError) as exc:
        records=[{"ok":False,"error":"InvalidJSON","detail":str(exc)} for _ in test_cases]
    return {"backend":"trusted" if backend=="trusted" else "answer","language":"json","status":"executed",
            "method":"closed-form answer verification; no submitted code is executed","records":records}

def reference_submission(seed=17):
    return {"task_id":"H02","artifacts":{"answer.json":json.dumps(answer(),ensure_ascii=False,allow_nan=False)},"answer":{}}

def mutants(seed=17):
    result={"reference":reference_submission(seed)}
    for label,mutator in [
        ("unconditional_as_conditional",lambda a:[r.update(tau_T=r["tau_abs"]) for r in a["cases"]]),
        ("second_moment_as_variance",lambda a:[r.update(var_T=r["var_T"]+r["tau_T"]**2) for r in a["cases"] if r["tau_T"] is not None]),
        ("zero_is_zero_lifetime",lambda a:a["cases"][0].update(tau_T=0,var_T=0)),
        ("boundary_is_optimum",lambda a:a["optimum"].update({"k":0,"yield":0})),
        ("invalid_counterexample",lambda a:a["counterexample"].update(k=math.sqrt(7.5))),
        ("ignore_return",lambda a:a["cases"][2].update(**analytical(math.sqrt(7.5),{**PARAMETERS,"r":0,"s":0}))),
    ]:
        a=copy.deepcopy(answer());mutator(a)
        result[label]={"task_id":"H02","artifacts":{"answer.json":json.dumps(a)},"answer":{}}
    result["empty"]={"task_id":"H02","artifacts":{"answer.json":"{}"},"answer":{}}
    return result

def prompt(seed=17):
    return (Path(__file__).resolve().parents[1]/"tasks/v2.0/H02.md").read_text(encoding="utf-8")
