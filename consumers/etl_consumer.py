# src/consumer.py

from kafka import KafkaConsumer
import json
import pandas as pd
from src.etl import etl
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

consumer = KafkaConsumer(
    'mock_aams_traffic',
    bootstrap_servers=['127.0.0.1:9092'],
    group_id='aams_consumer_group',
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

log.info("Starting Kafka Consumer. Waiting for messages...")

for message in consumer:
    log.info(f"Received message: Partition={message.partition}, Offset={message.offset}")

    try:
        df = pd.DataFrame([message.value])
        etl(df)
        pd.set_option('display.max_columns', None)
        # print(df)
    except Exception as e:
        log.error(f"Error processing message at offset {message.offset}: {e}", exc_info=True)

consumer.close()
log.info("Consumer closed.")