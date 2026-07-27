from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import Result, delete, func, select, text
from sqlalchemy.orm import Session

from src.data.models import ChannelEnum, ChannelRateHistory, FactCampaignPerformance, MarketingCostos, MarketingVentas
from src.data.validator import normalize_channel, validar_ventas, validar_costos, RecordVentas, RecordCostos


def default_ventas() -> list[dict]:
    today: date = date.today()
    return [
        {
            "id": "5142acb8-1e0c-443e-8eb0-d8915b9eaff4",
            "cliente": "cust-001",
            "monto": "1200",
            "fecha": today.isoformat(),
            "canal_venta": "facebook_ads",
        },
        {
            "id": "5142acb8-1e0c-443e-8eb0-d8915b23edde",
            "cliente": "cust-002",
            "monto": "250",
            "fecha": today.isoformat(),
            "canal_venta": "google",
        },
    ]


def default_costos() -> list[dict]:
    today: date = date.today()
    return [
        {
            "costo": "800",
            "fecha": today.isoformat(),
            "canal_venta": "FB Ads",
            "impresiones": "1000",
            "clicks": "50",
            "nuevos_usuarios": "10",
        },
        {
            "costo": "1100",
            "fecha": today.isoformat(),
            "canal_venta": "google_ads",
            "impresiones": "1500",
            "clicks": "75",
            "nuevos_usuarios": "15",
        },
    ]


def seed_channel_rates(session: Session) -> None:
    if session.scalar(select(func.count()).select_from(ChannelRateHistory)):
        return

    # Valores inventados para propósitos de prueba, en un escenario real estos valores 
    # deberían provenir de una fuente confiable
    defaults: list[tuple[ChannelEnum, Decimal]] = [
        (ChannelEnum.FACEBOOK, Decimal("0.20")),
        (ChannelEnum.TIKTOK, Decimal("0.25")),
        (ChannelEnum.INSTAGRAM, Decimal("0.18")),
        (ChannelEnum.EMAIL, Decimal("0.05")),
        (ChannelEnum.DIRECTO, Decimal("0.02")),
        (ChannelEnum.WEB, Decimal("0.11")),
        (ChannelEnum.RADIO, Decimal("0.15")),
        (ChannelEnum.FERIA, Decimal("0.40")),
        (ChannelEnum.OTRO, Decimal("0.00")),
    ]
    for canal_venta, cpc_base in defaults:
        session.add(
            ChannelRateHistory(
                canal_venta=canal_venta,
                cpc_base=cpc_base,
                fecha=date.today().replace(day=1),
                actual=True,
            )
        )


def add_channel_rate(session: Session, canal_venta: ChannelEnum, cpc_base: Decimal, fecha: date) -> None:
    existing: ChannelRateHistory | None = session.scalar(
        select(ChannelRateHistory)
        .where(ChannelRateHistory.canal_venta == canal_venta)
        .where(ChannelRateHistory.fecha == fecha)
    )
    if existing:
        existing.cpc_base = cpc_base
        existing.actual = True
    else:
        session.add(
            ChannelRateHistory(
                canal_venta=canal_venta,
                cpc_base=cpc_base,
                fecha=fecha,
                actual=True,
            )
        )
        current = session.scalar(
            select(ChannelRateHistory)
            .where(ChannelRateHistory.canal_venta == canal_venta)
            .where(ChannelRateHistory.actual == True)
        )
        if current:
            current.actual = False


def refresh_fact_table(session: Session) -> None:
    ventas_filas: Result = session.execute(
        select(
            MarketingVentas.fecha,
            MarketingVentas.canal_venta,
            func.sum(MarketingVentas.monto).label("ventas"),
            func.count(MarketingVentas.id).label("transacciones"),
            func.count(func.distinct(MarketingVentas.cliente)).label("clientes"),
        ).group_by(MarketingVentas.fecha, MarketingVentas.canal_venta)
    ).all()

    costos_filas: Result = session.execute(
        select(
            MarketingCostos.fecha,
            MarketingCostos.canal_venta,
            func.sum(MarketingCostos.costo).label("costos"),
            func.sum(MarketingCostos.impresiones).label("impresiones"),
            func.sum(MarketingCostos.clicks).label("clicks"),
        ).group_by(MarketingCostos.fecha, MarketingCostos.canal_venta)
    ).all()

    merged: dict[tuple[date, ChannelEnum], dict] = defaultdict(
        lambda: {
            "ventas": 0,
            "costos": 0,
            "impresiones": 0,
            "clicks": 0,
            "transacciones": 0,
            "clientes": 0,
        }
    )

    for row in ventas_filas:
        key: tuple[date, ChannelEnum] = (row.fecha, row.canal_venta)
        merged[key]["ventas"] = int(row.ventas or 0)
        merged[key]["transacciones"] = int(row.transacciones or 0)
        merged[key]["clientes"] = int(row.clientes or 0)

    for row in costos_filas:
        key: tuple[date, ChannelEnum] = (row.fecha, row.canal_venta)
        merged[key]["costos"] = int(row.costos or 0)
        merged[key]["impresiones"] = int(row.impresiones or 0)
        merged[key]["clicks"] = int(row.clicks or 0)

    session.execute(delete(FactCampaignPerformance))
    for (fecha, canal_venta), valores in merged.items():
        session.add(FactCampaignPerformance(fecha=fecha, canal_venta=canal_venta, **valores))


def ingest_data(
    session: Session,
    ventas: list[dict] | None = None,
    costos: list[dict] | None = None,
) -> dict:
    ventas_registro: list[RecordVentas] = validar_ventas(ventas or default_ventas())
    costos_registro: list[RecordCostos] = validar_costos(costos or default_costos())

    inserted_sales: int = 0
    seen_sales: set[str] = set()
    for record in ventas_registro:
        if record.id in seen_sales:
            continue
        seen_sales.add(record.id)

        exists: str | None = session.scalar(select(MarketingVentas.id).where(MarketingVentas.id == record.id))
        if exists:
            continue

        ventas_kwargs: dict[str, Any] = {
            "id": record.id,
            "cliente": record.cliente,
            "monto": int(record.monto),
            "fecha": record.fecha,
            "canal_venta": normalize_channel(record.canal_venta)
        }
        session.add(MarketingVentas(**ventas_kwargs))
        inserted_sales += 1

    inserted_marketing: int = 0
    seen_marketing: set[tuple[date, ChannelEnum]] = set()
    for record in costos_registro:
        key = (record.fecha, record.canal_venta)
        if key in seen_marketing:
            continue
        seen_marketing.add(key)

        exists: date | None = session.scalar(select(MarketingCostos.fecha)
                                     .where((MarketingCostos.fecha, MarketingCostos.canal_venta) == key))
        if exists:
            continue

        costos_kwargs: dict[str, Any] = {
            "fecha": record.fecha,
            "canal_venta": normalize_channel(record.canal_venta),
            "costo": int(record.costo),
            "impresiones": int(record.impresiones),
            "clicks": int(record.clicks),
            "nuevos_usuarios": int(record.nuevos_usuarios)
        }
        session.add(MarketingCostos(**costos_kwargs))
        inserted_marketing += 1

    seed_channel_rates(session)
    session.flush()
    refresh_fact_table(session)
    session.commit()

    return {
        "inserted_sales": inserted_sales,
        "inserted_marketing": inserted_marketing,
    }


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
