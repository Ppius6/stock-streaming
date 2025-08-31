CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    open_price DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    price DECIMAL(10, 2) NOT NULL,
    volume BIGINT,
    market_cap BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_only DATE GENERATED ALWAYS AS (timestamp::DATE) STORED
);
CREATE INDEX idx_symbol_symbol ON stock_prices (symbol, timestamp);
CREATE INDEX idx_date_only ON stock_prices (date_only, symbol);