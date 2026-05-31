"""
Handles the query_supabase custom tool call from DataAgent.
Keeps DB credentials host-side — the container never sees them.
"""

import os
import json
import psycopg2
import psycopg2.extras
from urllib.parse import quote_plus


def get_conn():
    return psycopg2.connect(
        host=os.environ["SUPABASE_HOST"],
        port=int(os.environ.get("SUPABASE_PORT", 5432)),
        dbname=os.environ.get("SUPABASE_DB", "postgres"),
        user=os.environ["SUPABASE_USER"],
        password=os.environ["SUPABASE_PASSWORD"],
        sslmode="require",
        connect_timeout=15,
    )


def execute_query(sql: str, limit: int = 2000) -> str:
    """
    Run a SELECT query and return JSON rows.
    Enforces a row limit to keep responses inside context window.
    """
    # Safety: only allow SELECT
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT") and not normalized.startswith("WITH"):
        return json.dumps({"error": "Only SELECT/WITH queries are allowed."})

    # Inject LIMIT if not present
    if "LIMIT" not in normalized:
        sql = sql.rstrip("; \n") + f" LIMIT {limit}"

    try:
        conn = get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        conn.close()
        return json.dumps([dict(r) for r in rows], default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


TOOL_DEFINITION = {
    "type": "custom",
    "name": "query_supabase",
    "description": (
        "Execute a SELECT SQL query against the Provision database in Supabase. "
        "Tables: transactions (transaction_id, date, products, total_items, total_cost, "
        "payment_method, city, location_id, store_type, discount_applied, customer_category, "
        "season, promotion), "
        "products (product_name, category, unit_cost_usd, unit_price_usd, supplier, unit), "
        "locations (location_id, location_name, city, state, store_type). "
        "The 'products' field in transactions is a Python list string e.g. ['Milk', 'Bread']. "
        "Today is 2026-05-31. Use date arithmetic accordingly. "
        "Call this tool whenever you need data to compute metrics or build intelligence reports."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "A valid PostgreSQL SELECT statement."
            }
        },
        "required": ["sql"]
    }
}
