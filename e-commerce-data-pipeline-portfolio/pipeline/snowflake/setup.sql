-- Snowflake Setup Script
-- Run as ACCOUNTADMIN or a role with sufficient privileges

-- 1. Create Warehouse
CREATE OR REPLACE WAREHOUSE ECOM_WH 
WITH WAREHOUSE_SIZE = 'XSMALL' 
AUTO_SUSPEND = 120 
AUTO_RESUME = TRUE 
INITIALLY_SUSPENDED = TRUE;

-- 2. Create Database and Schemas
CREATE OR REPLACE DATABASE ECOM_DB;
CREATE OR REPLACE SCHEMA ECOM_DB.RAW;
CREATE OR REPLACE SCHEMA ECOM_DB.STAGING;
CREATE OR REPLACE SCHEMA ECOM_DB.ANALYTICS;

-- 3. Create External Stage (S3)
-- Replace with your actual S3 credentials/IAM Role
CREATE OR REPLACE STAGE ECOM_DB.RAW.S3_PROCESSED_STAGE
URL = 's3://my-ecommerce-processed-zone/'
CREDENTIALS = (AWS_KEY_ID = 'XXXX' AWS_SECRET_KEY = 'XXXX');

-- 4. Create Raw Tables for COPY INTO
CREATE OR REPLACE TABLE ECOM_DB.RAW.ORDERS_RAW (
    order_id INTEGER,
    customer_id INTEGER,
    order_date DATE,
    product_id INTEGER,
    quantity INTEGER,
    processed_at TIMESTAMP_NTZ
);

CREATE OR REPLACE TABLE ECOM_DB.RAW.INVENTORY_RAW (
    product_id INTEGER,
    supplier_id INTEGER,
    stock_quantity INTEGER,
    restock_threshold INTEGER,
    last_updated TIMESTAMP_NTZ
);
