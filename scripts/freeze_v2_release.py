#!/usr/bin/env python3
"""Refresh generated prompts and bind the complete, reviewed candidate inputs.

Static R/H source prompts are never overwritten by their version wrappers.
This does not upload, commit or deploy; run the contract gate after freezing.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nrb_v1.provenance import fingerprint
from nrb_v2 import __version__
from nrb_v2.packets import candidate, catalog, input_manifest
from nrb_v2.registry import ALL_IDS, PYTHON_IDS, FORTRAN_IDS, module


def main():
    folder=ROOT / "tasks/v2.0"
    for tid in PYTHON_IDS:
        (folder / (tid+".md")).write_text(candidate(tid,17)["content"],encoding="utf-8")
    for tid in (*FORTRAN_IDS,"L01"):
        (folder / (tid+".md")).write_text(module(tid).prompt(17),encoding="utf-8")
    rows=[]
    for tid in ALL_IDS:
        packet=candidate(tid,17)
        row={"task_id":tid,"file":tid+".md","seed":17,"sha256":packet["packet_hash"],
             "source_sha256":fingerprint((folder/(tid+".md")).read_bytes())}
        if tid=="R06":
            row["input_manifest_hashes"]={mode:input_manifest(tid,17,mode)["sha256"] for mode in ("A","B")}
        else:
            row["input_manifest_hash"]=input_manifest(tid,17)["sha256"]
        rows.append(row)
    manifest={"benchmark_version":__version__,"kind":"candidate_only","tasks":rows}
    for name,value in [("manifest.json",manifest),("catalog.json",catalog(17))]:
        (folder/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"version":__version__,"tasks":len(rows),"source_prompts_preserved":"R01-R06,H01,H02"}))


if __name__=="__main__":
    main()
