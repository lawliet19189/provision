"""
Pushes all three CSVs to Supabase via PostgreSQL COPY (fast path).

Run: python3 data/push_to_supabase.py
"""

import os
import io
import csv
import psycopg2

DB_HOST     = "aws-1-us-west-2.pooler.supabase.com"
DB_PORT     = 5432
DB_NAME     = "postgres"
DB_USER     = "postgres.msxyacghespfoytxptte"
DB_PASSWORD = "ey!6L+RV#Jwk2Bp"

DATA_DIR = os.path.dirname(__file__)

DDL = """
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS products;

CREATE TABLE IF NOT EXISTS locations (
    location_id   TEXT PRIMARY KEY,
    location_name TEXT NOT NULL,
    city          TEXT NOT NULL,
    state         TEXT NOT NULL,
    store_type    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_name    TEXT PRIMARY KEY,
    category        TEXT NOT NULL,
    unit_cost_usd   NUMERIC(10,2) NOT NULL,
    unit_price_usd  NUMERIC(10,2) NOT NULL,
    supplier        TEXT NOT NULL,
    unit            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id    TEXT PRIMARY KEY,
    date              TIMESTAMPTZ NOT NULL,
    customer_name     TEXT,
    products          TEXT,
    total_items       INTEGER,
    total_cost        NUMERIC(10,2),
    payment_method    TEXT,
    city              TEXT,
    location_id       TEXT,
    store_type        TEXT,
    discount_applied  BOOLEAN,
    customer_category TEXT,
    season            TEXT,
    promotion         TEXT
);

CREATE INDEX IF NOT EXISTS idx_transactions_date        ON transactions (date);
CREATE INDEX IF NOT EXISTS idx_transactions_location_id ON transactions (location_id);
CREATE INDEX IF NOT EXISTS idx_transactions_city        ON transactions (city);
"""


def connect():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
        sslmode="require",
        connect_timeout=10,
    )


def create_schema(conn):
    print("Creating schema...")
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()
    print("  done.")


def copy_csv(conn, table, csv_path, columns):
    print(f"Loading {table} from {os.path.basename(csv_path)}...")
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        buf = io.StringIO()
        writer = csv.writer(buf)
        for row in reader:
            writer.writerow([row[c] for c in columns])
        buf.seek(0)
        with conn.cursor() as cur:
            cur.copy_expert(
                f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv)",
                buf,
            )
    conn.commit()
    print(f"  done.")


def copy_transactions(conn):
    """Stream transactions in chunks to avoid building a 1M-row buffer."""
    print("Loading transactions (1M rows, streaming)...")
    path = os.path.join(DATA_DIR, "transactions.csv")
    columns = [
        "transaction_id", "date", "customer_name", "products",
        "total_items", "total_cost", "payment_method",
        "city", "location_id", "store_type",
        "discount_applied", "customer_category", "season", "promotion",
    ]
    CHUNK = 50_000
    buf = io.StringIO()
    writer = csv.writer(buf)
    total = 0

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            writer.writerow([row[c] for c in columns])
            total += 1
            if total % CHUNK == 0:
                buf.seek(0)
                with conn.cursor() as cur:
                    cur.copy_expert(
                        f"COPY transactions ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv)",
                        buf,
                    )
                conn.commit()
                buf = io.StringIO()
                writer = csv.writer(buf)
                print(f"  {total:,} rows...")

        # flush remainder
        if buf.tell() > 0:
            buf.seek(0)
            with conn.cursor() as cur:
                cur.copy_expert(
                    f"COPY transactions ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv)",
                    buf,
                )
            conn.commit()

    print(f"  done. {total:,} rows total.")


def verify(conn):
    print("\nVerification:")
    with conn.cursor() as cur:
        for table in ("locations", "products", "transactions"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]:,} rows")
        cur.execute("SELECT MIN(date), MAX(date) FROM transactions")
        mn, mx = cur.fetchone()
        print(f"  date range: {mn} → {mx}")


def main():
    print("Connecting to Supabase...")
    conn = connect()
    print("  connected.\n")

    create_schema(conn)

    copy_csv(conn, "locations", os.path.join(DATA_DIR, "locations.csv"),
             ["location_id", "location_name", "city", "state", "store_type"])

    copy_csv(conn, "products", os.path.join(DATA_DIR, "products.csv"),
             ["product_name", "category", "unit_cost_usd", "unit_price_usd", "supplier", "unit"])

    copy_transactions(conn)

    verify(conn)
    conn.close()
    print("\nAll done.")


if __name__ == "__main__":
    main()
