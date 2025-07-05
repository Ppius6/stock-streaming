import json
import logging
import time
from datetime import datetime

import yfinance as yf
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockProducer:
    def __init__(self):
        self.stocks = self.load_stocks()
        self.producer = None
        self.connect_to_kafka()

    def load_stocks(self):
        """Load stocks from config file, handle both string and object formats"""
        try:
            with open("config/stocks.json", "r") as f:
                config = json.load(f)

            stocks_config = config.get("stocks", [])

            stocks = []
            for item in stocks_config:
                if isinstance(item, str):
                    stocks.append(item)
                elif isinstance(item, dict) and "symbol" in item:
                    stocks.append(item["symbol"])

            logger.info(f"Loaded {len(stocks)} stocks: {stocks}")
            return stocks

        except FileNotFoundError:
            logger.error("Config file not found, using default stocks.")
            return [
                "NVDA",
                "MSFT",
                "AAPL",
                "AMZN",
                "GOOGL",
                "GOOG",
                "META",
                "AVGO",
                "TSM",
                "TSLA",
                "JPM",
                "WMT",
            ]

    def connect_to_kafka(self):
        """Connect to Kafka producer with error handling"""
        max_retries = 10

        for attempt in range(max_retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=["localhost:9092"],
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    retries=5,
                    retry_backoff_ms=1000,
                )
                logger.info("Connected to Kafka producer.")
                break
            except NoBrokersAvailable as e:
                logger.info(
                    f"⏳ Attempt {attempt + 1}/{max_retries}: Waiting for Kafka to be ready..."
                )
                time.sleep(5)
        if not self.producer:
            raise Exception("Failed to connect to Kafka after multiple attempts.")

    def stream_prices(self):
        """Stream stock prices and send to Kafka topic"""
        logger.info("🚀 Starting to stream stock prices...")
        while True:
            for symbol in self.stocks:
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="1d", interval="1m").tail(1)

                    if not data.empty:
                        price_data = {
                            "symbol": symbol,
                            "price": float(data["Close"].iloc[0]),
                            "volume": int(data["Volume"].iloc[0]),
                            "timestamp": datetime.now().isoformat(),
                        }

                        self.producer.send("stock-prices", value=price_data)
                        logger.info(f"📤 Sent: {symbol} - ${price_data['price']:.2f}")

                except Exception as e:
                    logging.error(f"Error fetching data for {symbol}: {e}")
            time.sleep(10)


if __name__ == "__main__":
    producer = StockProducer()
    producer.stream_prices()
