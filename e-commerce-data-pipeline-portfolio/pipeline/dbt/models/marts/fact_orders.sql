-- models/marts/fact_orders.sql
WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }} -- Assume stg_products exists
),

final AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.order_date,
        o.product_id,
        o.quantity,
        p.price,
        p.category,
        (o.quantity * p.price) AS total_revenue
    FROM orders o
    LEFT JOIN products p ON o.product_id = p.product_id
)

SELECT * FROM final
