"""
Parses raw HDFS log lines into structured fields.

Raw line format (from the LogHub HDFS dataset):
    081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating

Fields: date, time, pid, level, component, content

The `content` portion is matched against the 29 known HDFS event templates
(from HDFS.log_templates.csv) to assign an event_id, and a block ID
(blk_...) is extracted separately since it's the join key used later for
anomaly labeling (anomaly_label.csv is keyed by block ID).
"""

import re

# Templates copied verbatim from HDFS.log_templates.csv. "[*]" is the
# dataset's wildcard token for variable content (block ids, sizes, IPs...).
_RAW_TEMPLATES = [
    ("E1", "[*]Adding an already existing block[*]"),
    ("E2", "[*]Verification succeeded for[*]"),
    ("E3", "[*]Served block[*]to[*]"),
    ("E4", "[*]Got exception while serving[*]to[*]"),
    ("E5", "[*]Receiving block[*]src:[*]dest:[*]"),
    ("E6", "[*]Received block[*]src:[*]dest:[*]of size[*]"),
    ("E7", "[*]writeBlock[*]received exception[*]"),
    ("E8", "[*]PacketResponder[*]for block[*]Interrupted[*]"),
    ("E9", "[*]Received block[*]of size[*]from[*]"),
    ("E10", "[*]PacketResponder[*]Exception[*]"),
    ("E11", "[*]PacketResponder[*]for block[*]terminating[*]"),
    ("E12", "[*]:Exception writing block[*]to mirror[*]"),
    ("E13", "[*]Receiving empty packet for block[*]"),
    ("E14", "[*]Exception in receiveBlock for block[*]"),
    ("E15", "[*]Changing block file offset of block[*]from[*]to[*]meta file offset to[*]"),
    ("E16", "[*]:Transmitted block[*]to[*]"),
    ("E17", "[*]:Failed to transfer[*]to[*]got[*]"),
    ("E18", "[*]Starting thread to transfer block[*]to[*]"),
    ("E19", "[*]Reopen Block[*]"),
    ("E20", "[*]Unexpected error trying to delete block[*]BlockInfo not found in volumeMap[*]"),
    ("E21", "[*]Deleting block[*]file[*]"),
    ("E22", "[*]BLOCK* NameSystem[*]allocateBlock:[*]"),
    ("E23", "[*]BLOCK* NameSystem[*]delete:[*]is added to invalidSet of[*]"),
    ("E24", "[*]BLOCK* Removing block[*]from neededReplications as it does not belong to any file[*]"),
    ("E25", "[*]BLOCK* ask[*]to replicate[*]to[*]"),
    ("E26", "[*]BLOCK* NameSystem[*]addStoredBlock: blockMap updated:[*]is added to[*]size[*]"),
    ("E27", "[*]BLOCK* NameSystem[*]addStoredBlock: Redundant addStoredBlock request received for[*]on[*]size[*]"),
    ("E28", "[*]BLOCK* NameSystem[*]addStoredBlock: addStoredBlock request received for[*]on[*]size[*]But it does not belong to any file[*]"),
    ("E29", "PendingReplicationMonitor timed out block[*]"),
]


def _template_to_regex(template: str) -> re.Pattern:
    parts = template.split("[*]")
    escaped = [re.escape(p) for p in parts]
    pattern = ".*?".join(escaped)
    return re.compile(pattern, re.IGNORECASE)


_EVENT_PATTERNS = [(eid, _template_to_regex(tmpl)) for eid, tmpl in _RAW_TEMPLATES]

_HEADER_RE = re.compile(
    r"^(?P<date>\d{6})\s+(?P<time>\d{6})\s+(?P<pid>\d+)\s+"
    r"(?P<level>[A-Z]+)\s+(?P<component>[\w\.\$]+):\s*(?P<content>.*)$"
)

_BLOCK_ID_RE = re.compile(r"blk_-?\d+")


def match_event_id(content: str) -> str:
    """Return the matching EventId for a content string, or 'UNKNOWN'."""
    for event_id, pattern in _EVENT_PATTERNS:
        if pattern.search(content):
            return event_id
    return "UNKNOWN"


def parse_line(raw_line: str) -> dict:
    """
    Parse one raw HDFS log line into a structured dict. Always returns
    all keys; on failure `parse_success` is False and structured fields
    are None (raw_line is preserved either way).
    """
    m = _HEADER_RE.match(raw_line)
    if not m:
        return {
            "raw_line": raw_line,
            "date": None,
            "time": None,
            "pid": None,
            "level": None,
            "component": None,
            "content": None,
            "event_id": "UNKNOWN",
            "block_id": None,
            "parse_success": False,
        }

    content = m.group("content")
    block_match = _BLOCK_ID_RE.search(content)

    return {
        "raw_line": raw_line,
        "date": m.group("date"),
        "time": m.group("time"),
        "pid": m.group("pid"),
        "level": m.group("level"),
        "component": m.group("component"),
        "content": content,
        "event_id": match_event_id(content),
        "block_id": block_match.group(0) if block_match else None,
        "parse_success": True,
    }