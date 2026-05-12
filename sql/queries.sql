-- 1. On-time rate по перевозчикам
SELECT 
   carrier, 
   COUNT(*) AS total, 
   ROUND(SUM(CASE 
   	WHEN delay_days <= 0 
  	THEN 1 
	ELSE 0 END)*100.0/COUNT(*),1) AS on_time_pct
FROM deliveries 
WHERE delivered = 1 
GROUP BY 1 
ORDER BY 3 DESC;

-- 2. Задержка по дистанции и дню недели
SELECT 
  CASE 
  	WHEN distance_km < 100 
	THEN '0-100' 
	WHEN distance_km < 300 
	THEN '100-300' 
	ELSE '300+' END AS dist,
  strftime('%w', order_date) AS dow, 
  ROUND(AVG(delay_days),1) AS avg_delay
FROM deliveries 
WHERE 
	delivered=1 AND 
	delay_days IS NOT NULL 
GROUP BY 1,2 
ORDER BY 3 DESC;

-- 3. Сезонность заказов
SELECT 
strftime('%Y-W%W', order_date) AS week, 
COUNT(*) AS orders, 
ROUND(AVG(freight_cost),2) AS avg_cost
FROM deliveries 
GROUP BY 1 
ORDER BY 1;

-- 4. Проблемные маршруты (топ-10 по задержке)
SELECT 
	warehouse_id, 
	destination_city, 
	COUNT(*) AS cnt, 
	ROUND(AVG(delay_days),1) AS avg_delay
FROM deliveries 
WHERE 
	delivered=1 AND 
	delay_days IS NOT NULL 
GROUP BY 1,2 
HAVING cnt>=50 
ORDER BY 4 DESC 
LIMIT 10;