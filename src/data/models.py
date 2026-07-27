from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, Date, Enum as SAEnum, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ChannelEnum(str, Enum):
    FACEBOOK: str = "FACEBOOK"
    INSTAGRAM: str = "INSTAGRAM"
    TIKTOK: str = "TIKTOK"
    EMAIL: str = "EMAIL"
    WEB: str = "WEB"
    RADIO: str = "RADIO"
    FERIA: str = "FERIA"
    DIRECTO: str = "DIRECTO"
    OTRO: str = "OTRO"


class MarketingCostos(Base):
    __tablename__ = "costos_marketing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    canal_venta: Mapped[ChannelEnum] = mapped_column(SAEnum(ChannelEnum), nullable=False, index=True)
    costo: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    impresiones: Mapped[int] = mapped_column(Integer, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False)
    nuevos_usuarios: Mapped[int] = mapped_column(Integer, nullable=False)


class MarketingVentas(Base):
    __tablename__ = "ventas_marketing"
    __table_args__ = (UniqueConstraint("cliente", "fecha", name="uq_cliente_fecha_ventas"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True, autoincrement=False)
    cliente: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    monto: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    canal_venta: Mapped[ChannelEnum] = mapped_column(SAEnum(ChannelEnum), nullable=False, index=True)


class ChannelRateHistory(Base):
    __tablename__ = "channel_rate_history"
    __table_args__ = (UniqueConstraint("canal_venta", "fecha", name="uq_canal_fecha_scd"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canal_venta: Mapped[ChannelEnum] = mapped_column(SAEnum(ChannelEnum), nullable=False, index=True)
    cpc_base: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    actual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FactCampaignPerformance(Base):
    __tablename__ = "fact_campaign_performance"
    __table_args__ = (UniqueConstraint("fecha", "canal_venta", name="uq_canal_fecha_fact"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    canal_venta: Mapped[ChannelEnum] = mapped_column(SAEnum(ChannelEnum), nullable=False, index=True)
    ventas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    costos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    impresiones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transacciones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clientes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
