# producer.py
import os
import json
import time
from kafka import KafkaProducer
from datetime import datetime
from data_fetcher.fetch_tube_status import fetch_tube_status

# Read broker address from the environment (defaults to kafka:9092 inside Docker)
KAFKA_BROKER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
TOPIC = 'tfl_tube_status'
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
            statuses = fetch_tube_status()
            timestamp = datetime.utcnow().isoformat()
            for status in statuses:
                message = {
                    'line_id': status['line_id'],
                    'name': status['name'],
                    'status': status['status'],
                    'severity': status['severity'],
                    'timestamp': timestamp
                }
                producer.send(TOPIC, message)
                print(f"Sent: {message}")
            producer.flush()
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Stopping producer...")

if __name__ == "__main__":
    main()
