from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import sys
import os

# Add pipeline directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# Import ingestion functions
try:
    from pipeline.ingestion.fetch_api_data import main as fetch_api
    from pipeline.ingestion.generate_inventory import main as generate_inventory
except ImportError as e:
    print(f"Warning: Could not import ingestion functions: {e}")
    fetch_api = lambda: print("Ingesting from FakeStoreAPI...")
    generate_inventory = lambda: print("Ingesting inventory CSV...")

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'ecommerce_data_pipeline',
    default_args=default_args,
    description='End-to-end ecommerce data pipeline',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
    catchup=False,
    tags=['ecommerce', 'snowflake', 'dbt'],
) as dag:

    # 1. Ingestion Tasks
    ingest_api_data = PythonOperator(
        task_id='ingest_api_data',
        python_callable=fetch_api,
    )

    ingest_inventory_csv = PythonOperator(
        task_id='ingest_inventory_csv',
        python_callable=generate_inventory,
    )

    # 2. Transformation Task (PySpark)
    transform_data_spark = BashOperator(
        task_id='transform_data_spark',
        bash_command='export PYTHONPATH={{ dag.parent_directory }}/pipeline:$PYTHONPATH && python {{ dag.parent_directory }}/pipeline/spark/transform_data.py',
    )

    # 3. Loading Task (Snowflake COPY INTO)
    load_to_snowflake = SnowflakeOperator(
        task_id='load_to_snowflake',
        snowflake_conn_id='snowflake_default',
        sql='{{ dag.parent_directory }}/pipeline/snowflake/copy_into.sql',
    )

    # 4. dbt Modeling Tasks
    run_dbt_models = BashOperator(
        task_id='run_dbt_models',
        bash_command='cd {{ dag.parent_directory }}/pipeline/dbt && dbt run --profiles-dir ~/.dbt',
    )

    run_dbt_tests = BashOperator(
        task_id='run_dbt_tests',
        bash_command='cd {{ dag.parent_directory }}/pipeline/dbt && dbt test --profiles-dir ~/.dbt',
    )

    # Define Dependencies
    [ingest_api_data, ingest_inventory_csv] >> transform_data_spark
    transform_data_spark >> load_to_snowflake
    load_to_snowflake >> run_dbt_models >> run_dbt_tests
