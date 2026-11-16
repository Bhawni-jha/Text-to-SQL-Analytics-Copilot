"""Measures how often the copilot's answer matches the answer of a known-correct query.

Run from the backend folder (venv active):
    python tests/run_eval.py

A question passes when the generated query returns the same rows as gold_sql
(column names and row order are ignored; numbers may differ by a tiny rounding amount).
Some failures are false alarms (for example a different but valid column choice), so
read the failures before trusting the number.
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.runner import QueryError, run_query  # noqa: E402
from app.service import answer_question  # noqa: E402
from app.validator import SQLValidationError, validate_sql  # noqa: E402

HERE = Path(__file__).resolve().parent


def is_num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def rows_match(a: list, b: list) -> bool:
    if len(a) != len(b):
        return False

    def sort_key(row):
        return (
            tuple(str(v) for v in row if not is_num(v)),
            tuple(float(v) for v in row if is_num(v)),
        )

    for row_a, row_b in zip(sorted(a, key=sort_key), sorted(b, key=sort_key)):
        if len(row_a) != len(row_b):
            return False
        for x, y in zip(row_a, row_b):
            if is_num(x) and is_num(y):
                if not math.isclose(x, y, rel_tol=1e-3, abs_tol=0.05):
                    return False
            elif str(x) != str(y):
                return False
    return True


def main() -> None:
    cases = json.loads((HERE / "eval_set.json").read_text(encoding="utf-8"))
    results, passed, counted = [], 0, 0

    for case in cases:
        try:
            gold = run_query(validate_sql(case["gold_sql"]))
        except (SQLValidationError, QueryError) as exc:
            print(f"[{case['id']:>2}] GOLD SQL ERROR  {case['question']}\n       {exc}")
            results.append({**case, "status": "gold_error", "detail": str(exc)})
            continue

        counted += 1
        outcome = answer_question(case["question"])
        if outcome.success and rows_match(outcome.rows, gold.rows):
            passed += 1
            status = "PASS"
        elif not outcome.success:
            status = "ERROR"
        else:
            status = "FAIL"

        print(f"[{case['id']:>2}] {status:<5} (attempts: {outcome.attempts})  {case['question']}")
        if status != "PASS":
            print(f"       generated: {(outcome.sql or outcome.error or '')[:300]}")
        results.append(
            {
                **case,
                "status": status,
                "attempts": outcome.attempts,
                "generated_sql": outcome.sql,
                "error": outcome.error,
            }
        )

    accuracy = (passed / counted * 100) if counted else 0.0
    print(f"\nAccuracy: {passed}/{counted} = {accuracy:.0f}%")
    (HERE / "eval_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("Details saved to tests/eval_results.json")


if __name__ == "__main__":
    main()
