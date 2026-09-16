from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import BlockAnomalyPrediction
from app.schemas import AnomalyOut

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=List[AnomalyOut])
def list_anomalies(
    predicted_only: bool = Query(True, description="Only return blocks predicted as anomalies"),
    min_probability: Optional[float] = Query(None, ge=0, le=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = db.query(BlockAnomalyPrediction)

    if predicted_only:
        query = query.filter(BlockAnomalyPrediction.predicted_label == 1)
    if min_probability is not None:
        query = query.filter(BlockAnomalyPrediction.probability_anomaly >= min_probability)

    query = query.order_by(BlockAnomalyPrediction.probability_anomaly.desc()).limit(limit)
    return query.all()


@router.get("/{block_id}", response_model=AnomalyOut)
def get_anomaly(block_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    result = (
        db.query(BlockAnomalyPrediction)
        .filter(BlockAnomalyPrediction.block_id == block_id)
        .first()
    )
    if not result:
        return {"block_id": block_id, "true_label": None, "predicted_label": None,
                 "probability_anomaly": None, "scored_at": None}
    return result