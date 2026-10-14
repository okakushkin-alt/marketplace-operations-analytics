-- 1. Основные показатели эффективности доставки

WITH delivered_orders AS (
    SELECT
        order_id,
        EXTRACT(
            EPOCH FROM (
                order_delivered_customer_date
                - order_estimated_delivery_date
            )
        ) / 86400.0 AS delay_days
    FROM raw.orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
)

SELECT
    COUNT(*) AS delivered_orders,

    COUNT(*) FILTER (
        WHERE delay_days <= 0
    ) AS on_time_orders,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE delay_days <= 0
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS on_time_pct,

    COUNT(*) FILTER (
        WHERE delay_days > 0
    ) AS late_orders,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE delay_days > 0
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS late_pct,

    ROUND(
        (AVG(delay_days) FILTER (
            WHERE delay_days > 0
        ))::numeric,
        2
    ) AS avg_delay_days,

    ROUND(
        (
            percentile_cont(0.5)
            WITHIN GROUP (ORDER BY delay_days)
            FILTER (WHERE delay_days > 0)
        )::numeric,
        2
    ) AS median_delay_days

FROM delivered_orders;