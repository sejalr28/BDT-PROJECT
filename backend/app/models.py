from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    # what to watch: "event_id" or "level"
    condition_field = Column(String, nullable=False)
    # value to match, e.g. "ERROR" or "E20"
    condition_value = Column(String, nullable=False)
    # trigger if count in the lookback window >= this
    threshold_count = Column(Integer, nullable=False, default=1)
    lookback_minutes = Column(Integer, nullable=False, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BlockAnomalyPrediction(Base):
    """
    Read-only mirror of the table ml/score_and_export.py writes.
    SQLAlchemy doesn't manage this table's schema (Spark's JDBC writer
    creates it) - this class exists just so we can query it with the ORM.
    """
    __tablename__ = "block_anomaly_predictions"

    block_id = Column(String, primary_key=True)
    true_label = Column(Integer)
    predicted_label = Column(Integer)
    probability_anomaly = Column(Float)
    scored_at = Column(DateTime(timezone=True))