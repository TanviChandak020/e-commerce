from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

# Import ingestion functions (assuming they're in the same project)
# from ingestion.fetch_api_data import main as fetch_api
# from ingestion.generate_inventory import main as generate_inventory

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
        python_callable=lambda: print("Ingesting from FakeStoreAPI..."), # Replace with actual call
    )

    ingest_inventory_csv = PythonOperator(
        task_id='ingest_inventory_csv',
        python_callable=lambda: print("Ingesting inventory CSV..."), # Replace with actual call
    )

    # 2. Transformation Task (PySpark on EMR)
    transform_data_spark = EmrAddStepsOperator(
        task_id='transform_data_spark',
        job_flow_id='J-XXXXXXXXXXXX', # Replace with actual EMR Cluster ID
        steps=[{
            'Name': 'PySpark Transformation',
            'ActionOnFailure': 'CONTINUE',
            'HadoopJarStep': {
                'Jar': 'command-runner.jar',
                'Args': ['spark-submit', 's3://my-bucket/scripts/transform_data.py'],
            },
        }],
    )

    # 3. Loading Task (Snowflake COPY INTO)
    load_to_snowflake = SnowflakeOperator(
        task_id='load_to_snowflake',
        snowflake_conn_id='snowflake_default',
        sql='pipeline/snowflake/copy_into.sql',
    )

    # 4. dbt Modeling Tasks
    # Typically run via BashOperator or DbtCloudRunJobOperator
    run_dbt_models = PythonOperator(
        task_id='run_dbt_models',
        python_callable=lambda: print("Running dbt models..."),
    )

    run_dbt_tests = PythonOperator(
        task_id='run_dbt_tests',
        python_callable=lambda: print("Running dbt tests..."),
    )

    # Define Dependencies
    [ingest_api_data, ingest_inventory_csv] >> transform_data_spark
    transform_data_spark >> load_to_snowflake
    load_to_snowflake >> run_dbt_models >> run_dbt_tests
