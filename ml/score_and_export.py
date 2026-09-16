"""
Loads the trained Random Forest model, scores every block, and writes
(block_id, true_label, predicted_label, probability_anomaly) to Postgres.
The FastAPI backend's /anomalies endpoint reads from this table rather
than loading Spark/the model itself - keeps the API lightweight.

Run inside spark-master (needs the Postgres JDBC driver):
    docker exec -it spark-master /spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --packages org.postgresql:postgresql:42.6.0 \
        /project/ml/score_and_export.py
"""

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassificationModel
from pyspark.ml.functions import vector_to_array


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--hdfs-uri", default="hdfs://namenode:8020")
    p.add_argument("--features-path", default="/ml/features/block_features")
    p.add_argument("--model-path", default="/ml/models/random_forest")
    p.add_argument("--pg-host", default="app-postgres")
    p.add_argument("--pg-port", default="5432")
    p.add_argument("--pg-db", default="logplatform")
    p.add_argument("--pg-user", default="appuser")
    p.add_argument("--pg-password", default="apppass")
    p.add_argument("--pg-table", default="block_anomaly_predictions")
    return p.parse_args()


def main():
    args = parse_args()
    features_full_path = args.hdfs_uri.rstrip("/") + args.features_path
    model_full_path = args.hdfs_uri.rstrip("/") + args.model_path

    spark = SparkSession.builder.appName("ScoreAndExport").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    df = spark.read.parquet(features_full_path)
    event_cols = [c for c in df.columns if c.startswith("E") and c[1:].isdigit()]

    assembler = VectorAssembler(inputCols=event_cols, outputCol="features")
    assembled = assembler.transform(df).select("BlockId", "features", "is_anomaly")

    model = RandomForestClassificationModel.load(model_full_path)
    predictions = model.transform(assembled)

    result = (
        predictions
        .withColumn("probability_arr", vector_to_array("probability"))
        .select(
            F.col("BlockId").alias("block_id"),
            F.col("is_anomaly").cast("int").alias("true_label"),
            F.col("prediction").cast("int").alias("predicted_label"),
            F.col("probability_arr")[1].alias("probability_anomaly"),
        )
        .withColumn("scored_at", F.current_timestamp())
    )

    jdbc_url = f"jdbc:postgresql://{args.pg_host}:{args.pg_port}/{args.pg_db}"
    print(f"Writing {result.count()} predictions to {jdbc_url}/{args.pg_table}")

    (
        result.write
        .format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", args.pg_table)
        .option("user", args.pg_user)
        .option("password", args.pg_password)
        .option("driver", "org.postgresql.Driver")
        .mode("overwrite")
        .save()
    )

    print("Done.")
    spark.stop()


if __name__ == "__main__":
    main()