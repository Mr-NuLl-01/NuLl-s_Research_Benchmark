"""Execute candidate files with expected answers kept in the host evaluator.

Docker is the supported boundary for arbitrary submissions. The trusted mode
exists solely for this repository's reference/mutation validation.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from .artifacts import materialize
from .provenance import fingerprint

DRIVER = r'''
import contextlib, importlib.util, io, json, os, pathlib, subprocess, sys, tempfile
data=json.load(sys.stdin)
records=[]
if data['language']=='python':
    try:
        sys.path.insert(0,os.getcwd())
        spec=importlib.util.spec_from_file_location('candidate_solution','solution.py')
        mod=importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            spec.loader.exec_module(mod)
            solve=getattr(mod,'solve',None)
            if not callable(solve):
                raise TypeError('Candidate must define callable solve(problem)')
    except BaseException as e:
        # Loading a candidate is not an attempted solution of an individual
        # case, even when its exception type matches an invalid-input check.
        records=[{'ok':False,'error':'WorkerInitializationError',
                  'detail':type(e).__name__+': '+str(e)[:500]} for _ in data['runs']]
    else:
        for item in data['runs']:
            original=json.dumps(item,sort_keys=True,allow_nan=False)
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    value=solve(item)
            except BaseException as e:
                record={'ok':False,'error':type(e).__name__,'detail':str(e)[:500]}
            else:
                try:
                    json.dumps(value,allow_nan=False)
                    record={'ok':True,'value':value}
                except BaseException as e:
                    record={'ok':False,'error':'NonJSONOutput','detail':type(e).__name__+': '+str(e)[:500]}
            try:
                if json.dumps(item,sort_keys=True,allow_nan=False)!=original:
                    record={'ok':False,'error':'InputMutation','detail':'solve changed the supplied problem object'}
            except BaseException:
                record={'ok':False,'error':'InputMutation','detail':'solve changed the supplied problem object'}
            records.append(record)
else:
    with tempfile.TemporaryDirectory(prefix='nrb-compile-') as out:
        binary=str(pathlib.Path(out)/'candidate')
        cmd=['gfortran','-std=f2008','-O2','-fcheck=all','-ffree-line-length-none','-J',out,'main.f90','-o',binary]
        compiled=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        if compiled.returncode:
            records=[{'ok':False,'error':'CompileError','detail':compiled.stderr[-3000:]} for _ in data['runs']]
        else:
            for text in data['runs']:
                try:
                    p=subprocess.run([binary],input=text,capture_output=True,text=True,timeout=data['case_timeout'])
                    records.append({'ok':p.returncode==0,'stdout':p.stdout,'error':None if p.returncode==0 else 'RuntimeError','detail':p.stderr[-1000:]})
                except subprocess.TimeoutExpired:
                    records.append({'ok':False,'error':'Timeout','detail':'Fortran case exceeded runtime budget'})
print('NRB_V1_RESULTS='+json.dumps(records,allow_nan=False,separators=(',',':')))
'''


def _run(argv, cwd, payload, timeout, env=None, drop_privileges=False):
    # File-backed streams avoid unbounded in-memory capture. RLIMIT_FSIZE also
    # bounds the child's output in trusted POSIX validation.
    def limits():
        if os.name == "posix":
            import resource
            resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
            resource.setrlimit(resource.RLIMIT_CORE,(0,0))
            if drop_privileges:
                os.setgroups([])
                os.setgid(65534)
                os.setuid(65534)
    started=time.monotonic()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc=subprocess.Popen(argv,cwd=cwd,stdin=subprocess.PIPE,stdout=out,stderr=err,
                              start_new_session=(os.name=="posix"),env=env,
                              preexec_fn=limits if os.name=="posix" else None)
        timed_out=False
        try: proc.communicate(payload.encode(),timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            if os.name=="posix": os.killpg(proc.pid,signal.SIGKILL)
            else: proc.kill()
            proc.communicate()
        out.seek(0); err.seek(0)
        stdout=out.read(16*1024*1024+1).decode(errors="replace")
        stderr=err.read(16*1024*1024+1).decode(errors="replace")
    return {"exit_code":proc.returncode,"timed_out":timed_out,"stdout":stdout,"stderr":stderr,
            "wall_seconds":time.monotonic()-started}


def execute(task_module, submission, cases, backend="docker", timeout=120, image=None):
    language=task_module.TASK["language"]
    source_name="main.f90" if language=="fortran" else "solution.py"
    common={"backend":backend,"language":language,"input_hash":fingerprint([c["input"] for c in cases]),
            "source_hash":fingerprint(submission["artifacts"].get(source_name,"")),"wall_seconds":None,
            "image_id":None,"compiler":None,"timeout_seconds":timeout}
    if source_name not in submission["artifacts"]:
        return dict(common,status="failed",error="Missing source",records=[{"ok":False,"error":"MissingSource"} for _ in cases])
    if backend=="none": return dict(common,status="unavailable",error="Execution disabled",records=[])
    if backend not in ("docker","trusted","container"): raise ValueError("Unknown execution backend")
    if backend=="container" and (os.environ.get("NRB_V1_IN_VERIFIER")!="1" or os.geteuid()!=0):
        raise ValueError("container backend is reserved for the separate root verifier")
    if backend=="docker":
        if not shutil.which("docker"):
            return dict(common,status="unavailable",error="Docker executable unavailable",records=[])
        image=image or os.environ.get("NRB_V1_IMAGE","nrb-v1:local")
        info=subprocess.run(["docker","image","inspect",image,"--format","{{.Id}}"],capture_output=True,text=True,timeout=15)
        if info.returncode:
            return dict(common,status="unavailable",error="Docker image/daemon unavailable; build environments/v1/Dockerfile",records=[])
        common.update(image=image,image_id=info.stdout.strip())
    elif language=="fortran":
        if not shutil.which("gfortran"):
            return dict(common,status="unavailable",error="gfortran unavailable",records=[])
        common["compiler"]=subprocess.run(["gfortran","--version"],capture_output=True,text=True,timeout=5).stdout.splitlines()[0]
    runs=([task_module.fortran_input(c["input"]) for c in cases] if language=="fortran" else [c["input"] for c in cases])
    payload=json.dumps({"language":language,"runs":runs,"case_timeout":min(30,timeout)},allow_nan=False)
    with tempfile.TemporaryDirectory(prefix="nrb-v1-eval-") as work:
        if backend=="container": Path(work).chmod(0o755)
        task_dir=Path(work)/"candidate"
        materialize(submission,task_dir)
        # evaluator data/expected values are never written here.
        (task_dir/"_driver_nrb.py").write_text(DRIVER)
        task_dir.chmod(0o755)
        for p in task_dir.rglob("*"):
            p.chmod(0o755 if p.is_dir() else 0o644)
        container_name="nrb-v1-"+Path(work).name.rsplit("-",1)[-1]
        if backend=="docker":
            argv=["docker","run","--rm","--name",container_name,"--pull=never","--network","none",
                  "--read-only","--cap-drop=ALL","--security-opt=no-new-privileges","--pids-limit","64",
                  "--memory","1g","--cpus","2","--user","65534:65534",
                  "--mount",f"type=bind,src={task_dir},dst=/task,readonly",
                  "--tmpfs","/tmp:rw,exec,nosuid,size=268435456","--workdir","/task","-i",
                  "-e","OPENBLAS_NUM_THREADS=1","-e","OMP_NUM_THREADS=1","-e","PYTHONDONTWRITEBYTECODE=1",
                  image,"python","-B","/task/_driver_nrb.py"]
            env=None
        else:
            argv=[sys.executable,"-B",str(task_dir/"_driver_nrb.py")]
            env={k:v for k,v in os.environ.items() if k not in ("PYTHONPATH","PYTHONHOME")}
            env.update(OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",PYTHONDONTWRITEBYTECODE="1")
        try: result=_run(argv,task_dir,payload,timeout,env,backend=="container")
        finally:
            if backend=="docker":
                subprocess.run(["docker","rm","-f",container_name],capture_output=True,timeout=15)
    common.update(wall_seconds=result["wall_seconds"],exit_code=result["exit_code"],
                  stdout_hash=fingerprint(result["stdout"].encode()),stderr_hash=fingerprint(result["stderr"].encode()),
                  stderr_excerpt=result["stderr"][-1500:])
    if result["timed_out"]:
        return dict(common,status="failed",error="Candidate runtime budget exceeded",records=[{"ok":False,"error":"Timeout"} for _ in cases])
    if backend=="docker" and result["exit_code"] in (125,126,127):
        return dict(common,status="unavailable",error="Container could not start",records=[])
    markers=[l for l in result["stdout"].splitlines() if l.startswith("NRB_V1_RESULTS=")]
    try:
        if result["exit_code"] != 0 or len(markers)!=1: raise ValueError("Missing/duplicate result frame or failed worker")
        records=json.loads(markers[0].split("=",1)[1])
        if not isinstance(records,list) or len(records)!=len(cases): raise ValueError("Incorrect case record count")
        for item in records:
            if not isinstance(item,dict) or type(item.get("ok")) is not bool:
                raise ValueError("Invalid case record schema")
            if item["ok"]:
                required="stdout" if language=="fortran" else "value"
                if required not in item or (required=="stdout" and not isinstance(item[required],str)):
                    raise ValueError("Successful case record lacks its output")
            elif not isinstance(item.get("error"),str) or not item["error"]:
                raise ValueError("Failed case record lacks its exception type")
        if language=="fortran":
            for item in records:
                if item.get("ok"):
                    try:
                        value=task_module.parse_fortran(item.pop("stdout"))
                        if isinstance(value,dict) and value.get("error")=="ValueError":
                            item.update(ok=False,error="ValueError")
                        else: item["value"]=value
                    except Exception as exc: item.update(ok=False,error="OutputFormatError",detail=str(exc))
        return dict(common,status="executed",records=records,result_hash=fingerprint(records))
    except (ValueError,TypeError,KeyError) as exc:
        return dict(common,status="failed",error=str(exc),records=[{"ok":False,"error":"WorkerFailure"} for _ in cases])

