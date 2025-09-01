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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockCollector:
    def __init__(self):
        self.stocks = self.load_stocks()
        self.connection = self.connect_to_database()

    def load_stocks(self):
        """Load stocks from config file"""
        try:
            with open("config/stocks.json", "r") as f:
                config = json.load(f)

            stocks_config = config.get("stocks", [])
            stocks = [
                item if isinstance(item, str) else item["symbol"]
                for item in stocks_config
            ]

            logger.info(f"Loaded {len(stocks)} stocks: {stocks}")
            return stocks
        except FileNotFoundError:
            logger.error("Config file not found, using default stocks.")
            return ["NVDA", "MSFT", "AAPL", "GOOG", "AMZN", "META", "TSLA"]

    def connect_to_database(self):
        """Connect to PostgreSQL database using DATABASE_URL"""
        try:
            # Use DATABASE_URL from environment (Supabase/Railway format)
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise Exception("DATABASE_URL environment variable not set")

            connection = psycopg2.connect(database_url)
            connection.autocommit = True
            logger.info("Connected to PostgreSQL database successfully.")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def create_table_if_not_exists(self):
        """Create the stock_prices table if it doesn't exist"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_prices (
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
                CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
                ON stock_prices (symbol, timestamp);
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_date_symbol_price 
                ON stock_prices (date_only, symbol, close_price);
            """
            )

            logger.info("Database schema verified/created.")
        except Exception as e:
            logger.error(f"Error creating table: {e}")

    def collect_and_store(self):
        """Collect stock data and store in database"""
        logger.info(f"Starting stock data collection at {datetime.now()}")

        cursor = self.connection.cursor()
        successful_collections = 0

        for symbol in self.stocks:
            try:
                ticker = yf.Ticker(symbol)

                # Get latest hourly data
                data = ticker.history(period="1d", interval="1h").tail(1)

                if not data.empty:
                    # Get market cap
                    try:
                        info = ticker.info
                        market_cap = info.get("marketCap", None)
                    except:
                        market_cap = None

                    cursor.execute(
                        """
                        INSERT INTO stock_prices 
                        (symbol, open_price, high, low, close_price, volume, market_cap, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            symbol,
                            float(data["Open"].iloc[0]),
                            float(data["High"].iloc[0]),
                            float(data["Low"].iloc[0]),
                            float(data["Close"].iloc[0]),
                            int(data["Volume"].iloc[0]),
                            market_cap,
                            datetime.now(),
                        ),
                    )

                    logger.info(
                        f"Stored data for {symbol}: ${float(data['Close'].iloc[0]):.2f}"
                    )
                    successful_collections += 1
                else:
                    logger.warning(f"No data available for {symbol}")

                # Small delay between API calls
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error collecting data for {symbol}: {e}")

        logger.info(
            f"Collection completed. {successful_collections}/{len(self.stocks)} successful."
        )
        return successful_collections

    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    collector = StockCollector()
    try:
        collector.create_table_if_not_exists()
        collector.collect_and_store()
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        exit(1)
    finally:
        collector.close_connection()

    logger.info("Stock data collection completed successfully.")
