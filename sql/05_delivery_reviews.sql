-- Связь своевременности доставки с оценками покупателей

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

-- Одна строка на заказ, чтобы не задвоить заказы
reviews_by_order AS (
    SELECT
        order_id,
        AVG(review_score::numeric) AS avg_review_score
    FROM raw.order_reviews
    GROUP BY order_id
),

delivery_reviews AS (
    SELECT
        d.order_id,
        d.delivery_status,
        r.avg_review_score
    FROM delivered_orders d
    JOIN reviews_by_order r
        ON d.order_id = r.order_id
)

SELECT
    delivery_status,
    COUNT(*) AS orders_with_reviews,
    ROUND(AVG(avg_review_score), 2) AS avg_review_score,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE avg_review_score <= 2
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS low_rating_orders_pct
FROM delivery_reviews
GROUP BY delivery_status
ORDER BY
    CASE
        WHEN delivery_status = 'В срок или раньше' THEN 1
        ELSE 2
    END;