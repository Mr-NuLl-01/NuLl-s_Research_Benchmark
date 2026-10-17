"""Actual Docker verifier smoke; only repository-authored code, no AI calls."""
import argparse
import json
from pathlib import Path
from nrb.core import get_case, grade_submission, reference_submission


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    path = Path(args.out)
    if path.exists():
        raise FileExistsError(path)
    results = []
    for task_id in ("NRB04", "NRB05"):
        case = get_case(task_id, 17)
        correct = reference_submission(case)
        oracle = grade_submission(case, correct, execution="docker")
        broken = reference_submission(case)
        broken["artifacts"]["solution.py"] = case["files"]["starter.py"]
        negative = grade_submission(case, broken, execution="docker")
        results.append({"task_id": task_id, "oracle": oracle, "buggy_starter": negative})
    passed = all(row["oracle"]["coverage"] == 1 and row["oracle"]["auto_points"] == 70
                 and row["buggy_starter"]["coverage"] == 1 and row["buggy_starter"]["auto_points"] < 70
                 for row in results)
    report = {"purpose": "actual Docker execution of repository oracle and negative controls; not model performance",
              "passed": passed, "results": results}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"passed": passed, "tasks": len(results), "report": str(path)}))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
