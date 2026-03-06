-- COPY INTO script for loading Parquet from S3
-- This script is typically executed by Airflow's SnowflakeOperator

-- Load Orders
COPY INTO ECOM_DB.RAW.ORDERS_RAW
FROM @ECOM_DB.RAW.S3_PROCESSED_STAGE/processed/orders/
FILE_FORMAT = (TYPE = 'PARQUET')
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Load Inventory
COPY INTO ECOM_DB.RAW.INVENTORY_RAW
FROM @ECOM_DB.RAW.S3_PROCESSED_STAGE/processed/inventory/
FILE_FORMAT = (TYPE = 'PARQUET')
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;
