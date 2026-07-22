from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.data.models import Base
from src.main import app, get_db


def test_endpoints_ingest_metrics_chat() -> None:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    ingest_response = client.post("/data/ingest", json={})
    assert ingest_response.status_code == 200
    assert ingest_response.json()["status"] == "ok"

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "metrics" in metrics_response.json()

    chat_response = client.post("/chat", json={"message": "Dame un resumen de métricas"})
    assert chat_response.status_code == 200
    assert "json" in chat_response.json()

    app.dependency_overrides.clear()
