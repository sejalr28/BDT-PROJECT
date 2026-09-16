"""
Trains a Random Forest classifier (Spark MLlib) on the block feature
table to predict Normal vs Anomaly, and reports precision/recall/F1/AUC.

Note: this dataset is heavily imbalanced (anomalies are a small minority
of blocks), so accuracy alone would be misleading - that's why we report
precision/recall/F1 and AUC rather than just accuracy.

Run inside spark-master:
    docker exec -it spark-master /spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        /project/ml/train_random_forest.py
"""

import argparse

from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import (
    BinaryClassificationEvaluator,
    MulticlassClassificationEvaluator,
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--hdfs-uri", default="hdfs://namenode:8020")
    p.add_argument("--features-path", default="/ml/features/block_features")
    p.add_argument("--model-output", default="/ml/models/random_forest")
    p.add_argument("--num-trees", type=int, default=100)
    p.add_argument("--max-depth", type=int, default=8)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main():
    args = parse_args()
    features_full_path = args.hdfs_uri.rstrip("/") + args.features_path
    model_full_path = args.hdfs_uri.rstrip("/") + args.model_output

    spark = SparkSession.builder.appName("RandomForestAnomalyDetector").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    df = spark.read.parquet(features_full_path)
    event_cols = [c for c in df.columns if c.startswith("E") and c[1:].isdigit()]

    assembler = VectorAssembler(inputCols=event_cols, outputCol="features")
    assembled = assembler.transform(df).select("BlockId", "features", "is_anomaly")

    train_df, test_df = assembled.randomSplit([0.8, 0.2], seed=args.seed)
    print(f"Train rows: {train_df.count()}  Test rows: {test_df.count()}")

    rf = RandomForestClassifier(
        featuresCol="features",
        labelCol="is_anomaly",
        numTrees=args.num_trees,
        maxDepth=args.max_depth,
        seed=args.seed,
    )
    model = rf.fit(train_df)
    predictions = model.transform(test_df)

    auc_evaluator = BinaryClassificationEvaluator(
        labelCol="is_anomaly", rawPredictionCol="rawPrediction", metricName="areaUnderROC"
    )
    auc = auc_evaluator.evaluate(predictions)

    metrics = {}
    for metric in ["accuracy", "weightedPrecision", "weightedRecall", "f1"]:
        evaluator = MulticlassClassificationEvaluator(
            labelCol="is_anomaly", predictionCol="prediction", metricName=metric
        )
        metrics[metric] = evaluator.evaluate(predictions)

    # Precision/recall specifically for the anomaly class (label=1) - this
    # is the number that actually matters given the class imbalance.
    tp = predictions.filter("is_anomaly = 1.0 AND prediction = 1.0").count()
    fp = predictions.filter("is_anomaly = 0.0 AND prediction = 1.0").count()
    fn = predictions.filter("is_anomaly = 1.0 AND prediction = 0.0").count()
    precision_anomaly = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall_anomaly = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    print("\n=== Overall metrics (test set) ===")
    print(f"AUC:                {auc:.4f}")
    print(f"Accuracy:           {metrics['accuracy']:.4f}")
    print(f"Weighted Precision: {metrics['weightedPrecision']:.4f}")
    print(f"Weighted Recall:    {metrics['weightedRecall']:.4f}")
    print(f"F1:                 {metrics['f1']:.4f}")

    print("\n=== Anomaly-class metrics (the ones that actually matter here) ===")
    print(f"True Positives:  {tp}")
    print(f"False Positives: {fp}")
    print(f"False Negatives: {fn}")
    print(f"Precision (anomaly): {precision_anomaly:.4f}")
    print(f"Recall (anomaly):    {recall_anomaly:.4f}")

    print("\n=== Feature importances ===")
    for col, importance in sorted(
        zip(event_cols, model.featureImportances.toArray()), key=lambda x: -x[1]
    )[:10]:
        print(f"  {col}: {importance:.4f}")

    model.write().overwrite().save(model_full_path)
    print(f"\nModel saved to {model_full_path}")

    spark.stop()


if __name__ == "__main__":
    main()