-- models/staging/stg_orders.sql
WITH source AS (
    SELECT * FROM {{ source('raw', 'orders_raw') }}
),

renamed AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        product_id,
        quantity,
        processed_at AS ingestion_timestamp
    FROM source
)

SELECT * FROM renamed
