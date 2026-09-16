"""
Builds the per-block feature table used for anomaly detection:
    Event_occurrence_matrix.csv (E1..E29 counts per block)
    JOIN
    anomaly_label.csv (true Normal/Anomaly label per block)
  -> hdfs:///ml/features/block_features (Parquet)

Run inside spark-master:
    docker exec -it spark-master /spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        /project/ml/feature_engineering.py
"""

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--occurrence-matrix", default="/project/data/raw/Event_occurrence_matrix.csv")
    p.add_argument("--anomaly-labels", default="/project/data/raw/anomaly_label.csv")
    p.add_argument("--hdfs-uri", default="hdfs://namenode:8020")
    p.add_argument("--output-path", default="/ml/features/block_features")
    return p.parse_args()


def main():
    args = parse_args()

    spark = SparkSession.builder.appName("FeatureEngineering").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    occurrence = spark.read.csv(args.occurrence_matrix, header=True, inferSchema=True)
    labels = spark.read.csv(args.anomaly_labels, header=True, inferSchema=True)

    event_cols = [c for c in occurrence.columns if c.startswith("E") and c[1:].isdigit()]
    print(f"Event feature columns: {event_cols}")

    # Drop the occurrence matrix's own Label/Type columns - anomaly_label.csv
    # is the authoritative target, so we join that in separately.
    features = occurrence.select(["BlockId"] + event_cols)

    labeled = (
        features.join(labels, on="BlockId", how="inner")
        .withColumn("is_anomaly", F.when(F.col("Label") == "Anomaly", 1.0).otherwise(0.0))
        .drop("Label")
    )

    total = labeled.count()
    anomalies = labeled.filter(F.col("is_anomaly") == 1.0).count()
    print(f"\nTotal labeled blocks: {total}")
    print(f"Anomalies: {anomalies} ({100 * anomalies / total:.2f}%)")
    print(f"Normal:    {total - anomalies} ({100 * (total - anomalies) / total:.2f}%)")

    output_full_path = args.hdfs_uri.rstrip("/") + args.output_path
    labeled.write.mode("overwrite").parquet(output_full_path)
    print(f"\nWrote feature table to {output_full_path}")

    spark.stop()


if __name__ == "__main__":
    main()