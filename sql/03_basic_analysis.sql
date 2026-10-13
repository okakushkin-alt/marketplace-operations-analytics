
-- 1. Количество заказов по месяцам
SELECT
    DATE_TRUNC('month', order_purchase_timestamp)::date AS month,
    COUNT(*) AS orders_count
FROM raw.orders
GROUP BY 1
ORDER BY 1;


-- 2. Распределение заказов по статусам
SELECT
    order_status,
    COUNT(*) AS orders_count
FROM raw.orders
GROUP BY order_status
ORDER BY orders_count DESC;


-- 3. Топ-10 категорий по сумме стоимости товаров
SELECT
    COALESCE(
        t.product_category_name_english,
        p.product_category_name,
        'Неизвестная категория'
    ) AS category,
    ROUND(SUM(i.price), 2) AS item_revenue,
    COUNT(DISTINCT i.order_id) AS orders_count
FROM raw.order_items i
JOIN raw.products p
    ON i.product_id = p.product_id
LEFT JOIN raw.category_translation t
    ON p.product_category_name = t.product_category_name
GROUP BY 1
ORDER BY item_revenue DESC
LIMIT 10;
