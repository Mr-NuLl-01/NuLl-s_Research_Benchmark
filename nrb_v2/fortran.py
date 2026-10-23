"""V2 source-only Fortran adapter for the existing isolated execution engine.

Only the candidate's solution.f90 is staged.  Evaluator modules and expected
answers stay on the host; renaming the staged source is an internal runner
detail, not another candidate artifact requirement.
"""
from __future__ import annotations

import shutil
import subprocess

from nrb_v1.execution import execute as _execute

COMPILE_FLAGS=("-std=f2008", "-O2", "-fcheck=all", "-ffree-line-length-none")


def execute(task_module, submission, cases, backend="docker", timeout=120, image=None):
    source = submission.get("artifacts", {}).get("solution.f90")
    staged = {"task_id": submission["task_id"], "answer": {},
              "artifacts": {} if source is None else {"main.f90": source}}
    compiler=None
    if backend=="docker" and source is not None and shutil.which("docker"):
        image=image or "nrb-v2:local"
        # A Python-only image is an evaluator/environment mistake, not a zero
        # for the candidate.  This preflight runs no candidate files and has
        # neither a host mount nor a network connection.
        command=["docker","run","--rm","--pull=never","--network","none",
                 "--read-only","--cap-drop=ALL","--security-opt=no-new-privileges",
                 "--pids-limit","32","--memory","256m","--user","65534:65534",
                 "--entrypoint","gfortran",image,"--version"]
        try:
            check=subprocess.run(command,capture_output=True,text=True,timeout=20)
            if check.returncode or not check.stdout.strip():
                reason="Fortran compiler/container unavailable: "+(check.stderr.strip()[-1000:] or "gfortran --version failed")
            else:
                compiler=check.stdout.splitlines()[0]
                reason=None
        except (OSError,subprocess.SubprocessError) as exc:
            reason="Fortran compiler/container unavailable: "+type(exc).__name__+": "+str(exc)[:1000]
        if reason is not None:
            result=_execute(task_module,staged,cases,"none",timeout,image)
            result.update(backend="docker",image=image,error=reason,compiler=None,
                          compile_flags=list(COMPILE_FLAGS),candidate_source="solution.f90")
            return result
    result=_execute(task_module,staged,cases,backend,timeout,image)
    result.update(compile_flags=list(COMPILE_FLAGS),candidate_source="solution.f90")
    if compiler is not None:
        result["compiler"]=compiler
    return result
