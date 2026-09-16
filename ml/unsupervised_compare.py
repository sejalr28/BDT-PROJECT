"""
Unsupervised comparison: does Isolation Forest or K-Means clustering
surface the same anomalies as the supervised Random Forest, WITHOUT
being given the true labels during training? Labels are only used
afterward, to score how well each unsupervised method lines up with
ground truth.

Runs as a plain Python script on the host (small dataset, no need for
Spark here) - reads the two source CSVs directly.

Usage:
    python unsupervised_compare.py
"""

import argparse

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--occurrence-matrix", default="../data/raw/Event_occurrence_matrix.csv")
    p.add_argument("--anomaly-labels", default="../data/raw/anomaly_label.csv")
    p.add_argument(
        "--contamination",
        type=float,
        default=0.03,
        help="Expected fraction of anomalies, passed to Isolation Forest",
    )
    p.add_argument("--n-clusters", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def load_features(occurrence_path: str, labels_path: str):
    occurrence = pd.read_csv(occurrence_path)
    labels = pd.read_csv(labels_path)

    event_cols = [c for c in occurrence.columns if c.startswith("E") and c[1:].isdigit()]
    merged = occurrence[["BlockId"] + event_cols].merge(labels, on="BlockId", how="inner")
    merged["is_anomaly"] = (merged["Label"] == "Anomaly").astype(int)

    X = merged[event_cols].values
    y = merged["is_anomaly"].values
    return X, y, merged


def report(name: str, y_true, y_pred):
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred)

    print(f"\n=== {name} vs. true labels ===")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1:        {f1:.4f}")
    print(f"Confusion matrix [[TN, FP], [FN, TP]]:\n{cm}")


def run_isolation_forest(X, y, contamination: float, seed: int):
    model = IsolationForest(contamination=contamination, random_state=seed)
    raw_pred = model.fit_predict(X)  # -1 = anomaly, 1 = normal
    y_pred = (raw_pred == -1).astype(int)
    report("Isolation Forest", y, y_pred)


def run_kmeans(X, y, n_clusters: int, seed: int):
    X_scaled = StandardScaler().fit_transform(X)
    model = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    cluster_assignments = model.fit_predict(X_scaled)

    # K-Means has no notion of "anomaly" - we treat whichever cluster is
    # smaller as the "anomaly" cluster, since anomalies are the minority
    # class here, then score against the true labels for comparison.
    counts = pd.Series(cluster_assignments).value_counts()
    minority_cluster = counts.idxmin()
    y_pred = (cluster_assignments == minority_cluster).astype(int)

    print(f"\nCluster sizes: {dict(counts)}")
    print(f"Treating cluster {minority_cluster} (smaller) as the 'anomaly' cluster")
    report("K-Means (minority cluster)", y, y_pred)


def main():
    args = parse_args()
    X, y, merged = load_features(args.occurrence_matrix, args.anomaly_labels)

    total = len(y)
    anomalies = int(y.sum())
    print(f"Total blocks: {total}")
    print(f"True anomalies: {anomalies} ({100 * anomalies / total:.2f}%)")

    run_isolation_forest(X, y, args.contamination, args.seed)
    run_kmeans(X, y, args.n_clusters, args.seed)


if __name__ == "__main__":
    main()