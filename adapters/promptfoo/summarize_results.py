"""Extract one canonical ten-task NRB result from a promptfoo JSON export."""
import argparse
import json
from pathlib import Path

from nrb.adapters import summarize_promptfoo_results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    path = Path(args.out)
    if path.exists() or path.is_symlink():
        raise FileExistsError("Choose a new output file")
    result = summarize_promptfoo_results(args.results)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 0 if result["complete_auto"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
