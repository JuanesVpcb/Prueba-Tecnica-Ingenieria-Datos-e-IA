from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, Date, Enum as SAEnum, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ChannelEnum(str, Enum):
    FACEBOOK = "FACEBOOK"
    GOOGLE = "GOOGLE"
    INSTAGRAM = "INSTAGRAM"
    EMAIL = "EMAIL"
    DIRECT = "DIRECT"
    OTHER = "OTHER"


class SaleRaw(Base):
    __tablename__ = "sales_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    channel: Mapped[ChannelEnum] = mapped_column(SAEnum(ChannelEnum), nullable=False, index=True)


class MarketingSpendRaw(Base):
    __tablename__ = "marketing_spend_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    cliente: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    canal_venta: Mapped[ChannelEnum] = mapped_column(SAEnum(ChannelEnum), nullable=False, index=True)


class ChannelRateHistory(Base):
    __tablename__ = "channel_rate_history"
    __table_args__ = (UniqueConstraint("channel", "valid_from", name="uq_channel_valid_from"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel: Mapped[ChannelEnum] = mapped_column(SAEnum(ChannelEnum), nullable=False, index=True)
    base_cpc: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FactCampaignPerformance(Base):
    __tablename__ = "fact_campaign_performance"
    __table_args__ = (UniqueConstraint("perf_date", "channel", name="uq_fact_date_channel"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    perf_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    channel: Mapped[ChannelEnum] = mapped_column(SAEnum(ChannelEnum), nullable=False, index=True)
    total_sales: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_spend: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    customers_acquired: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
