# End-to-End E-Commerce Data Pipeline

This repository contains a production-grade data engineering pipeline that ingests, transforms, and models e-commerce data using a modern data stack.

## Architecture Overview

The pipeline follows a Medallion-style architecture:
1.  **Raw Zone (S3)**: Ingestion of JSON from REST APIs and CSV from inventory feeds.
2.  **Processed Zone (S3)**: PySpark transformations (cleaning, flattening, schema enforcement) saved as Parquet.
3.  **Warehouse (Snowflake)**: Data loaded via `COPY INTO` commands.
4.  **Analytics Layer (dbt)**: Dimensional modeling (Star Schema) and business logic.
5.  **Orchestration (Airflow)**: End-to-end workflow management.

## Tech Stack
- **Python**: Ingestion scripts (Requests, Pandas).
- **AWS S3**: Scalable object storage for raw and processed data.
- **PySpark**: Distributed data processing for large-scale transformations.
- **Snowflake**: Cloud data warehouse for high-performance analytics.
- **dbt (data build tool)**: SQL-based modeling and testing.
- **Apache Airflow**: Workflow orchestration.

## Project Structure
```text
pipeline/
├── airflow/            # Airflow DAGs and configuration
├── dbt/                # dbt project, models, and tests
├── ingestion/          # Python ingestion scripts
├── snowflake/          # SQL setup and loading scripts
└── spark/              # PySpark transformation jobs
```

## Setup Instructions

### 1. AWS Configuration
- Create two S3 buckets: `raw-zone` and `processed-zone`.
- Configure IAM users with S3 and EMR access.

### 2. Snowflake Setup
- Run the scripts in `pipeline/snowflake/setup.sql` to initialize the warehouse, database, and stages.

### 3. dbt Configuration
- Install dbt: `pip install dbt-snowflake`
- Configure your `profiles.yml` with Snowflake credentials.
- Run `dbt deps` and `dbt run`.

### 4. Airflow Setup
- Use Astro CLI: `astro dev start`
- Place the DAG in the `dags/` folder.
- Configure connections for `snowflake_default` and `aws_default` in the Airflow UI.

## Analytical Output Goals
- **Revenue by Category**: Weekly trends calculated in `fact_orders`.
- **Stockout Risk**: Identified by joining `fact_inventory` with sales velocity.
- **Customer LTV**: Top customers ranked by total spend.
- **Fulfillment Delay**: Trends analyzed via order timestamps.
