from kafka import KafkaConsumer
import json
import pandas as pd
import logging
from time import sleep

from src.etl import etl
from src.load import setup_db_schema, get_connection
from psycopg2.errors import OperationalError, UndefinedTable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def wait_for_db_readiness(max_retries=15, delay_seconds=2):
    log.info("Attempting initial database schema setup and readiness check...")

    setup_db_schema()

    for i in range(1, max_retries + 1):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM salary_errors LIMIT 1;")
            conn.close()
            log.info("PostgreSQL database and schema are verified ready. Continuing application startup.")
            return

        except (UndefinedTable, OperationalError) as e:
            if i < max_retries:
                log.warning(
                    f"Database dependency not met (Table or Connection not ready): Retrying in {delay_seconds}s (Attempt {i}/{max_retries})")
                sleep(delay_seconds)
            else:
                log.error(f"Database readiness failed after {max_retries} attempts.")
                raise TimeoutError("Database schema setup failed: exceeded max retries.") from e

        except Exception as e:
            log.error(f"An unexpected error occurred during DB readiness check: {e}")
            raise


if __name__ == "__main__":
    try:
        wait_for_db_readiness()

        consumer = KafkaConsumer(
            'mock_aams_traffic',
            bootstrap_servers=['kafka:9092'],
            group_id='aams_consumer_group',
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

        log.info("Starting Kafka Consumer. Waiting for messages...")

        for message in consumer:
            log.info(f"Received message: Partition={message.partition}, Offset={message.offset}")

            max_retries_msg = 5
            attempt = 0
            message_processed = False

            while not message_processed and attempt < max_retries_msg:
                try:
                    df = pd.DataFrame([message.value])
                    etl(df)
                    message_processed = True
                    log.info(f"Successfully processed message at offset {message.offset} (Attempt {attempt + 1})")

                except UndefinedTable as e:
                    if attempt < max_retries_msg - 1:
                        log.warning(f"Offset {message.offset}: DB table missing. Retrying ETL in 2s...")
                        sleep(2)
                        attempt += 1
                    else:
                        log.error(
                            f"Offset {message.offset}: DB table missing after {max_retries_msg} attempts. Skipping message.")
                        break

                except Exception as e:
                    log.error(f"Error processing message at offset {message.offset}: {e}", exc_info=True)
                    break

        consumer.close()
        log.info("Consumer closed.")

    except TimeoutError as e:
        log.critical(f"Application failed to start: {e}")
    except Exception as e:
        log.critical(f"A critical error occurred in the application startup or main loop: {e}")