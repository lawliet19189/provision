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
