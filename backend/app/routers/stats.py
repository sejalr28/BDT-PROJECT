from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.config import settings
from app.es_client import es_client

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/level-breakdown")
def level_breakdown(_user=Depends(get_current_user)):
    result = es_client.search(
        index=settings.logs_index,
        size=0,
        aggs={"by_level": {"terms": {"field": "level", "size": 10}}},
    )
    buckets = result["aggregations"]["by_level"]["buckets"]
    return [{"level": b["key"], "count": b["doc_count"]} for b in buckets]


@router.get("/top-event-types")
def top_event_types(limit: int = 10, _user=Depends(get_current_user)):
    result = es_client.search(
        index=settings.logs_index,
        size=0,
        aggs={"by_event": {"terms": {"field": "event_id", "size": limit}}},
    )
    buckets = result["aggregations"]["by_event"]["buckets"]
    return [{"event_id": b["key"], "count": b["doc_count"]} for b in buckets]


@router.get("/busiest-blocks")
def busiest_blocks(limit: int = 20, _user=Depends(get_current_user)):
    result = es_client.search(
        index=settings.logs_index,
        size=0,
        query={"bool": {"must_not": {"term": {"block_id": ""}}}},
        aggs={"by_block": {"terms": {"field": "block_id", "size": limit}}},
    )
    buckets = result["aggregations"]["by_block"]["buckets"]
    return [{"block_id": b["key"], "count": b["doc_count"]} for b in buckets]


@router.get("/overview")
def overview(_user=Depends(get_current_user)):
    count_result = es_client.count(index=settings.logs_index)
    level_result = level_breakdown(_user=_user)
    top_events = top_event_types(limit=5, _user=_user)
    return {
        "total_log_lines": count_result["count"],
        "level_breakdown": level_result,
        "top_5_event_types": top_events,
    }