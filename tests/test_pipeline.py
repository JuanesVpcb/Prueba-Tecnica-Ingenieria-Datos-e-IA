from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.data.models import Base, FactCampaignPerformance, MarketingVentas, MarketingCostos
from src.data.pipeline import ingest_data, seed_marketing_from_sql_file


def test_ingest_deduplicates_and_builds_fact() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    costos = [
        {
            "fecha": "2024-01-10",
            "canal_venta": "Facebook",
            "costo": "100000",
            "impresiones": "100",
            "clicks": "10",
            "nuevos_usuarios": "5",
        },
        {
            "fecha": "2024-01-10",
            "canal_venta": "Facebook_ads",
            "costo": "100000",
            "impresiones": "100",
            "clicks": "10",
            "nuevos_usuarios": "5",
        },
    ]
    ventas = [
        {
            "id": '43231a6e-d2a9-4b5a-839b-d2bc2e8545fd',
            "cliente": "cliente-1",
            "monto": "20000",
            "fecha": "2024-01-10",
            "canal_venta": "FB Ads",
        }
    ]

    with Session(engine) as session:
        result = ingest_data(session, ventas=ventas, costos=costos)
        assert result["inserted_sales"] == 1
        assert result["inserted_marketing"] == 1

        sales_count = session.scalar(select(func.count()).select_from(MarketingCostos))
        assert sales_count == 1

        facts = session.scalars(select(FactCampaignPerformance)).all()
        assert len(facts) == 1
        assert float(facts[0].ventas) == 20000.0
        assert float(facts[0].costos) == 100.0


def test_seed_marketing_from_sql_file(tmp_path) -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    sql_file = tmp_path / "VENTAS_MARKETING.sql"
    sql_file.write_text(
        """
INSERT INTO VENTAS_MARKETING (id, cliente, monto, fecha, canal_venta)
VALUES ('5f8414eb-1ede-44fe-b66b-d30ddb7aac27', 'Claude Nawrocki', 42197000, '2025-12-16', 'TIKTOK')
ON CONFLICT (cliente, fecha) DO NOTHING;
        """.strip(),
        encoding="utf-8",
    )

    with Session(engine) as session:
        loaded = seed_marketing_from_sql_file(session, str(sql_file))
        assert loaded is True
        rows = session.scalar(select(func.count()).select_from(MarketingVentas))
        assert rows == 1
