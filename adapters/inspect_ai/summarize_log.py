"""Extract a denominator-preserving NRB report from one Inspect log epoch."""
import argparse
import json
from pathlib import Path

from nrb.adapters import summarize_inspect_log


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    parser.add_argument("--epoch", type=int, default=1)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    dest = Path(args.out)
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("Output must be new")
    result = summarize_inspect_log(args.log, epoch=args.epoch)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 0 if result["complete_auto"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
