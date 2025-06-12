import os
import json
import time
import sqlite3
from kafka import KafkaConsumer, errors

KAFKA_BROKER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
TOPIC = 'tfl_bus_status'
GROUP_ID = 'tfl_bus_consumer_group'
DB_PATH = 'data/tfl.db'  # shared DB path with tube data

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bus_arrivals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stop_id TEXT,
            route TEXT,
            destination TEXT,
            vehicle_id TEXT,
            actual_arrival TEXT,
            scheduled_arrival TEXT,
            delay_minutes REAL,
            on_time TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    return conn

def insert_arrival(conn, data):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bus_arrivals (
            stop_id, route, destination, vehicle_id,
            actual_arrival, scheduled_arrival,
            delay_minutes, on_time, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('stop_id'),
        data.get('route'),
        data.get('destination'),
        data.get('vehicle_id'),
        data.get('actual_arrival'),
        data.get('scheduled_arrival'),
        float(data.get('delay_minutes', 0)),
        data.get('on_time'),
        data.get('timestamp')
    ))
    conn.commit()

def main():
    conn = init_db()
    print(f"Connecting to Kafka at {KAFKA_BROKER}…")

    # Retry Kafka connection
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
        print(f"Received bus arrival: {data}")
        insert_arrival(conn, data)

if __name__ == "__main__":
    main()
