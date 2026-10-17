"""Small, dependency-free grading primitives. No text keyword grading."""
from __future__ import annotations
import math


def check(id, points, passed, detail="", critical=False):
    if passed is not None:
        passed = bool(passed)
    return {"id": str(id), "points": float(points), "passed": passed,
            "detail": str(detail), "critical": bool(critical)}


def close(actual, expected, rtol=1e-7, atol=1e-10):
    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
        return False
    if isinstance(expected, bool) or not isinstance(expected, (int, float)):
        return False
    try:
        return (math.isfinite(actual) and math.isfinite(expected)
                and math.isclose(actual, expected, rel_tol=rtol, abs_tol=atol))
    except (OverflowError, ValueError):
        # Arbitrarily large JSON integers are wrong answers, not outages of
        # the evaluator. Python's finite/isclose convert integers to float.
        return False


def numbers_close(actual, expected, rtol=1e-7, atol=1e-10):
    if isinstance(expected, dict):
        return (isinstance(actual, dict) and set(actual) == set(expected)
                and all(numbers_close(actual[k], v, rtol, atol) for k, v in expected.items()))
    if isinstance(expected, (list, tuple)):
        return (isinstance(actual, (list, tuple)) and len(actual) == len(expected)
                and all(numbers_close(a, e, rtol, atol) for a, e in zip(actual, expected)))
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        return type(actual) is type(expected) and actual == expected
    return close(actual, expected, rtol, atol)
