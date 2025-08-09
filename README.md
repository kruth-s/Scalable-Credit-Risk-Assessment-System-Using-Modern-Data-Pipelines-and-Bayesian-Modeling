# Scalable Credit Risk Assessment System Using Modern Data Pipelines and Bayesian Modeling

## Overview

This project implements an end-to-end credit risk assessment system designed using modern data engineering principles and statistical modeling techniques. The system is capable of processing both batch and streaming financial data, applying probabilistic models for credit risk scoring, and serving insights through a real-time dashboard.

## Objectives

- Simulate loan application and behavioral data.
- Design and implement scalable data pipelines using Apache Airflow and Kafka.
- Store and query data using PostgreSQL and Delta Lake.
- Apply Bayesian inference and logistic regression for risk modeling.
- Visualize risk profiles using Streamlit.

## Architecture

The architecture follows a modular and scalable data pipeline:

1. **Data Simulation**: Generates historical and real-time user data.
2. **Data Ingestion**: Utilizes Kafka for streaming data and Airflow for batch ingestion.
3. **Data Storage**: Stores data in PostgreSQL and Delta Lake for analytics and ML processing.
4. **Risk Modeling**: Implements Bayesian inference and logistic regression.
5. **Dashboard**: Provides an interactive dashboard built with Streamlit for visualizing credit risk scores.


## Streaming in the Pipeline

Source Events (Producer) — Simulated customer activity (e.g., payment made, missed payment, credit usage spike) is emitted continuously.

Message Broker (Kafka) — Acts as a durable, scalable buffer that decouples event producers and consumers.

Stream Processor (Consumer) — Subscribes to Kafka topics, cleans/enriches events, updates risk scores (Bayesian or feature updates), and writes results to storage (Postgres / Delta / Redis).

Serving Layer / Dashboard — Reads latest risk scores from storage and visualizes them in Streamlit.

Batch Pipeline (Airflow) — Periodically ingests historical data (loan_applications.csv), retrains models, and backfills results. Streaming adds near real-time updates on top of batch insights.

## Directory Structure

```
credit-risk-assessment/
├── data/                 # Simulated datasets
├── ingestion/            # Ingestion scripts (Kafka, Airflow)
├── models/               # Bayesian and Logistic models
├── processing/           # Data transformation scripts
├── storage/              # Database and Delta Lake setup
├── dashboard/            # Streamlit dashboard code
├── reports/              # Documentation and diagrams
├── tests/                # Unit tests
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
```

## Technologies Used

- Python 3
- Apache Kafka
- Apache Airflow
- PostgreSQL
- Delta Lake
- Pandas, NumPy, SciPy, scikit-learn
- Streamlit

## Setup Instructions

1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure PostgreSQL and Kafka.
4. Run the Airflow DAG for batch ingestion.
5. Start the Kafka producer for streaming data.
6. Launch the Streamlit dashboard:
   ```bash
   streamlit run dashboard/app.py
   ```

## License

This project is licensed under the MIT License.