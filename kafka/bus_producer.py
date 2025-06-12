# producer_bus.py
import os
import json
import time
from kafka import KafkaProducer
from datetime import datetime
from data_fetcher.fetch_bus_status import fetch_bus_status

KAFKA_BROKER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
TOPIC = 'tfl_bus_status'
POLL_INTERVAL_SECONDS = 300  # 5 minutes

def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def main():
    print(f">>> Broker from ENV inside container: {KAFKA_BROKER}")
    producer = create_producer()
    print(f"Kafka producer started. Connecting to {KAFKA_BROKER}")

    try:
        while True:
            print("Fetching bus status data...")
            statuses = fetch_bus_status()
            timestamp = datetime.utcnow().isoformat()
            for status in statuses:
                status['timestamp'] = timestamp
                producer.send(TOPIC, status)
                print(f"Sent: {status}")
            producer.flush()
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Stopping bus producer...")

if __name__ == "__main__":
    main()
