
-- 1. Заказы, для которых не найден покупатель
SELECT
    'Заказы без покупателя' AS check_name,
    COUNT(*) AS issue_count
FROM raw.orders o
LEFT JOIN raw.customers c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL

UNION ALL

-- 2. Товарные позиции без существующего заказа
SELECT
    'Позиции без заказа',
    COUNT(*)
FROM raw.order_items i
LEFT JOIN raw.orders o
    ON i.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

-- 3. Товарные позиции без существующего товара
SELECT
    'Позиции без товара',
    COUNT(*)
FROM raw.order_items i
LEFT JOIN raw.products p
    ON i.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL

-- 4. Товарные позиции без существующего продавца
SELECT
    'Позиции без продавца',
    COUNT(*)
FROM raw.order_items i
LEFT JOIN raw.sellers s
    ON i.seller_id = s.seller_id
WHERE s.seller_id IS NULL

UNION ALL

-- 5. Платежи без заказа
SELECT
    'Платежи без заказа',
    COUNT(*)
FROM raw.order_payments p
LEFT JOIN raw.orders o
    ON p.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

-- 6. Отзывы без заказа
SELECT
    'Отзывы без заказа',
    COUNT(*)
FROM raw.order_reviews r
LEFT JOIN raw.orders o
    ON r.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

-- 7. Доставленные заказы без фактической даты доставки
SELECT
    'Доставленные заказы без даты доставки',
    COUNT(*)
FROM raw.orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NULL

UNION ALL

-- 8. Дата доставки раньше даты оформления заказа
SELECT
    'Доставка раньше оформления',
    COUNT(*)
FROM raw.orders
WHERE order_delivered_customer_date IS NOT NULL
  AND order_purchase_timestamp IS NOT NULL
  AND order_delivered_customer_date < order_purchase_timestamp

UNION ALL

-- 9. Оценки отзывов вне диапазона 1–5
SELECT
    'Оценки вне диапазона 1–5',
    COUNT(*)
FROM raw.order_reviews
WHERE review_score NOT BETWEEN 1 AND 5
   OR review_score IS NULL

UNION ALL

-- 10. Нулевая или отрицательная стоимость товара
SELECT
    'Неположительная стоимость товара',
    COUNT(*)
FROM raw.order_items
WHERE price <= 0 OR price IS NULL

UNION ALL

-- 11. Отрицательная стоимость доставки
SELECT
    'Отрицательная стоимость доставки',
    COUNT(*)
FROM raw.order_items
WHERE freight_value < 0

UNION ALL

-- 12. Отрицательная сумма платежа
SELECT
    'Отрицательная сумма платежа',
    COUNT(*)
FROM raw.order_payments
WHERE payment_value < 0

ORDER BY check_name;
