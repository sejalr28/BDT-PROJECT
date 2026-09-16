from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# --- Auth ---

class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Alerts ---

class AlertCreate(BaseModel):
    name: str
    condition_field: str  # "event_id" or "level"
    condition_value: str  # e.g. "E20" or "ERROR"
    threshold_count: int = 1
    lookback_minutes: int = 60


class AlertOut(BaseModel):
    id: int
    name: str
    condition_field: str
    condition_value: str
    threshold_count: int
    lookback_minutes: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Anomalies ---

class AnomalyOut(BaseModel):
    block_id: str
    true_label: Optional[int]
    predicted_label: Optional[int]
    probability_anomaly: Optional[float]
    scored_at: Optional[datetime]

    class Config:
        from_attributes = True