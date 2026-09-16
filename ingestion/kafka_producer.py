"""
Replays a log file into a Kafka topic, line by line, simulating
real-time log arrival from servers/applications.

Usage examples:
    # Dev run: send only the first 50,000 lines, small delay between sends
    python kafka_producer.py --file ../data/raw/HDFS.log --limit 50000

    # Full replay, no artificial delay (as fast as Kafka will accept)
    python kafka_producer.py --file ../data/raw/HDFS.log --delay 0

    # Full replay, throttled to roughly simulate real traffic
    python kafka_producer.py --file ../data/raw/HDFS.log --delay 0.002
"""

import argparse
import sys
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError


def build_producer(bootstrap_servers: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: v.encode("utf-8"),
        linger_ms=20,       # small batching window for throughput
        acks=1,             # leader ack is enough for a coursework pipeline
        retries=3,
        api_version=(2, 5, 0),  # skip broker auto-detection (unreliable here)
    )


def replay_file(
    file_path: str,
    topic: str,
    bootstrap_servers: str,
    limit: int | None,
    delay: float,
    report_every: int,
) -> None:
    producer = build_producer(bootstrap_servers)

    sent = 0
    failed = 0
    start = time.time()

    print(f"Producing to topic '{topic}' via {bootstrap_servers}")
    print(f"Source file: {file_path}")
    if limit:
        print(f"Limiting to first {limit} lines")
    print(f"Per-message delay: {delay}s\n")

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f, start=1):
                if limit and line_no > limit:
                    break

                line = line.rstrip("\n")
                if not line:
                    continue

                try:
                    producer.send(topic, value=line)
                    sent += 1
                except KafkaError as e:
                    failed += 1
                    print(f"[WARN] failed to send line {line_no}: {e}", file=sys.stderr)

                if sent % report_every == 0 and sent > 0:
                    elapsed = time.time() - start
                    rate = sent / elapsed if elapsed > 0 else 0
                    print(f"  sent={sent:>8}  failed={failed:>4}  rate={rate:,.0f} msg/s")

                if delay > 0:
                    time.sleep(delay)

    except FileNotFoundError:
        print(f"[ERROR] file not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user, flushing remaining messages...")
    finally:
        producer.flush(timeout=30)
        producer.close()

    elapsed = time.time() - start
    print(f"\nDone. sent={sent}  failed={failed}  elapsed={elapsed:.1f}s")


def parse_args():
    p = argparse.ArgumentParser(description="Replay a log file into Kafka.")
    p.add_argument("--file", required=True, help="Path to the log file (e.g. HDFS.log)")
    p.add_argument("--topic", default="hdfs-logs", help="Kafka topic to produce to")
    p.add_argument(
        "--bootstrap-servers",
        default="localhost:9092",
        help="Kafka bootstrap servers (host-side address)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only send the first N lines (omit for the full file)",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=0.001,
        help="Seconds to sleep between messages (0 = as fast as possible)",
    )
    p.add_argument(
        "--report-every",
        type=int,
        default=5000,
        help="Print a progress line every N messages sent",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    replay_file(
        file_path=args.file,
        topic=args.topic,
        bootstrap_servers=args.bootstrap_servers,
        limit=args.limit,
        delay=args.delay,
        report_every=args.report_every,
    )