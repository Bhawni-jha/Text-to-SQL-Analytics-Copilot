"""Turns a question + schema into a SQL query using Groq."""
import json
import re
from dataclasses import dataclass

from groq import Groq

from .config import settings

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq()  # reads GROQ_API_KEY from the environment
    return _client


# Tune these hints in Week 4 while improving accuracy. They are the cheapest way
# to fix repeated mistakes on your own database.
DOMAIN_HINTS = """
Business definitions for this database (Northwind trading company):
- Revenue / sales / order value = SUM(order_details.unit_price * order_details.quantity * (1 - order_details.discount)).
- Orders are dated between 1996 and 1998, so "last year" or "recent" questions should use those years.
- Customers, suppliers and shippers use company_name; people in employees use first_name and last_name.
"""

SYSTEM_PROMPT = f"""You are an expert PostgreSQL analyst. You receive a database schema and a question in plain English.

Reply with ONE JSON object and nothing else, in this exact format:
{{"sql": "<one PostgreSQL SELECT query>", "explanation": "<one short sentence saying what the query returns>"}}

Rules:
- Write a single read-only SELECT query (a WITH clause is fine). Never write INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, COPY or anything that changes data.
- Use only tables and columns that exist in the schema. Use the exact names.
- Alias computed columns with clear names (for example total_revenue). Round money to 2 decimals.
- For "top N" or "list" questions add ORDER BY and a sensible LIMIT.
- If the question cannot be answered from this schema, reply {{"sql": null, "explanation": "<why>"}}.
{DOMAIN_HINTS}"""


@dataclass
class Generation:
    sql: str | None
    explanation: str
    raw: str


def generate_sql(
    question: str,
    schema_text: str,
    previous_sql: str | None = None,
    error: str | None = None,
) -> Generation:
    messages = [
        {
            "role": "user",
            "content": f"Database schema (PostgreSQL):\n{schema_text}\n\nQuestion: {question}",
        }
    ]
    if previous_sql and error:
        # Self-correction: show the model its own query and the error it caused.
        messages.append(
            {"role": "assistant", "content": json.dumps({"sql": previous_sql, "explanation": ""})}
        )
        messages.append(
            {
                "role": "user",
                "content": (
                    f"That query failed.\nError: {error}\n"
                    "Fix the SQL and answer again in the same JSON format."
                ),
            }
        )

    response = _get_client().chat.completions.create(
        model=settings.groq_model,
        max_tokens=800,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages,
        ],
    )
    raw = (response.choices[0].message.content or "").strip()
    return _parse(raw)


def _parse(raw: str) -> Generation:
    text = re.sub(r"^```(?:json|sql)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)

    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1], strict=False)
            sql = data.get("sql")
            sql = sql.strip() if isinstance(sql, str) and sql.strip() else None
            return Generation(sql, str(data.get("explanation") or ""), raw)
        except (json.JSONDecodeError, AttributeError):
            pass

    # Fallback: the model answered with bare SQL
    if re.match(r"(?is)^\s*(select|with)\b", text):
        return Generation(text.strip(), "", raw)
    return Generation(None, text[:300] or "The model did not return a query.", raw)
