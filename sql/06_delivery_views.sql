CREATE SCHEMA IF NOT EXISTS analytics;


-- 1. Показатели своевременности доставки
CREATE OR REPLACE VIEW analytics.delivery_metrics AS
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
        AVG(delay_days) FILTER (
            WHERE delay_days > 0
        )::numeric,
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


-- 2. Своевременность доставки и отзывы покупателей
CREATE OR REPLACE VIEW analytics.delivery_reviews AS
WITH delivered_orders AS (
    SELECT
        order_id,
        CASE
            WHEN order_delivered_customer_date
                 <= order_estimated_delivery_date
            THEN 'В срок или раньше'
            ELSE 'С опозданием'
        END AS delivery_status
    FROM raw.orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
),
reviews_by_order AS (
    SELECT
        order_id,
        AVG(review_score::numeric) AS avg_review_score
    FROM raw.order_reviews
    GROUP BY order_id
)
SELECT
    d.delivery_status,
    COUNT(*) AS orders_with_reviews,
    ROUND(AVG(r.avg_review_score), 2) AS avg_review_score,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE r.avg_review_score <= 2
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS low_rating_orders_pct
FROM delivered_orders d
JOIN reviews_by_order r
    ON d.order_id = r.order_id
GROUP BY d.delivery_status;