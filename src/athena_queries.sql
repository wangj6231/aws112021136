-- =========================================================================
-- Amazon Athena SQL 建表與大數據交叉分析查詢 (已修正為相容 Athena 的雙引號)
-- 專案目標：台南永康交流道 (319K) 車流行為分析 (M06A 旅次資料)
-- =========================================================================

-- -------------------------------------------------------------------------
-- 0. 建立資料庫與外部資料表 (DDL)
-- -------------------------------------------------------------------------

-- 建立資料庫
CREATE DATABASE IF NOT EXISTS tdcs_db;

-- 建立永康交流道資料表
CREATE EXTERNAL TABLE IF NOT EXISTS tdcs_db.m06a_yongkang (
    vehicle_type string,
    direction_time_o string,
    gantry_id_o string,
    direction_time_d string,
    gantry_id_d string,
    trip_length double,
    trip_end string,
    trip_information string,
    direction string,
    travel_type string
)
PARTITIONED BY (date string)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://freeway-data-112021136/cleaned-yongkang/'
TBLPROPERTIES (
    "skip.header.line.count"="1"
);

-- 自動載入並修復 S3 的分區
MSCK REPAIR TABLE tdcs_db.m06a_yongkang;


-- -------------------------------------------------------------------------
-- 分析指標 1：車種交叉分析 (車流量與佔比)
-- -------------------------------------------------------------------------
SELECT 
    CASE vehicle_type
        WHEN '31' THEN '31-小客車'
        WHEN '32' THEN '32-小貨車'
        WHEN '41' THEN '41-大客車'
        WHEN '42' THEN '42-大貨車'
        WHEN '5'  THEN '5-聯結車'
        ELSE '未知車種'
    END AS "車種",
    COUNT(*) AS "總旅次量",
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tdcs_db.m06a_yongkang), 2) AS "車流百分比(%)",
    ROUND(AVG(trip_length), 2) AS "平均行駛距離(公里)"
FROM tdcs_db.m06a_yongkang
GROUP BY vehicle_type
ORDER BY vehicle_type;


-- -------------------------------------------------------------------------
-- 分析指標 2：每週車流變化與行為交叉分析 (上交流道、下交流道、直行)
-- -------------------------------------------------------------------------
WITH weekly_base AS (
    SELECT 
        date,
        -- 計算日期與 2026-03-01 的差距，以判定是第幾週
        (date_diff('day', DATE '2026-03-01', CAST(SUBSTR(date, 1, 4) || '-' || SUBSTR(date, 5, 2) || '-' || SUBSTR(date, 7, 2) AS DATE)) / 7) + 1 AS week_num,
        direction,
        CASE travel_type
            WHEN 'entering' THEN '上交流道'
            WHEN 'exiting' THEN '下交流道'
            WHEN 'passing' THEN '直行過境'
        END AS behavior
    FROM tdcs_db.m06a_yongkang
    WHERE date BETWEEN '20260426' AND '20260523'
)
SELECT 
    '第 ' || CAST(week_num AS VARCHAR) || ' 週' AS "分析週別",
    MIN(date) || ' ~ ' || MAX(date) AS "週日期範圍",
    COUNT(CASE WHEN behavior = '上交流道' THEN 1 END) AS "上交流道車流",
    COUNT(CASE WHEN behavior = '下交流道' THEN 1 END) AS "下交流道車流",
    COUNT(CASE WHEN behavior = '直行過境' THEN 1 END) AS "直行過境車流",
    COUNT(*) AS "總通過車流"
FROM weekly_base
GROUP BY week_num
ORDER BY week_num;


-- -------------------------------------------------------------------------
-- 分析指標 3：尖峰小時車流行為分析 (24小時熱力分佈)
-- -------------------------------------------------------------------------
WITH hourly_base AS (
    SELECT 
        CAST(SUBSTR(direction_time_o, 12, 2) AS INT) AS hour_of_day,
        direction,
        CASE travel_type
            WHEN 'entering' THEN '上交流道'
            WHEN 'exiting' THEN '下交流道'
            WHEN 'passing' THEN '直行過境'
        END AS behavior
    FROM tdcs_db.m06a_yongkang
)
SELECT 
    LPAD(CAST(hour_of_day AS VARCHAR), 2, '0') || ':00 ~ ' || LPAD(CAST(hour_of_day + 1 AS VARCHAR), 2, '0') || ':00' AS "時段",
    COUNT(CASE WHEN behavior = '上交流道' THEN 1 END) AS "上交流道量",
    COUNT(CASE WHEN behavior = '下交流道' THEN 1 END) AS "下交流道量",
    COUNT(CASE WHEN behavior = '直行過境' THEN 1 END) AS "主線直行量",
    COUNT(*) AS "總車流合計"
FROM hourly_base
GROUP BY hour_of_day
ORDER BY hour_of_day;


-- -------------------------------------------------------------------------
-- 分析指標 4：永康交流道起訖點 (O-D) 分析 - 尋找車流來源與目的地
-- -------------------------------------------------------------------------

-- 4.1：從永康上交流道 (Entering) 的車輛，最終都去哪裡？ (Top 10 出口門架)
SELECT 
    gantry_id_d AS "目的地終點門架",
    COUNT(*) AS "旅次量",
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS "比例(%)",
    ROUND(AVG(trip_length), 2) AS "平均行駛長度"
FROM tdcs_db.m06a_yongkang
WHERE travel_type = 'entering'
GROUP BY gantry_id_d
ORDER BY "旅次量" DESC
LIMIT 10;

-- 4.2：從永康下交流道 (Exiting) 的車輛，最初是從哪裡上國道的？ (Top 10 起點門架)
SELECT 
    gantry_id_o AS "出發起點門架",
    COUNT(*) AS "旅次量",
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS "比例(%)",
    ROUND(AVG(trip_length), 2) AS "平均行駛長度"
FROM tdcs_db.m06a_yongkang
WHERE travel_type = 'exiting'
GROUP BY gantry_id_o
ORDER BY "旅次量" DESC
LIMIT 10;


-- -------------------------------------------------------------------------
-- 專用大功能 5：導出「多維度車流資料庫 CSV」(專供互動式 Web 視覺化工作台對接使用)
-- -------------------------------------------------------------------------
-- 執行此 SQL 查詢，將結果「下載為 CSV」並命名為 database.csv。
-- 將該 CSV 檔案直接拖入網頁，即可瞬間解鎖 28 天所有日期、車種、方向、上/下/直行行為的無限交叉查詢！
SELECT 
    date AS "date",
    vehicle_type AS "vehicle_type",
    direction AS "direction",
    travel_type AS "travel_type",
    CAST(SUBSTR(direction_time_o, 12, 2) AS INT) AS "hour_of_day",
    COUNT(*) AS "trip_count",
    ROUND(AVG(trip_length), 2) AS "avg_trip_length"
FROM tdcs_db.m06a_yongkang
WHERE date BETWEEN '20260426' AND '20260523'
GROUP BY date, vehicle_type, direction, travel_type, CAST(SUBSTR(direction_time_o, 12, 2) AS INT)
ORDER BY date, vehicle_type, direction, travel_type, hour_of_day;
