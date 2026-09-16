-- Run with:
--   docker exec -it hive-server hive -f /project/batch/queries/example_aggregations.sql

USE logdb;

-- 1. Log volume by level (how much INFO vs WARN vs ERROR)
SELECT level, COUNT(*) AS cnt
FROM parsed_logs
GROUP BY level
ORDER BY cnt DESC;

-- 2. Errors/warnings by hour of day (log_time is HHmmss, so first 2 chars = hour)
SELECT SUBSTR(log_time, 1, 2) AS hour_of_day, COUNT(*) AS warn_or_error_count
FROM parsed_logs
WHERE level IN ('WARN', 'ERROR')
GROUP BY SUBSTR(log_time, 1, 2)
ORDER BY hour_of_day;

-- 3. Top 10 most frequent event templates
SELECT event_id, COUNT(*) AS cnt
FROM parsed_logs
GROUP BY event_id
ORDER BY cnt DESC
LIMIT 10;

-- 4. Blocks with the most log events (busiest/most-touched blocks)
SELECT block_id, COUNT(*) AS event_count
FROM parsed_logs
WHERE block_id IS NOT NULL
GROUP BY block_id
ORDER BY event_count DESC
LIMIT 20;

-- 5. Lines that failed to parse (should be near-zero; useful sanity check)
SELECT COUNT(*) AS unparsed_count
FROM parsed_logs
WHERE parse_success = false;