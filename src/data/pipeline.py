from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from src.data.models import ChannelEnum, ChannelRateHistory, FactCampaignPerformance, MarketingSpendRaw, SaleRaw
from src.data.validator import normalize_channel, validate_marketing, validate_sales


def default_sales_source() -> list[dict]:
    today = date.today()
    return [
        {
            "transaction_id": f"txn-{today.isoformat()}-1",
            "customer_id": "cust-001",
            "amount": "120.50",
            "sale_date": today.isoformat(),
            "channel": "facebook_ads",
        },
        {
            "transaction_id": f"txn-{today.isoformat()}-2",
            "customer_id": "cust-002",
            "amount": "250.00",
            "sale_date": today.isoformat(),
            "channel": "google",
        },
    ]


def default_marketing_source() -> list[dict]:
    today = date.today()
    return [
        {
            "spend_date": today.isoformat(),
            "channel": "FB Ads",
            "campaign_name": "awareness",
            "campaign_cost": "80.00",
            "impressions": 10000,
            "clicks": 450,
        },
        {
            "spend_date": today.isoformat(),
            "channel": "google_ads",
            "campaign_name": "intent",
            "campaign_cost": "110.00",
            "impressions": 8000,
            "clicks": 370,
        },
    ]


def seed_channel_rates(session: Session) -> None:
    if session.scalar(select(func.count()).select_from(ChannelRateHistory)):
        return

    defaults = [
        (ChannelEnum.FACEBOOK, Decimal("0.20")),
        (ChannelEnum.GOOGLE, Decimal("0.35")),
        (ChannelEnum.INSTAGRAM, Decimal("0.18")),
        (ChannelEnum.EMAIL, Decimal("0.05")),
        (ChannelEnum.DIRECT, Decimal("0.00")),
    ]
    for channel, base_cpc in defaults:
        session.add(
            ChannelRateHistory(
                channel=channel,
                base_cpc=base_cpc,
                valid_from=date.today().replace(day=1),
                valid_to=None,
                is_current=True,
            )
        )


def ingest_data(
    session: Session,
    sales_data: list[dict] | None = None,
    marketing_data: list[dict] | None = None,
) -> dict:
    sales_records = validate_sales(sales_data or default_sales_source())
    marketing_records = validate_marketing(marketing_data or default_marketing_source())

    inserted_sales = 0
    seen_sales = set()
    for record in sales_records:
        if record.transaction_id in seen_sales:
            continue
        seen_sales.add(record.transaction_id)

        exists = session.scalar(select(SaleRaw.id).where(SaleRaw.transaction_id == record.transaction_id))
        if exists:
            continue

        session.add(
            SaleRaw(
                transaction_id=record.transaction_id,
                customer_id=record.customer_id,
                amount=record.amount,
                sale_date=record.sale_date,
                channel=normalize_channel(record.channel),
            )
        )
        inserted_sales += 1

    inserted_marketing = 0
    seen_marketing = set()
    for record in marketing_records:
        key = (record.spend_date, normalize_channel(record.channel), record.campaign_name)
        if key in seen_marketing:
            continue
        seen_marketing.add(key)

        exists = session.scalar(
            select(MarketingSpendRaw.id).where(
                MarketingSpendRaw.spend_date == record.spend_date,
                MarketingSpendRaw.channel == key[1],
                MarketingSpendRaw.campaign_name == record.campaign_name,
            )
        )
        if exists:
            continue

        session.add(
            MarketingSpendRaw(
                spend_date=record.spend_date,
                channel=key[1],
                campaign_name=record.campaign_name,
                campaign_cost=record.campaign_cost,
                impressions=record.impressions,
                clicks=record.clicks,
            )
        )
        inserted_marketing += 1

    seed_channel_rates(session)
    session.flush()
    refresh_fact_table(session)
    session.commit()

    return {
        "inserted_sales": inserted_sales,
        "inserted_marketing": inserted_marketing,
    }


def refresh_fact_table(session: Session) -> None:
    sales_rows = session.execute(
        select(
            SaleRaw.sale_date,
            SaleRaw.channel,
            func.sum(SaleRaw.amount).label("sales"),
            func.count(SaleRaw.id).label("transactions"),
            func.count(func.distinct(SaleRaw.customer_id)).label("customers"),
        ).group_by(SaleRaw.sale_date, SaleRaw.channel)
    ).all()

    marketing_rows = session.execute(
        select(
            MarketingSpendRaw.spend_date,
            MarketingSpendRaw.channel,
            func.sum(MarketingSpendRaw.campaign_cost).label("spend"),
            func.sum(MarketingSpendRaw.impressions).label("impressions"),
            func.sum(MarketingSpendRaw.clicks).label("clicks"),
        ).group_by(MarketingSpendRaw.spend_date, MarketingSpendRaw.channel)
    ).all()

    merged: dict[tuple[date, ChannelEnum], dict] = defaultdict(
        lambda: {
            "total_sales": Decimal("0"),
            "total_spend": Decimal("0"),
            "impressions": 0,
            "clicks": 0,
            "transactions": 0,
            "customers_acquired": 0,
        }
    )

    for row in sales_rows:
        key = (row.sale_date, row.channel)
        merged[key]["total_sales"] = row.sales or Decimal("0")
        merged[key]["transactions"] = int(row.transactions or 0)
        merged[key]["customers_acquired"] = int(row.customers or 0)

    for row in marketing_rows:
        key = (row.spend_date, row.channel)
        merged[key]["total_spend"] = row.spend or Decimal("0")
        merged[key]["impressions"] = int(row.impressions or 0)
        merged[key]["clicks"] = int(row.clicks or 0)

    session.execute(delete(FactCampaignPerformance))
    for (perf_date, channel), values in merged.items():
        session.add(FactCampaignPerformance(perf_date=perf_date, channel=channel, **values))


def seed_marketing_from_sql_file(session: Session, sql_file_path: str) -> bool:
    sql_path = Path(sql_file_path)
    if not sql_path.exists():
        return False

    sql_text = sql_path.read_text(encoding="utf-8").strip()
    if not sql_text:
        return False

    session.execute(text(sql_text))
    session.commit()
    refresh_fact_table(session)
    session.commit()
    return True
