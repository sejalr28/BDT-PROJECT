from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import get_current_user
from app.config import settings
from app.es_client import es_client

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/search")
def search_logs(
    q: Optional[str] = Query(None, description="Free-text search over log content"),
    level: Optional[str] = Query(None, description="Filter by level, e.g. INFO/WARN/ERROR"),
    event_id: Optional[str] = Query(None, description="Filter by event template id, e.g. E20"),
    block_id: Optional[str] = Query(None, description="Filter by block id"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    _user=Depends(get_current_user),
):
    must = []
    if q:
        must.append({"match": {"content": q}})
    if level:
        must.append({"term": {"level": level}})
    if event_id:
        must.append({"term": {"event_id": event_id}})
    if block_id:
        must.append({"term": {"block_id": block_id}})

    query = {"bool": {"must": must}} if must else {"match_all": {}}

    result = es_client.search(
        index=settings.logs_index,
        query=query,
        from_=(page - 1) * page_size,
        size=page_size,
        sort=[{"indexed_at": {"order": "desc"}}],
    )

    hits = result["hits"]["hits"]
    total = result["hits"]["total"]["value"]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [h["_source"] for h in hits],
    }