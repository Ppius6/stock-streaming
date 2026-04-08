import json
import logging
import os
import time
from datetime import datetime

import psycopg2
import yfinance as yf
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockCollector:
    def __init__(self):
        self.stocks = self.load_stocks()
        self.connection = self.connect_to_database()
        self.market_caps = self.load_market_caps()

    def load_stocks(self):
        """Load stocks from the config file"""
        try:
            with open("config/stocks.json", "r") as s:
                config = json.load(s)

            stocks_config = config.get("stocks", [])
            stocks = [
                item if isinstance(item, str) else item["symbol"]
                for item in stocks_config
            ]

            logger.info(f"Loaded {len(stocks)} stocks: {stocks}")

            return stocks

        except FileNotFoundError:
            logger.error("Config file not found, using default stocks.")
            return [
                "NVDA",
                "MSFT",
                "AAPL",
                "GOOG",
                "AMZN",
                "META",
                "2222.SR",
                "AVGO",
                "TSM",
                "BRK-B",
                "TSLA",
                "JPM",
                "WMT",
                "TCEHY",
                "V",
            ]

    def connect_to_database(self):
        """Connect to the database"""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise Exception("Database URL environment variable not set.")
            conn = psycopg2.connect(database_url)
            logger.info("Connected to the database successfully!")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def create_table_if_not_exists(self):
        """Create the stock_prices table if it does not exist"""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_prices(
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    open_price DECIMAL(10, 2),
                    high DECIMAL(10, 2),
                    low DECIMAL(10, 2),
                    close_price DECIMAL(10, 2) NOT NULL,
                    volume BIGINT,
                    market_cap BIGINT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_only DATE GENERATED ALWAYS AS (timestamp::DATE) STORED
                );
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_symbool_timestamp 
                ON stock_prices (symbol, timestamp);
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_date_symbol_price
                ON stock_prices (date_only, symbol, close_price);
                """
            )
            self.connection.commit()

            logger.info("Database schema verified/created.")

    def collect_and_store(self):
        """Collect stock data and store in database"""
        logger.info(f"Starting stock data collection at {datetime.now()}")

        rows = []

        for symbol in self.stocks:

            try:
                ticker = yf.Ticker(symbol)

                # Get latest hourly data
                data = ticker.history(period="1d", interval="1h").tail(1)

                if not data.empty:
                    rows.append(
                        (
                            symbol,
                            float(data["Open"].iloc[0]),
                            float(data["High"].iloc[0]),
                            float(data["Low"].iloc[0]),
                            float(data["Close"].iloc[0]),
                            int(data["Volume"].iloc[0]),
                            self.market_caps.get(symbol),
                            datetime.now(),
                        )
                    )

            except Exception as e:
                logger.error(f"Error collecting {symbol}: {e}")
            time.sleep(0.5)

        # One batch insert
        if rows:

            try:
                with self.connection.cursor() as cursor:
                    cursor.executemany(
                        """
                        INSERT INTO stock_prices 
                        (symbol, open_price, high, low, close_price, volume, market_cap, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                        rows,
                    )
                    self.connection.commit()
                    logger.info(f"Batch inserted {len(rows)} rows.")

            except Exception as e:
                self.connection.rollback()
                logger.error(f"Batch insert failed, rolled back: {e}")

    def load_market_caps(self):
        """Fetch market caps once as they do not change hourly"""
        market_caps = {}
        for symbol in self.stocks:
            try:
                info = yf.Ticker(symbol).info
                market_caps[symbol] = info.get("marketCap", None)

            except Exception as e:
                logger.warning(f"Could not fetch market cap for {symbol}: {e}")
                market_caps[symbol] = None

        return market_caps

    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    collector = StockCollector()
    try:
        collector.create_table_if_not_exists()
        while True:

            collector.collect_and_store()
            logger.info("Sleeping for 1 hour...")
            time.sleep(3600)
    finally:
        collector.close_connection()
