"""Quick safety check for the SQL validator.  Run from the backend folder:
    python tests/test_validator.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.validator import SQLValidationError, validate_sql  # noqa: E402

SHOULD_PASS = [
    "SELECT 1",
    "SELECT * FROM orders LIMIT 5;",
    "SELECT country, COUNT(*) FROM customers GROUP BY country ORDER BY 2 DESC",
    "WITH x AS (SELECT 1 AS a) SELECT * FROM x",
    "SELECT product_name FROM products UNION SELECT company_name FROM suppliers",
    "SELECT EXTRACT(YEAR FROM order_date) AS y, COUNT(*) FROM orders GROUP BY 1",
    "SELECT * FROM customers WHERE company_name ILIKE '%market%'",
]

SHOULD_FAIL = [
    "DROP TABLE orders",
    "DELETE FROM orders",
    "UPDATE orders SET freight = 0",
    "INSERT INTO shippers (company_name) VALUES ('x')",
    "SELECT 1; SELECT 2",
    "SELECT pg_sleep(10)",
    "SELECT * INTO new_table FROM orders",
    "WITH d AS (DELETE FROM orders RETURNING *) SELECT * FROM d",
    "CREATE TABLE x (a int)",
    "TRUNCATE orders",
    "SELECT * FROM orders FOR UPDATE",
    "",
]


def main() -> None:
    failures = 0
    for sql in SHOULD_PASS:
        try:
            validate_sql(sql)
            print(f"ok    allowed : {sql}")
        except SQLValidationError as exc:
            failures += 1
            print(f"FAIL  should be allowed but was blocked ({exc}): {sql}")
    for sql in SHOULD_FAIL:
        try:
            validate_sql(sql)
            failures += 1
            print(f"FAIL  should be blocked but was allowed: {sql!r}")
        except SQLValidationError:
            print(f"ok    blocked : {sql!r}")
    print("\nAll checks passed." if failures == 0 else f"\n{failures} check(s) failed.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
