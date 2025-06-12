**Project Name: TfL Status Streamer**

A real-time data pipeline for fetching, streaming, and persisting Transport for London (TfL) bus and Tube status updates using Kafka, Python, and SQLite.

---

## 🗂️ Repository Structure

```text
.
├── kafka/
│   ├── producer.py           # Tube status producer
│   ├── bus_producer.py       # Bus arrival producer
│   ├── consumer.py           # Tube status consumer
│   └── bus_consumer.py       # Bus arrival consumer
├── data_fetcher/
│   ├── fetch_tube_status.py  # Module to fetch Tube statuses from TfL API
│   └── fetch_bus_status.py   # Module to fetch bus arrivals and calculate delays from TfL API
├── docker/
│   ├── Dockerfile.producer  # Docker image for producers
│   └── Dockerfile.consumer  # Docker image for consumers
├── data/                     # SQLite database files (persisted)
│   └── tfl.db
├── requirements.txt          # Python dependencies
└── docker-compose.yml        # Multi-container orchestration (Zookeeper, Kafka, producers, consumers)
```

## 📡 Data Fetchers

This project includes two data fetcher modules located in the `data_fetcher/` directory:

* **`fetch_tube_status.py`**: Fetches the status of all Tube lines from the TfL API endpoint `https://api.tfl.gov.uk/Line/Mode/tube/Status`. It maps human-readable status descriptions (e.g., "Good Service", "Minor Delays") to a numeric severity score and returns a list of dictionaries with the following keys:

  * `line_id`: Identifier of the Tube line
  * `name`: Human-readable line name
  * `status`: Status description
  * `severity`: Numeric severity level (lower = more severe)

* **`fetch_bus_status.py`**: Retrieves arrival predictions for a fixed set of TfL bus stop IDs. For each predicted arrival, it parses the expected arrival timestamp, fetches the scheduled timetable for comparison, and calculates the delay (in minutes). It then returns a list of records containing:

  * `stop_id`: Bus stop Naptan ID
  * `route`: Bus route identifier
  * `destination`: Destination name
  * `vehicle_id`: Unique vehicle identifier
  * `actual_arrival`: Parsed actual arrival time (UTC)
  * `scheduled_arrival`: Closest scheduled arrival time (UTC)
  * `delay_minutes`: Calculated delay in minutes (from schedule)
  * `on_time`: "Yes" if delay is within ±5 minutes, otherwise "No"
  * `timestamp`: Injection timestamp added by the producer

These modules are used by the respective producer scripts (`producer.py` and `producer_bus.py`) to supply enriched TfL data into Kafka topics.

---

## 🚀 Features

* **Real-time streaming** of TfL bus arrival data and Tube line statuses via Kafka topics:

  * `tfl_bus_status`
  * `tfl_tube_status`
* **Producer services** poll TfL REST APIs at regular intervals (5 minutes) and publish JSON messages.
* **Consumer services** read from Kafka topics, print received records, and persist them to a shared SQLite database (`data/tfl.db`).
* **Dockerized** components for easy deployment using `docker-compose`.

---

## 🛠️ Tech Stack

* **Python** (3.9-slim)
* **Kafka** (Confluent CP-Kafka)
* **ZooKeeper** (Bitnami)
* **SQLite** (lightweight embedded database)
* **Docker / Docker Compose**

---

## 🐳 Quickstart with Docker Compose

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/tfl-status-streamer.git
   cd tfl-status-streamer
   ```

2. **Configure environment** (optional)

   * By default, services connect to Kafka at `kafka:9092` inside the Docker network.
   * To override broker address, set `KAFKA_BOOTSTRAP_SERVERS` in your shell or in an `.env` file.

3. **Start all services**

   ```bash
   docker-compose up -d
   ```

4. **Monitor logs**

   ```bash
   docker-compose logs -f tube_producer bus_producer tube_consumer bus_consumer
   ```

5. **Data persistence**

   * The SQLite file is persisted in `./data/tfl.db` on the host.
   * You can inspect the tables `tube_statuses` and `bus_arrivals` with any SQLite client.

6. **Stop and remove containers**

   ```bash
   docker-compose down
   ```

---

## ⚙️ Development Setup (Without Docker)

1. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run producers**

   * Tube producer:

     ```bash
     python kafka/producer.py
     ```
   * Bus producer:

     ```bash
     python kafka/bus_producer.py
     ```

4. **Run consumers**

   * Tube consumer:

     ```bash
     python kafka/consumer.py
     ```
   * Bus consumer:

     ```bash
     python kafka/bus_consumer.py
     ```

5. Ensure a local Kafka cluster is running and accessible at `localhost:9092`, and a ZooKeeper instance at `localhost:2181`.

---

## 📝 Database Schema

* **tube\_statuses**

  | Column     | Type    | Description                    |
  | ---------- | ------- | ------------------------------ |
  | id         | INTEGER | Auto-increment primary key     |
  | line\_name | TEXT    | Tube line name (e.g., Jubilee) |
  | severity   | INTEGER | Numeric severity level         |
  | timestamp  | TEXT    | ISO8601 timestamp of record    |

* **bus\_arrivals**

  | Column             | Type    | Description                          |
  | ------------------ | ------- | ------------------------------------ |
  | id                 | INTEGER | Auto-increment primary key           |
  | stop\_id           | TEXT    | Bus stop identifier                  |
  | route              | TEXT    | Bus route number/name                |
  | destination        | TEXT    | Destination name                     |
  | vehicle\_id        | TEXT    | Unique vehicle identifier            |
  | actual\_arrival    | TEXT    | ISO8601 actual arrival time          |
  | scheduled\_arrival | TEXT    | ISO8601 scheduled arrival time       |
  | delay\_minutes     | REAL    | Calculated delay in minutes          |
  | on\_time           | TEXT    | "true"/"false" indicator             |
  | timestamp          | TEXT    | ISO8601 timestamp of ingestion event |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/awesome-feature`).
3. Commit your changes (`git commit -m 'Add awesome feature'`).
4. Push to the branch (`git push origin feature/awesome-feature`).
5. Open a Pull Request.

Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on coding standards and the pull request process.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙋‍♂️ Support

If you encounter any issues or have questions, please open an issue on the GitHub repository or reach out to the maintainer.
