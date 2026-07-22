from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.data.models import Base, FactCampaignPerformance, MarketingSpendRaw, SaleRaw
from src.data.pipeline import ingest_data, seed_marketing_from_sql_file


def test_ingest_deduplicates_and_builds_fact() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    sales = [
        {
            "transaction_id": "txn-1",
            "customer_id": "cust-1",
            "amount": "100",
            "sale_date": "2024-01-10",
            "channel": "Facebook",
        },
        {
            "transaction_id": "txn-1",
            "customer_id": "cust-1",
            "amount": "100",
            "sale_date": "2024-01-10",
            "channel": "facebook_ads",
        },
    ]
    marketing = [
        {
            "spend_date": "2024-01-10",
            "channel": "FB Ads",
            "campaign_name": "camp-1",
            "campaign_cost": "20",
            "impressions": 100,
            "clicks": 10,
        }
    ]

    with Session(engine) as session:
        result = ingest_data(session, sales_data=sales, marketing_data=marketing)
        assert result["inserted_sales"] == 1
        assert result["inserted_marketing"] == 1

        sales_count = session.scalar(select(func.count()).select_from(SaleRaw))
        assert sales_count == 1

        facts = session.scalars(select(FactCampaignPerformance)).all()
        assert len(facts) == 1
        assert float(facts[0].total_sales) == 100.0
        assert float(facts[0].total_spend) == 20.0


def test_seed_marketing_from_sql_file(tmp_path) -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    sql_file = tmp_path / "MARKETING_A.sql"
    sql_file.write_text(
        """
INSERT INTO marketing_spend_raw (spend_date, channel, campaign_name, campaign_cost, impressions, clicks)
VALUES ('2026-06-01', 'FACEBOOK', 'seed_campaign', 120.00, 5000, 250)
ON CONFLICT (spend_date, channel, campaign_name) DO NOTHING;
        """.strip(),
        encoding="utf-8",
    )

    with Session(engine) as session:
        loaded = seed_marketing_from_sql_file(session, str(sql_file))
        assert loaded is True
        rows = session.scalar(select(func.count()).select_from(MarketingSpendRaw))
        assert rows == 1
