"""
Reads raw log lines from Kafka, parses each one against the HDFS event
templates, and writes the structured result to HDFS as Parquet.

Run this INSIDE the spark-master container (it needs to resolve the
`kafka` and `namenode` service names on the Docker network):

    docker exec -it spark-master spark-submit \
        --master spark://spark-master:7077 \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0 \
        --py-files /project/common/log_parser.py \
        /project/streaming/spark_streaming_job.py

Optional args: --kafka-bootstrap, --topic, --hdfs-uri, --output-path,
--checkpoint-path (see parse_args below for defaults).
"""

import argparse

from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StructType, StructField, StringType, BooleanType

from log_parser import parse_line

PARSED_SCHEMA = StructType([
    StructField("raw_line", StringType()),
    StructField("date", StringType()),
    StructField("time", StringType()),
    StructField("pid", StringType()),
    StructField("level", StringType()),
    StructField("component", StringType()),
    StructField("content", StringType()),
    StructField("event_id", StringType()),
    StructField("block_id", StringType()),
    StructField("parse_success", BooleanType()),
])


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--kafka-bootstrap", default="kafka:29092")
    p.add_argument("--topic", default="hdfs-logs")
    p.add_argument("--hdfs-uri", default="hdfs://namenode:8020")
    p.add_argument("--output-path", default="/logs/parsed")
    p.add_argument("--checkpoint-path", default="/logs/checkpoints/spark-streaming")
    p.add_argument(
        "--starting-offsets",
        default="earliest",
        help="'earliest' to reprocess everything already in the topic, 'latest' for new messages only",
    )
    return p.parse_args()


def main():
    args = parse_args()

    spark = (
        SparkSession.builder
        .appName("HDFSLogStreamParser")
        .config("spark.sql.streaming.schemaInference", "true")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    parse_udf = udf(parse_line, PARSED_SCHEMA)

    raw_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", args.kafka_bootstrap)
        .option("subscribe", args.topic)
        .option("startingOffsets", args.starting_offsets)
        .option("failOnDataLoss", "false")
        .load()
    )

    parsed = (
        raw_stream
        .selectExpr("CAST(value AS STRING) AS raw_line")
        .withColumn("parsed", parse_udf("raw_line"))
        .select("parsed.*")
    )

    output_full_path = args.hdfs_uri.rstrip("/") + args.output_path
    checkpoint_full_path = args.hdfs_uri.rstrip("/") + args.checkpoint_path

    query = (
        parsed.writeStream
        .format("parquet")
        .option("path", output_full_path)
        .option("checkpointLocation", checkpoint_full_path)
        .outputMode("append")
        .trigger(processingTime="10 seconds")
        .start()
    )

    print(f"Streaming started. Writing parsed logs to {output_full_path}")
    print(f"Checkpoint at {checkpoint_full_path}")
    query.awaitTermination()


if __name__ == "__main__":
    main()