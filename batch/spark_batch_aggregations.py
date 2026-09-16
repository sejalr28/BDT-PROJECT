"""
Batch aggregations over the Spark-Streaming-written Parquet logs, using
the DataFrame API directly (no Hive dependency - reads Parquet straight
off HDFS). Demonstrates the "batch analytics" side of Spark separately
from the streaming job in Phase 2.

Run inside spark-master:
    docker exec -it spark-master spark-submit \
        --master spark://spark-master:7077 \
        /project/batch/spark_batch_aggregations.py
"""

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--hdfs-uri", default="hdfs://namenode:8020")
    p.add_argument("--input-path", default="/logs/parsed")
    return p.parse_args()


def main():
    args = parse_args()
    input_full_path = args.hdfs_uri.rstrip("/") + args.input_path

    spark = SparkSession.builder.appName("LogBatchAggregations").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    df = spark.read.parquet(input_full_path)
    df.cache()

    total = df.count()
    print(f"\nTotal parsed rows: {total}\n")

    print("=== Log volume by level ===")
    df.groupBy("level").count().orderBy(F.desc("count")).show()

    print("=== Warn/Error counts by hour of day ===")
    (
        df.filter(F.col("level").isin("WARN", "ERROR"))
        .withColumn("hour_of_day", F.substring("time", 1, 2))
        .groupBy("hour_of_day")
        .count()
        .orderBy("hour_of_day")
        .show(24)
    )

    print("=== Top 10 event templates ===")
    df.groupBy("event_id").count().orderBy(F.desc("count")).show(10)

    print("=== Top 20 busiest blocks ===")
    (
        df.filter(F.col("block_id").isNotNull())
        .groupBy("block_id")
        .count()
        .orderBy(F.desc("count"))
        .show(20, truncate=False)
    )

    print("=== Unparsed line count (sanity check) ===")
    unparsed = df.filter(F.col("parse_success") == False).count()  # noqa: E712
    print(f"unparsed_count = {unparsed}")

    spark.stop()


if __name__ == "__main__":
    main()