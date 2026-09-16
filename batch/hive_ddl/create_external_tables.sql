-- Run with:
--   docker exec -it hive-server hive -f /project/batch/hive_ddl/create_external_tables.sql

CREATE DATABASE IF NOT EXISTS logdb;

USE logdb;

-- External table over the Parquet files Spark Structured Streaming has
-- been writing to hdfs:///logs/parsed. No data is copied - Hive just
-- reads whatever Parquet files are currently in that directory.
-- NOTE: Hive 2.x's Parquet SerDe matches columns by ORDER, not name, so
-- the column order below must match the Parquet schema written by
-- spark_streaming_job.py exactly (raw_line, date, time, pid, level,
-- component, content, event_id, block_id, parse_success). Renamed
-- date/time to log_date/log_time here only to sidestep any ambiguity
-- with Hive's DATE type keyword - the underlying data is unaffected.
CREATE EXTERNAL TABLE IF NOT EXISTS parsed_logs (
    raw_line       STRING,
    log_date       STRING,   -- yyMMdd, e.g. 081109
    log_time       STRING,   -- HHmmss, e.g. 203615
    pid            STRING,
    level          STRING,   -- INFO / WARN / ERROR
    component      STRING,
    content        STRING,
    event_id       STRING,   -- E1..E29, or UNKNOWN if unmatched
    block_id       STRING,   -- blk_..., null if not a block-related line
    parse_success  BOOLEAN
)
STORED AS PARQUET
LOCATION 'hdfs://namenode:8020/logs/parsed';

-- Sanity check
SELECT COUNT(*) AS total_rows FROM parsed_logs;