from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models  # noqa: F401 - ensures models are registered before create_all
from app.routers import auth, logs, stats, anomalies, alerts

# Creates users/alerts tables if they don't exist yet. Does NOT touch
# block_anomaly_predictions - that table is owned by Spark's JDBC writer
# (ml/score_and_export.py), which recreates it on each run.
Base.metadata.create_all(bind=engine, tables=[
    models.User.__table__,
    models.Alert.__table__,
])

app = FastAPI(
    title="Enterprise Log Analytics & Incident Detection API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(logs.router)
app.include_router(stats.router)
app.include_router(anomalies.router)
app.include_router(alerts.router)


@app.get("/health")
def health():
    return {"status": "ok"}