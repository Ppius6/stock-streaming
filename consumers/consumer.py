import json
import logging
import os
import time
from datetime import datetime

import psycopg2
from dotenv import load_dotenv
from kafka import KafkaConsumer

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConsumer:
    def __init__(self):
        """Initialize the consumer and database connection."""
        self.consumer = None
        self.connection = None
        self.connect_to_kafka()
        self.connect_to_database()

    def connect_to_kafka(self):
        """Connect to Kafka consumer with error handling."""
        max_retries = 10

        kafka_servers = os.getenv("KAFKA_SERVERS", "localhost:9092").split(",")

        for attempt in range(max_retries):
            try:
                self.consumer = KafkaConsumer(
                    "stock-prices",
                    bootstrap_servers=["kafka:9092"],
                    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                    auto_offset_reset="earliest",
                    group_id="stock-consumer-group",
                )
                logger.info("Connected to Kafka successfully.")
                break
            except Exception as e:
                logger.info(
                    f"⏳ Attempt {attempt + 1}/{max_retries}: Waiting for Kafka..."
                )
                time.sleep(3)

        if not self.consumer:
            raise Exception("Failed to connect to Kafka after multiple attempts.")

    def connect_to_database(self):
        """Connect to PostgreSQL database."""
        max_retries = 10
        for attempt in range(max_retries):
            try:
                self.connection = psycopg2.connect(
                    host="postgres",
                    database=os.getenv("POSTGRES_DB"),
                    user=os.getenv("POSTGRES_USER"),
                    password=os.getenv("POSTGRES_PASSWORD"),
                    port="5432",
                )
                self.connection.autocommit = True
                logger.info("Connected to PostgreSQL database successfully.")
                break
            except Exception as e:
                logger.info(
                    f"⏳ Attempt {attempt + 1}/{max_retries}: Waiting for database..."
                )
                time.sleep(3)

        if not self.connection:
            raise Exception("❌ Failed to connect to database")

    def consume_and_store(self):
        """Consume messages from Kafka and store in database"""
        logger.info("🚀 Starting to consume and store stock data...")

        cursor = self.connection.cursor()

        for message in self.consumer:
            try:
                data = message.value

                cursor.execute(
                    """
                    INSERT INTO stock_prices (symbol, open_price, high, low, close_price, volume, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        data["symbol"],
                        data["open"],
                        data["high"],
                        data["low"],
                        data["close"],
                        data["volume"],
                        datetime.fromisoformat(data["timestamp"]),
                    ),
                )

                logger.info(f"💾 Stored: {data['symbol']} - ${data['close']:.2f}")

            except Exception as e:
                logger.error(f"❌ Database error: {e}")

    def close_connections(self):
        """Close Kafka and database connections."""
        if self.consumer:
            self.consumer.close()
            logger.info("Closed Kafka consumer connection.")
        if self.connection:
            self.connection.close()
            logger.info("Closed database connection.")


if __name__ == "__main__":
    consumer = DatabaseConsumer()
    try:
        consumer.consume_and_store()
    except KeyboardInterrupt:
        logger.info("🔔 Stopping consumer...")
    finally:
        consumer.close_connections()
        logger.info("✅ Consumer stopped and connections closed.")
