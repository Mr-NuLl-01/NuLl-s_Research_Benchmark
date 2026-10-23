#!/usr/bin/env python3
"""Synchronize the static site's RC.1 catalog, candidates and score contract."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nrb_v2 import __version__
from nrb_v2.grading import public_manifest
from nrb_v2.packets import candidate, catalog
from nrb_v2.registry import PYTHON_IDS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, required=True, help="Verified source checkout, not the public dist directory")
    parser.add_argument("--downloads", type=Path)
    args = parser.parse_args()
    directory = args.site.resolve() / "dist"
    if not (directory / "index.html").is_file():
        raise SystemExit("Expected an existing static site checkout with dist/index.html")
    packets = directory / "packets-v2"
    packets.mkdir(exist_ok=True)
    items = []
    for spec in catalog()["tasks"]:
        entry = {**spec, "level": str(spec["difficulty"]) + "/5",
                 "budget": round(spec["time_budget_s"] / 60) if spec.get("time_budget_s") else None,
                 "version": __version__}
        if spec["id"] in PYTHON_IDS:
            packet = candidate(spec["id"])
            entry.update(packet="packets-v2/" + spec["id"] + ".md", packetHash=packet["packet_hash"])
            (packets / (spec["id"] + ".md")).write_text(packet["content"], encoding="utf-8")
        items.append(entry)
    downloads = json.loads(args.downloads.read_text(encoding="utf-8")) if args.downloads else {}
    data = {"version": __version__, "status": "phase1", "date": "2026-10-23",
            "tasks": items, "downloads": downloads, "grading": public_manifest((0, 17, 2026))}
    payload = json.dumps(data, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    (directory / "release-data.js").write_text("globalThis.NRB_RELEASE = " + payload + ";\n", encoding="utf-8")
    print(json.dumps({"site": str(args.site.resolve()), "version": __version__, "tasks": len(items),
                      "ready": sum(t["status"] == "ready" for t in items),
                      "fingerprint": data["grading"]["evaluatorFingerprint"]}))


if __name__ == "__main__":
    main()
