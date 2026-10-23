"""L01: checked Lean proof terms for an exact transfer-ledger invariant.

No candidate declaration is trusted. A fixed Lean driver parses a term, elaborates
it against a frozen proposition, checks the declaration with the Lean kernel,
and audits the full axiom dependency closure. Docker is the candidate boundary;
trusted mode is exclusively for reviewed repository controls.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from nrb_v1.artifacts import decode
from nrb_v1.execution import _run
from nrb_v1.provenance import fingerprint

LEAN_VERSION = "4.19.0"
LEAN_RELEASE = "https://github.com/leanprover/lean4/releases/tag/v4.19.0"
LEAN_LINUX_SHA256 = "6fe3ce97a58f44e2b3567d455b994eacec5bfe9ae7774f2a573444480ba813fe"
SOURCE_NAME = "proofs.json"
DEFAULT_IMAGE = "nrb-v2-lean:local"
ALLOWED_AXIOMS = frozenset(("propext", "Classical.choice", "Quot.sound"))
GOALS = ("step_balance", "zero_input_active", "trace_balance", "restart", "prefix_admissible", "collected_bound")
TASK = {
    "id": "L01", "title": "已有守恒结论的 Lean 形式化", "language": "lean", "difficulty": 4,
    "capabilities": ["formalization", "induction", "invariants", "conservation", "kernel-checking"],
    "required_artifacts": [SOURCE_NAME], "time_budget_s": 1800,
}

PRELUDE = 'import Lean\n\nnamespace NRB\n\nstructure State where\n  active : Nat\n  collected : Nat\n  lost : Nat\n  deriving Repr, DecidableEq\n\nstructure Event where\n  injected : Nat\n  collect : Nat\n  lose : Nat\n  deriving Repr, DecidableEq\n\ndef total (s : State) : Nat := s.active + s.collected + s.lost\n\ndef admissible (s : State) (e : Event) : Prop := e.collect + e.lose ≤ s.active + e.injected\n\ndef step (s : State) (e : Event) : State :=\n  ⟨s.active + e.injected - (e.collect + e.lose),\n   s.collected + e.collect, s.lost + e.lose⟩\n\ndef run : State → List Event → State\n  | s, [] => s\n  | s, e :: es => run (step s e) es\n\ndef injected : List Event → Nat\n  | [] => 0\n  | e :: es => e.injected + injected es\n\ndef admissibleTrace : State → List Event → Prop\n  | _, [] => True\n  | s, e :: es => admissible s e ∧ admissibleTrace (step s e) es\n\nnamespace Goals\n\ndef step_balance : Prop := ∀ (s : State) (e : Event),\n  admissible s e → total (step s e) = total s + e.injected\n\ndef zero_input_active : Prop := ∀ (s : State) (e : Event),\n  e.injected = 0 → (step s e).active ≤ s.active\n\ndef trace_balance : Prop := ∀ (s : State) (es : List Event),\n  admissibleTrace s es → total (run s es) = total s + injected es\n\ndef restart : Prop := ∀ (s : State) (xs ys : List Event),\n  run s (xs ++ ys) = run (run s xs) ys\n\ndef prefix_admissible : Prop := ∀ (s : State) (xs ys : List Event),\n  admissibleTrace s (xs ++ ys) → admissibleTrace s xs\n\ndef collected_bound : Prop := ∀ (s : State) (es : List Event),\n  admissibleTrace s es → (run s es).collected ≤ total s + injected es\n\nend Goals\nend NRB\n'

DRIVER = 'import Lean\nimport NRBPrelude\nopen Lean Meta Elab\n\n-- The only dynamically elaborated input is one term, never a command.\n-- A small, published proof language excludes metaprogram execution and configs.\ndef safeTacticKinds : List String := [\n  "tacticSorry", "tacticAdmit", "tacticTry_", "tacticRepeat_", "tacticNext_", "caseArg", "caseArgRename", "caseArgWild", "rcasesPat.ignore", "rcasesPat.clear", "rcasesPat.explicit",\n  "elimTarget", "tacticHave_", "tacticLet_", "tacticShow_", "tacticRfl", "tacticTrivial", "locationType",\n  "refine", "refine\'", "left", "right", "rename", "classical", "match", "matchRhs", "matchAlts", "applyRfl", "acRfl", "symm", "congr", "calc", "paren", "nestedTactic", "simpaArgsRest", "simpArgsRest", "dsimpArgsRest", "simpAllArgsRest",\n  "tacticSeq", "tacticSeq1Indented", "tacticSeqBracketed", "null",\n  "intro", "intros", "exact", "apply", "assumption", "constructor",\n  "rfl", "trivial", "contradiction", "omega", "decide",\n  "simp", "simpAll", "simpa", "dsimp", "unfold", "rw", "rewriteSeq", "rwRuleSeq", "rwRule",\n  "location", "locationHyp", "locationWildcard", "simpStar", "simpErase", "simpLemma",\n  "simpOnly", "simpArgs", "simpErase", "optConfig", "optConfigItem", "optStar",\n  "induction", "cases", "inductionAlts", "inductionAlt", "inductionAltsWhere",\n  "inductionAltLHS", "inductionAltsWhere", "inductionTarget", "withArg",\n  "rcases", "rcasesPat", "rcasesPat.tuple", "rcasesPat.one", "rcasesPat.alts",\n  "rcasesPatMed", "rcasesPatLo", "rcasesPat.paren", "rcasesPat.type",\n  "obtain", "case", "next", "renameI", "rename_i", "have", "let", "show", "change",\n  "subst", "revert", "generalize", "clear", "specialize",\n  "allGoals", "anyGoals", "first", "repeat", "repeat\'", "try", "focus", "done",\n  "tacticSeq1Indented", "tacticSeq", "seq1", "seq", "seqFocus", "orElse", "andThen", "parens",\n  "haveLet", "haveDecl", "haveIdDecl", "havePatDecl", "letIdDecl", "letPatDecl"\n]\n\npartial def checkSyntax (stx : Syntax) : Except String Unit := do\n  match stx with\n  | .node _ kind args =>\n    let ks := kind.toString\n    if ks.startsWith "Lean.Parser.Tactic." then\n      let localName := ks.drop "Lean.Parser.Tactic.".length\n      unless safeTacticKinds.contains localName do\n        throw ("Tactic syntax outside the published proof language: " ++ ks)\n      -- Even a pure-looking config can invoke the native expression evaluator.\n      if localName == "optConfig" && !args.isEmpty then\n        if args.any (fun a => !a.isMissing && a.getNumArgs != 0) then\n          throw "Custom tactic configuration is not allowed"\n    if ks == "Lean.Parser.Term.set_option" || ks == "Lean.Parser.Term.run" ||\n        ks == "Lean.Parser.Term.runMeta" || ks == "Lean.Parser.Term.eval" ||\n        ks == "Lean.byElab" || ks == "Lean.Parser.Term.unsafe" || ks == "Lean.includeStr" then\n      throw "Term-level metaprogram execution/options/external input are not allowed"\n    for a in args do checkSyntax a\n  | _ => pure ()\n\npartial def syntaxKinds (s : Syntax) : Array String :=\n  match s with\n  | .node _ k args => #[k.toString] ++ (args.flatMap syntaxKinds)\n  | _ => #[]\n\ndef goals : Array (String × Name) := #[\n  ("step_balance", `NRB.Goals.step_balance),\n  ("zero_input_active", `NRB.Goals.zero_input_active),\n  ("trace_balance", `NRB.Goals.trace_balance),\n  ("restart", `NRB.Goals.restart),\n  ("prefix_admissible", `NRB.Goals.prefix_admissible),\n  ("collected_bound", `NRB.Goals.collected_bound)\n]\n\ndef failRecord (id msg : String) : Json := Json.mkObj [\n  ("ok", toJson false), ("error", toJson "ProofRejected"), ("detail", toJson msg),\n  ("goal", toJson id)\n]\n\nunsafe def checkProof (env : Environment) (id : String) (goal : Name) (proof : String) : IO Json := do\n  try\n    let stx ← IO.ofExcept (Parser.runParserCategory env `term proof)\n    -- Print is disabled for normal evaluation; helpful when auditing syntax.\n    if (← IO.getEnv "NRB_LEAN_AST") == some "1" then\n      IO.eprintln (toJson ((syntaxKinds stx).toList.eraseDups)).compress\n    IO.ofExcept (checkSyntax stx)\n    let opts := ({} : Options).setBool `Elab.async false |>.setBool `debug.skipKernelTC false |>.setNat `maxHeartbeats 2000000\n    let target := mkConst goal\n    let name := Name.str `NRB.Checked id\n    let action : CoreM (Array Name × String) := MetaM.run\' <| Term.TermElabM.run\' do\n      let value ← Term.elabTermEnsuringType stx (some target)\n      Term.synthesizeSyntheticMVarsNoPostponing\n      let value ← instantiateMVars value\n      unless !value.hasMVar && !value.hasFVar do throwError "Unclosed proof"\n      -- Synchronous kernel checking is forced after elaboration.\n      withOptions (fun _ => opts) do\n        addDecl <| Declaration.thmDecl { name := name, levelParams := [], type := target, value := value }\n      let some info := (← getEnv).checked.get.find? name | throwError "Missing kernel declaration"\n      unless info.type == target do throwError "Target type changed"\n      let axs ← collectAxioms name\n      let statement ← ppExpr (← whnf target)\n      return (axs, toString statement)\n    let ctx : Core.Context := {\n      fileName := "candidate-proof"\n      fileMap := FileMap.ofString proof\n      options := opts\n      currNamespace := `NRB\n      openDecls := [.simple `NRB []]\n    }\n    -- Every goal starts from the identical trusted environment. No failed or\n    -- successful previous candidate declaration is available to another goal.\n    let ((axs, statement), state) ← action.toIO ctx { env := env }\n    if state.messages.hasErrors then\n      return failRecord id "Elaboration produced errors"\n    let allowed : Array Name := #[`propext, `Classical.choice, `Quot.sound]\n    if axs.any (fun ax => !allowed.contains ax) then\n      return failRecord id ("Forbidden transitive axiom dependency: " ++ String.intercalate ", " (axs.toList.map Name.toString))\n    return Json.mkObj [\n      ("ok", toJson true),\n      ("value", Json.mkObj [\n        ("goal", toJson id), ("kernel_checked", toJson true),\n        ("target_verified", toJson true), ("axioms", toJson (axs.map Name.toString)),\n        ("statement", toJson statement)\n      ])\n    ]\n  catch err =>\n    return failRecord id err.toString\n\nunsafe def main (args : List String) : IO UInt32 := do\n  initSearchPath (← findSysroot)\n  enableInitializersExecution\n  let env ← importModules (loadExts := true) #[{ module := `NRBPrelude }] {} 0\n  let data ← IO.ofExcept (Json.parse (← IO.FS.readFile (args[0]!)))\n  let mut records : Array Json := #[]\n  for (id, goal) in goals do\n    match data.getObjValAs? String id with\n    | .error msg => records := records.push (failRecord id msg)\n    | .ok proof => records := records.push (← checkProof env id goal proof)\n  IO.println ("NRB_L01_RESULTS=" ++ (toJson records).compress)\n  return 0\n'

REFERENCE_PROOFS = {'step_balance': 'by\n  intro s e h\n  unfold admissible at h\n  unfold total step\n  dsimp\n  omega', 'zero_input_active': 'by\n  intro s e h\n  simp only [step]\n  omega', 'trace_balance': 'by\n  intro s es\n  induction es generalizing s with\n  | nil => simp [run, injected, total]\n  | cons e es ih =>\n    intro h\n    rcases h with ⟨he, hrest⟩\n    have hstep : total (step s e) = total s + e.injected := by\n      unfold admissible at he\n      unfold total step\n      dsimp\n      omega\n    have ht := ih (step s e) hrest\n    simp only [run, injected]\n    omega', 'restart': 'by\n  intro s xs\n  induction xs generalizing s with\n  | nil => intro ys; rfl\n  | cons e es ih =>\n    intro ys\n    simp only [List.cons_append, run]\n    exact ih (step s e) ys', 'prefix_admissible': 'by\n  intro s xs\n  induction xs generalizing s with\n  | nil => intro ys h; trivial\n  | cons e es ih =>\n    intro ys h\n    change admissible s e ∧ admissibleTrace (step s e) (es ++ ys) at h\n    exact ⟨h.1, ih (step s e) ys h.2⟩', 'collected_bound': 'by\n  intro s es h\n  have bal : ∀ (s : State) (es : List Event), admissibleTrace s es →\n      total (run s es) = total s + injected es := by\n    intro s es\n    induction es generalizing s with\n    | nil => simp [run, injected, total]\n    | cons e es ih =>\n      intro h\n      rcases h with ⟨he, hrest⟩\n      have hstep : total (step s e) = total s + e.injected := by\n        unfold admissible at he\n        unfold total step\n        dsimp\n        omega\n      have ht := ih (step s e) hrest\n      simp only [run, injected]\n      omega\n  have hb := bal s es h\n  unfold total at hb ⊢\n  omega'}


def cases(seed=17):
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("Seed must be an integer in [0,2**32)")
    tiers = ("basic", "basic", "scientific", "scientific", "stress", "stress")
    weights = (10, 10, 15, 15, 10, 10)
    return [{"id": goal, "tier": tier, "weight": weight,
             "critical": goal in ("step_balance", "trace_balance", "collected_bound"),
             "input": {"goal": goal, "toolchain": LEAN_VERSION}, "expected": True,
             "rtol": 0, "atol": 0}
            for goal, tier, weight in zip(GOALS, tiers, weights)]


def validate_output(case, value):
    if not isinstance(value, dict):
        return False, "Missing native kernel audit record"
    if value.get("goal") != case["id"] or value.get("kernel_checked") is not True or value.get("target_verified") is not True:
        return False, "Fixed target was not checked by the Lean kernel"
    axioms = value.get("axioms")
    if (not isinstance(axioms, list) or any(type(a) is not str for a in axioms)
            or len(set(axioms)) != len(axioms) or not set(axioms) <= ALLOWED_AXIOMS):
        return False, "Disallowed or malformed transitive axiom dependencies"
    if not isinstance(value.get("statement"), str) or not value["statement"]:
        return False, "Missing expanded target statement"
    return True, "Lean " + LEAN_VERSION + " kernel; axioms: " + (", ".join(axioms) or "none")


def _strict_proofs(source):
    raw = decode(source)
    if len(raw) > 256 * 1024:
        raise ValueError("proofs.json exceeds 256 KiB")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate proof key: " + key)
            result[key] = value
        return result
    result = json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                        parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    if not isinstance(result, dict) or any(k not in GOALS for k in result):
        raise ValueError("Expected an object containing only the six published goal keys")
    if any(type(v) is not str or len(v.encode("utf-8")) > 48 * 1024 for v in result.values()):
        raise ValueError("Each proof must be a Lean term string of at most 48 KiB")
    # Missing keys earn zero for their own obligation; partial work can be scored.
    return result


def reference_submission(seed=17):
    return {"task_id": "L01", "artifacts": {SOURCE_NAME: json.dumps(REFERENCE_PROOFS, ensure_ascii=False)}, "answer": {}}


def mutants(seed=17):
    def submission(proofs):
        return {"task_id": "L01", "artifacts": {SOURCE_NAME: json.dumps(proofs, ensure_ascii=False)}, "answer": {}}
    result = {"reference": reference_submission(seed)}
    examples = {
        "sorry": "by sorry",
        "indirect_sorry": "by\n  have h : False := by\n    sorry\n  exact False.elim h",
        "weakened_statement": "by exact True.intro",
        "axiom_command": "by sorry\naxiom injected : False",
        "native_decide": "by native_decide",
        "metaprogram": 'by run_tac do Lean.logInfo "forged pass"; sorry',
        "term_metaprogram": "by_elab do return Lean.mkConst ``True.intro",
        "native_config": "by decide +native",
        "unsafe_term": "unsafe (by sorry)",
        "include_file": 'by\n  have leaked : String := include_str "/tmp/nrb-l01-missing-input.txt"\n  sorry',
        "skip_kernel": "by set_option debug.skipKernelTC true in sorry",
    }
    for label, term in examples.items():
        result[label] = submission({goal: term for goal in GOALS})
    partial = dict(REFERENCE_PROOFS)
    partial["trace_balance"] = "by intro s es h; rfl"
    result["invalid_trace_induction"] = submission(partial)
    result["missing_obligation"] = submission({k: v for k, v in REFERENCE_PROOFS.items() if k != "collected_bound"})
    result["empty"] = submission({})
    return result


_WORKER = r'''
import json, os, pathlib, re, shutil, subprocess, sys, tempfile
PRELUDE = __PRELUDE__
DRIVER = __DRIVER__
VERSION = __VERSION__

def unavailable(message, compiler=None):
    return {"status":"unavailable", "error":message, "compiler":compiler, "records":[]}

def failed(message):
    return {"status":"failed", "error":message,
            "records":[{"ok":False,"error":"VerifierFailed","detail":message} for _ in range(6)]}

def main():
    data=json.load(sys.stdin)
    lean=os.environ.get("NRB_LEAN") or shutil.which("lean")
    if not lean:
        return unavailable("Lean executable unavailable; build environments/v2/LeanDockerfile")
    lean=pathlib.Path(lean).resolve()
    try:
        check=subprocess.run([str(lean),"--version"],capture_output=True,text=True,timeout=10)
    except (OSError,subprocess.SubprocessError) as exc:
        return unavailable("Lean could not start: "+str(exc))
    compiler=check.stdout.strip()
    if check.returncode or not re.search(r"\bversion "+re.escape(VERSION)+r"(?:,|\))",compiler):
        return unavailable("Pinned Lean "+VERSION+" required; observed "+compiler+" "+check.stderr[-500:],compiler)
    with tempfile.TemporaryDirectory(prefix="nrb-l01-") as work:
        path=pathlib.Path(work)
        (path/"NRBPrelude.lean").write_text(PRELUDE,encoding="utf-8")
        (path/"Driver.lean").write_text(DRIVER,encoding="utf-8")
        (path/"proofs.json").write_text(json.dumps(data["proofs"],ensure_ascii=False),encoding="utf-8")
        env={k:v for k,v in os.environ.items() if k not in ("LEAN_PATH","LEAN_SRC_PATH","LEAN_SYSROOT","NRB_LEAN_AST")}
        env.update(LEAN_PATH=work,LEAN_SYSROOT=str(lean.parent.parent))
        pre=subprocess.run([str(lean),"-o","NRBPrelude.olean","NRBPrelude.lean"],cwd=work,env=env,capture_output=True,text=True,timeout=30)
        if pre.returncode:
            return unavailable("Trusted Lean prelude failed to compile: "+pre.stdout[-2000:]+pre.stderr[-1000:],compiler)
        try:
            run=subprocess.run([str(lean),"--run","Driver.lean","proofs.json"],cwd=work,env=env,capture_output=True,text=True,timeout=data["timeout"])
        except subprocess.TimeoutExpired:
            return failed("Lean proof process exceeded the execution budget")
    frames=[line for line in run.stdout.splitlines() if line.startswith("NRB_L01_RESULTS=")]
    if run.returncode or len(frames)!=1:
        return failed("Lean driver did not produce exactly one valid result frame: "+run.stdout[-2000:]+run.stderr[-1000:])
    try:
        records=json.loads(frames[0].split("=",1)[1])
        if not isinstance(records,list) or len(records)!=6 or any(not isinstance(x,dict) or type(x.get("ok")) is not bool for x in records):
            raise ValueError("Invalid kernel audit record count/schema")
    except (ValueError,TypeError) as exc:
        return failed(str(exc))
    return {"status":"executed","compiler":compiler,"records":records}

try:
    result=main()
except (OSError,subprocess.SubprocessError) as exc:
    result=unavailable(type(exc).__name__+": "+str(exc)[:1500])
print("NRB_L01_WORKER="+json.dumps(result,ensure_ascii=False,separators=(",",":"),allow_nan=False))
'''


def _worker_source():
    return (_WORKER.replace("__PRELUDE__", repr(PRELUDE))
            .replace("__DRIVER__", repr(DRIVER)).replace("__VERSION__", repr(LEAN_VERSION)))


def execute(submission, test_cases=None, backend="docker", timeout=120, image=None):
    test_cases = cases() if test_cases is None else test_cases
    if [c["id"] for c in test_cases] != list(GOALS):
        raise ValueError("L01 uses the six frozen theorem obligations in their published order")
    if backend not in ("docker", "trusted", "none"):
        raise ValueError("Unsupported execution backend")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 3600:
        raise ValueError("Timeout must be finite and in (0,3600]")
    source = submission.get("artifacts", {}).get(SOURCE_NAME)
    common = {"backend": backend, "language": "lean", "toolchain": LEAN_VERSION,
              "input_hash": fingerprint([c["input"] for c in test_cases]),
              "source_hash": fingerprint(decode(source)) if source is not None else fingerprint(b""),
              "wall_seconds": None, "image_id": None, "compiler": None, "timeout_seconds": timeout,
              "audit_method": "fixed target + synchronous Lean kernel + transitive Lean.collectAxioms"}
    if backend == "none":
        return dict(common, status="unavailable", error="Execution disabled", records=[])
    try:
        if source is None:
            raise ValueError("Missing proofs.json")
        proofs = _strict_proofs(source)
    except (ValueError, UnicodeError, TypeError) as exc:
        return dict(common, status="failed", error=str(exc),
                    records=[{"ok": False, "error": "InvalidProofPacket", "detail": str(exc)} for _ in test_cases])
    image = image or DEFAULT_IMAGE
    if backend == "docker":
        if not shutil.which("docker"):
            return dict(common, status="unavailable", error="Docker executable unavailable; build environments/v2/LeanDockerfile", records=[])
        try:
            info = subprocess.run(["docker", "image", "inspect", image, "--format", "{{.Id}}"], capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.SubprocessError) as exc:
            return dict(common, status="unavailable", error=str(exc), records=[])
        if info.returncode:
            return dict(common, status="unavailable", error="Docker daemon/image unavailable; build environments/v2/LeanDockerfile as nrb-v2-lean:local", records=[])
        common.update(image=image, image_id=info.stdout.strip())
    payload = json.dumps({"proofs": proofs, "timeout": max(1, timeout - 10)}, ensure_ascii=False, allow_nan=False)
    with tempfile.TemporaryDirectory(prefix="nrb-v2-l01-") as work:
        task_dir = Path(work)
        task_dir.chmod(0o755)
        worker = task_dir / "_nrb_lean_worker.py"
        worker.write_text(_worker_source(), encoding="utf-8")
        worker.chmod(0o644)
        container_name = "nrb-l01-" + task_dir.name.rsplit("-", 1)[-1]
        if backend == "docker":
            argv = ["docker", "run", "--rm", "--name", container_name, "--pull=never", "--platform", "linux/amd64",
                    "--network", "none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                    "--pids-limit", "64", "--memory", "1g", "--cpus", "2", "--user", "65534:65534",
                    "--mount", f"type=bind,src={task_dir},dst=/task,readonly",
                    "--tmpfs", "/tmp:rw,exec,nosuid,size=268435456", "--workdir", "/task", "-i",
                    "-e", "PYTHONDONTWRITEBYTECODE=1", image, "python", "-B", "/task/_nrb_lean_worker.py"]
            env = None
        else:
            argv = [sys.executable, "-B", str(worker)]
            env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
        try:
            result = _run(argv, task_dir, payload, timeout, env)
        except (OSError, subprocess.SubprocessError) as exc:
            return dict(common, status="unavailable", error=str(exc), records=[])
        finally:
            if backend == "docker":
                try:
                    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=15)
                except (OSError, subprocess.SubprocessError):
                    pass
    common.update(wall_seconds=result["wall_seconds"], exit_code=result["exit_code"],
                  stdout_hash=fingerprint(result["stdout"].encode()), stderr_hash=fingerprint(result["stderr"].encode()),
                  stderr_excerpt=result["stderr"][-1500:])
    if result["timed_out"]:
        return dict(common, status="failed", error="Lean worker execution budget exceeded",
                    records=[{"ok": False, "error": "Timeout", "detail": "Lean worker exceeded budget"} for _ in test_cases])
    if backend == "docker" and result["exit_code"] in (125, 126, 127):
        return dict(common, status="unavailable", error="Container could not start", records=[])
    frames = [line for line in result["stdout"].splitlines() if line.startswith("NRB_L01_WORKER=")]
    try:
        if result["exit_code"] != 0 or len(frames) != 1:
            raise ValueError("Missing/duplicate worker frame or failed worker")
        parsed = json.loads(frames[0].split("=", 1)[1])
        if not isinstance(parsed, dict) or parsed.get("status") not in ("executed", "failed", "unavailable"):
            raise ValueError("Malformed worker result")
        records = parsed["records"]
        if parsed["status"] != "unavailable" and (not isinstance(records, list) or len(records) != len(test_cases)):
            raise ValueError("Wrong number of theorem audit records")
    except (ValueError, KeyError, TypeError) as exc:
        return dict(common, status="failed", error=str(exc),
                    records=[{"ok": False, "error": "WorkerFailed", "detail": str(exc)} for _ in test_cases])
    common.update(status=parsed["status"], compiler=parsed.get("compiler"), records=records)
    if parsed.get("error"):
        common["error"] = parsed["error"]
    common["proof_audit"] = [record.get("value", {"goal": case["id"], "error": record.get("error"), "detail": record.get("detail")})
                              for case, record in zip(test_cases, records)]
    return common


def prompt(seed=17):
    cases(seed)
    return f"""# L01 · 已有守恒与不变量结论的 Lean 形式化

设计难度 4/5；题面种子 {seed}。本题六个全称命题不随种子改变。

## 科学问题与已知结论

一个闭合计数系统把对象记录在三个账本中：`active`（仍在系统内）、`collected`（累计收集）和 `lost`（累计损失）。一次事件先注入 `injected` 个对象，再把 `collect` 个对象记为收集、`lose` 个对象记为损失。所有量都是任意大小的非负整数 `Nat`，属于精确离散计数；这里不声称证明连续微分方程或浮点程序。

有效事件满足 `collect + lose ≤ active + injected`。这正是自然数减法不会截断负数的条件。若不加这个条件，减法仍是 Lean 的饱和减法，但守恒恒等式一般不成立。有效事件序列要求每个事件在**当时状态**上有效，不能只检查初始状态。

以下是要形式化的已有结论，不要求提出新定理：

1. 有效单步的三账本总量恰好增加注入量。
2. 若本步注入量为零，活动量不会增加。这个不等式无需有效性前提；饱和减法也只会减少活动量。
3. 任意有限有效事件序列的最终总量等于初始总量加累计注入量。
4. 先执行前缀、保存状态，再执行后缀，与一次执行连接后的序列完全相同。
5. 一个有效序列的任意前缀仍有效。
6. 有效序列的累计收集量不超过初始三账本总量与累计注入量之和。初始收集和损失可以非零，因此上界不能偷偷替换为初始活动量。

## 固定数学定义与目标类型

工具链固定为 **Lean {LEAN_VERSION}**，仅使用其随附 `Lean`/`Std` 库，不使用 mathlib。下列定义和 `Goals` 中的目标类型由评测器固定。你不能改定义、增加前提或用另一个相似命题替代目标。

```lean
{PRELUDE.rstrip()}
```

`run` 按列表从左至右执行；`admissibleTrace` 中递归状态与 `run` 一致。以上记录及六个全称命题构成本题完整语义。

## 提交

提交一个 UTF-8 的 **`proofs.json`**，顶层是 JSON 对象。六个键分别是：

```json
{{
  "step_balance": "by\\n  ...",
  "zero_input_active": "by\\n  ...",
  "trace_balance": "by\\n  ...",
  "restart": "by\\n  ...",
  "prefix_admissible": "by\\n  ...",
  "collected_bound": "by\\n  ..."
}}
```

每个值是一段完整 Lean **term**，例如 `by` 开头的证明块或函数式证明项。解析上下文已经 `open NRB`。每个证明分别从相同的上述定义环境开始；不能引用其他键的候选证明。需要辅助引理时，在本证明内用 `have` 写出。缺失的键只使对应义务失败；额外键、重复键、非字符串、非法 JSON 会使整个提交失败。文件不超过 256 KiB，每个证明不超过 48 KiB。

为了防止候选元程序改变评测器环境，公开的证明语言允许常规项表达式及以下核心战术族：`intro/intros`、`exact/apply/refine`、`assumption`、`constructor/left/right`、`rfl/trivial/contradiction`、`have/let/show/change`、`cases/induction/rcases/obtain`、`rename_i/subst/revert/generalize/clear/specialize`、`rw/simp/simp_all/simpa/dsimp/unfold`、`omega/decide`、`case/next/all_goals/any_goals/first/repeat/try/focus/done`，以及其常规分支、位置和括号语法。普通证明项、局部辅助证明和命题组合不受“只用某一种证明”的限制。

不允许顶层命令、用户元程序、`run_tac/by_elab`、`include_str`、`unsafe`、`native_decide`、`set_option`、自定义战术配置、外部插件或原生求值信任路径。这里的限制是明确的测试语言合同。`sorry`、`admit`、直接或间接的 `sorryAx`、新公理即便能编译也不通过。

可在自己的固定 Lean 环境把每段值填入 `theorem local_test : NRB.Goals.<键名> := <证明项>` 做自检。不需提交解释报告；解释没有人工分。不要提交声称已通过的日志来代替证明。

## 自动评分与核验

|证明义务|组别|相对权重|
|---|---|---:|
|step_balance|基础|10|
|zero_input_active|基础|10|
|trace_balance|科学|15|
|restart|科学|15|
|prefix_admissible|边界|10|
|collected_bound|边界|10|

每个义务都实际调用固定 Lean 工具链：先按 `term` 语法解析，再针对固定期望类型展开证明，完成同步内核检查，并从内核环境读取目标及传递公理依赖。只允许 `propext`、`Classical.choice`、`Quot.sound`；依赖表为空也合格。不得用字符串搜索、Python 真值模拟或仅有进程退出码替代这些检查。

分数为 `100 × 通过权重 / 70`。所有义务通过才标记 `passed`，部分通过仍显示实际部分分。缺编译器、错误工具链版本、Docker 不可用等环境问题为 `unscored/null`；语法错误、错证、放宽命题、禁止语法和超时属于作答失败。每个证明的 `maxHeartbeats` 为 2,000,000；默认整次验证执行预算为 120 s（包含启动及六个证明）。这不是模型作答的时间预算。

正式候选通过 `nrb-v2-lean:local` Docker 镜像执行；`trusted` 只用于已审读的参考与错误控制。网页只核对导入报告与重算权重，不在浏览器运行 Lean，也不把普通 JSON/哈希称为不可伪造认证。

## 来源与适用范围

守恒与前缀不变量是上述明确给定离散更新的标准归纳结论；本题模型及合成计数约定由题库编写，不使用私人科研结果。Lean 的内核、定义、公理依赖与固定版本说明见：

- https://lean-lang.org/doc/reference/latest/ValidatingProofs/
- https://lean-lang.org/theorem_proving_in_lean4/axioms_and_computation.html
- {LEAN_RELEASE}

核验结果仅覆盖这里冻结的六个精确命题，不替代现实系统模型、连续动力学或数值实现的独立验证。
"""


def candidate_files(seed=17):
    """Optional candidate-only project files; never include reference proofs."""
    return {"L01.md": prompt(seed), "NRBPrelude.lean": PRELUDE,
            "lean-toolchain": "leanprover/lean4:v" + LEAN_VERSION + "\n",
            "proofs.template.json": json.dumps({name: "" for name in GOALS}, ensure_ascii=False, indent=2) + "\n"}
