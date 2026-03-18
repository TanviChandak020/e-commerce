-- COPY INTO script for loading Parquet from S3
-- Load processed data from S3 into Snowflake raw tables

-- Create or use existing S3 integration (assumes it's already configured)
-- For this to work, S3 integration and stage must be configured in Snowflake

-- Load Orders from processed S3 location
COPY INTO ECOM_DB.RAW.ORDERS_RAW
FROM 's3://' || :s3_bucket || '/processed/orders/'
CREDENTIALS = (
  AWS_KEY_ID = :aws_key
  AWS_SECRET_KEY = :aws_secret
)
FILE_FORMAT = (TYPE = 'PARQUET')
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Load Products from processed S3 location  
COPY INTO ECOM_DB.RAW.PRODUCTS_RAW
FROM 's3://' || :s3_bucket || '/processed/products/'
CREDENTIALS = (
  AWS_KEY_ID = :aws_key
  AWS_SECRET_KEY = :aws_secret
)
FILE_FORMAT = (TYPE = 'PARQUET')
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;
