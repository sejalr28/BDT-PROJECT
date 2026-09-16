"""
Consumes the same Kafka topic as the Spark job (separate consumer group,
so it doesn't compete for partitions/offsets) and bulk-indexes parsed
events into Elasticsearch for fast search and Kibana dashboards.

This runs as a plain Python process on the host - it only needs
localhost:9092 (Kafka) and localhost:9200 (Elasticsearch), both already
exposed by docker-compose.

Usage:
    python es_indexer.py
    python es_indexer.py --from-beginning   # reprocess the whole topic
"""

import argparse
import sys
import time
from pathlib import Path

from kafka import KafkaConsumer
from elasticsearch import Elasticsearch, helpers

# Import the shared parser from ../common
sys.path.append(str(Path(__file__).resolve().parent.parent / "common"))
from log_parser import parse_line  # noqa: E402

INDEX_NAME = "hdfs-logs-parsed"


def ensure_index(es: Elasticsearch):
    if es.indices.exists(index=INDEX_NAME):
        return
    es.indices.create(
        index=INDEX_NAME,
        mappings={
            "properties": {
                "raw_line": {"type": "text"},
                "date": {"type": "keyword"},
                "time": {"type": "keyword"},
                "pid": {"type": "keyword"},
                "level": {"type": "keyword"},
                "component": {"type": "keyword"},
                "content": {"type": "text"},
                "event_id": {"type": "keyword"},
                "block_id": {"type": "keyword"},
                "parse_success": {"type": "boolean"},
                "indexed_at": {"type": "date"},
            }
        },
    )
    print(f"Created index '{INDEX_NAME}'")


def bulk_index(es: Elasticsearch, docs: list) -> None:
    actions = [{"_index": INDEX_NAME, "_source": doc} for doc in docs]
    success, errors = helpers.bulk(es, actions, raise_on_error=False)
    if errors:
        print(f"[WARN] {len(errors)} documents failed to index", file=sys.stderr)


def run(bootstrap_servers: str, topic: str, es_url: str, from_beginning: bool, batch_size: int):
    es = Elasticsearch(es_url)
    ensure_index(es)

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id="es-indexer",
        auto_offset_reset="earliest" if from_beginning else "latest",
        enable_auto_commit=True,
        api_version=(2, 5, 0),
        value_deserializer=lambda v: v.decode("utf-8"),
    )

    print(f"Indexing '{topic}' -> Elasticsearch index '{INDEX_NAME}' ({es_url})")

    buffer = []
    indexed_total = 0
    last_flush = time.time()

    try:
        for message in consumer:
            doc = parse_line(message.value)
            doc["indexed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            buffer.append(doc)

            if len(buffer) >= batch_size or (time.time() - last_flush) > 5:
                bulk_index(es, buffer)
                indexed_total += len(buffer)
                print(f"  indexed_total={indexed_total}")
                buffer = []
                last_flush = time.time()

    except KeyboardInterrupt:
        print("\nInterrupted, flushing remaining buffer...")
    finally:
        if buffer:
            bulk_index(es, buffer)
            indexed_total += len(buffer)
        consumer.close()
        print(f"Done. indexed_total={indexed_total}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap-servers", default="localhost:9092")
    p.add_argument("--topic", default="hdfs-logs")
    p.add_argument("--es-url", default="http://localhost:9200")
    p.add_argument("--from-beginning", action="store_true")
    p.add_argument("--batch-size", type=int, default=500)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        es_url=args.es_url,
        from_beginning=args.from_beginning,
        batch_size=args.batch_size,
    )