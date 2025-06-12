import os
import json
import time
import sqlite3
from kafka import KafkaConsumer, errors

# Read broker address from environment; default to 'kafka:9092' inside Docker
KAFKA_BROKER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
TOPIC = 'tfl_tube_status'
GROUP_ID = 'tfl_status_consumer_group'
DB_PATH = 'data/tfl.db'   # write into /app/data so it's persisted

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tube_statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_name TEXT,
            severity INTEGER,
            timestamp TEXT
        )
    ''')
    conn.commit()
    return conn

def insert_status(conn, line_name, severity, timestamp):
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO tube_statuses (line_name, severity, timestamp) VALUES (?, ?, ?)',
        (line_name, severity, timestamp)
    )
    conn.commit()

def main():
    conn = init_db()
    print(f"Connecting to Kafka at {KAFKA_BROKER}…")

    # Retry loop in case Kafka isn’t quite ready
    for attempt in range(10):
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=KAFKA_BROKER,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id=GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            break
        except errors.NoBrokersAvailable:
            wait = 5
            print(f"  – attempt {attempt+1}/10 failed, retrying in {wait}s…")
            time.sleep(wait)
    else:
        print("Failed to connect to Kafka after multiple attempts. Exiting.")
        return

    print("Kafka consumer connected. Listening for messages…")
    for message in consumer:
        data = message.value
        line_name = data.get('name')
        severity = data.get('severity', 0)
        timestamp = data.get('timestamp', None)
        print(f"Received: {line_name} severity {severity} at {timestamp}")
        insert_status(conn, line_name, severity, timestamp)

if __name__ == "__main__":
    main()
