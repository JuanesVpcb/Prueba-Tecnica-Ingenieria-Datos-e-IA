from __future__ import annotations

import os
from typing import Any

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.ai.agent import InsightAgent
from src.data.models import Base
from src.data.pipeline import ingest_data, seed_marketing_from_sql_file

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

app = FastAPI(title="Insight Extractor & History Tracker", version="1.0.0")
agent = InsightAgent()


class ChatRequest(BaseModel):
    message: str


class IngestRequest(BaseModel):
    sales_data: list[dict[str, Any]] | None = None
    marketing_data: list[dict[str, Any]] | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_marketing_from_sql_file(session, "/app/migrations/MARKETING_A.sql")


@app.post("/data/ingest")
async def data_ingest(payload: IngestRequest, db: Session = Depends(get_db)):
    result = ingest_data(db, sales_data=payload.sales_data, marketing_data=payload.marketing_data)
    return {"status": "ok", **result}


@app.get("/metrics")
async def metrics(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT
                perf_date,
                channel,
                total_sales,
                total_spend,
                CASE WHEN total_spend = 0 THEN 0 ELSE ((total_sales - total_spend) / total_spend) END AS roi,
                CASE WHEN customers_acquired = 0 THEN 0 ELSE (total_spend / customers_acquired) END AS cac,
                CASE WHEN impressions = 0 THEN 0 ELSE (CAST(clicks AS FLOAT) / impressions) END AS conversion_rate
            FROM fact_campaign_performance
            ORDER BY perf_date DESC, channel
            """
        )
    )
    return {"metrics": [dict(row._mapping) for row in rows]}


@app.post("/chat")
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    response = agent.invoke(payload.message, db)
    return response
