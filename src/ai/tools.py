from __future__ import annotations

from typing import Any

from sqlalchemy import Result, text
from sqlalchemy.orm import Session

READ_ONLY_BLOCKLIST = {
    "insert",
    "update",
    "delete",
    "drop",
    "truncate",
    "alter",
    "create",
    "grant",
    "revoke",
}


def validate_read_only_query(query: str) -> None:
    normalized: str = query.strip().lower()
    if not (normalized.startswith("select") or normalized.startswith("with")):
        raise ValueError("Only SELECT/CTE statements are allowed")

    if ";" in normalized:
        raise ValueError("Multiple statements are not allowed")

    for forbidden in READ_ONLY_BLOCKLIST:
        if forbidden in normalized:
            raise ValueError("Potentially unsafe SQL detected")


def execute_read_only_query(session: Session, query: str) -> list[dict[str, Any]]:
    validate_read_only_query(query)
    result: Result[Any] = session.execute(text(query))
    return [dict(row._mapping) for row in result]


def query_for_intent(intent: str, user_input: str) -> str:
    base_kpi: str = """
WITH kpis AS (
  SELECT
    fecha,
    canal_venta,
    ventas,
    costos,
    impresiones,
    clicks,
    transacciones,
    clientes,
    CASE WHEN costos = 0 THEN 0 ELSE ((ventas - costos) / costos) END AS roi,
    CASE WHEN clientes = 0 THEN 0 ELSE (costos / clientes) END AS cac,
    CASE WHEN impresiones = 0 THEN 0 ELSE (CAST(clicks AS FLOAT) / impresiones) END AS tasa_cambio
  FROM fact_campaign_performance
)
""".strip()

    lowered: str = user_input.lower()

    if intent == "analysis":
        if ("agrupa" in lowered or "por" in lowered) and ("canal" in lowered or "channel" in lowered):
            return (
                f"{base_kpi} "
                "SELECT canal_venta, AVG(roi) AS avg_roi, AVG(cac) AS avg_cac, AVG(tasa_cambio) AS avg_tasa_cambio "
                "FROM kpis GROUP BY canal_venta ORDER BY avg_roi DESC"
            )

        if ("agrupa" in lowered or "por" in lowered) and ("fecha" in lowered or "date" in lowered):
            return (
                f"{base_kpi} "
                "SELECT fecha, AVG(roi) AS avg_roi, AVG(cac) AS avg_cac, AVG(tasa_cambio) AS avg_tasa_cambio "
                "FROM kpis GROUP BY fecha ORDER BY fecha DESC"
            )
    
        return (
            f"{base_kpi} "
            "SELECT fecha, canal_venta, roi, cac, tasa_cambio, ventas, costos, impresiones, clicks, transacciones, clientes "
            "FROM kpis ORDER BY fecha DESC, roi DESC LIMIT 50"
        )
    
    if intent == "data_query":
        if "historial" in lowered or "history" in lowered or "historia" in lowered:
            return (
                "SELECT canal_venta, cpc_base, fecha, actual "
                "FROM channel_rate_history ORDER BY fecha DESC, canal_venta ASC"
            )
        
        return (
            "SELECT fecha, canal_venta, ventas, costos, roi, cac, tasa_cambio "
            "FROM fact_campaign_performance ORDER BY fecha DESC, canal_venta ASC"
        )

    return ""


def summarize_result(intent: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No hay datos disponibles todavía. Ejecuta /data/ingest para cargar información."

    if intent == "analysis":
        best: int = max(rows, key=lambda row: float(row.get("roi", 0) or 0))
        worst: int = min(rows, key=lambda row: float(row.get("roi", 0) or 0))
        return (
            f"Análisis de desempeño de marketing:\n"
            f"\t+ Total de registros: {len(rows)}.\n"
            f"\t+ Mejor desempeño: {best.get('canal_venta')} ({best.get('fecha')}) con ROI {best.get('roi')}.\n"
            f"\t+ Peor desempeño: {worst.get('canal_venta')} ({worst.get('fecha')}) con ROI {worst.get('roi')}.\n"
            f"\t+ Promedio de ROI: {sum(float(row.get('roi', 0) or 0) for row in rows) / len(rows):.2f}.\n"
            f"\t+ Promedio de CAC: {sum(float(row.get('cac', 0) or 0) for row in rows) / len(rows):.2f}.\n"
            f"\t+ Promedio de tasa de cambio: {sum(float(row.get('tasa_cambio', 0) or 0) for row in rows) / len(rows):.2f}.\n"
        )
    
    i: int = 1
    complete_list: str = ""
    for row in rows:
        complete_list += f"\t+ Registro {i}: "
        complete_list += ", ".join(f"{key}: {row.get(key)}" for key in row.keys())
        complete_list += "\n"
        i += 1

    if rows[0].get("cpc_base") is not None:
        return (
            f"Se tienen {len(rows)} registros de historial de tasas de marketing. "
            f"El último registro es del canal {rows[0].get('canal_venta')} en la fecha {rows[0].get('fecha')} "
            f"con CPC base {rows[0].get('cpc_base')}.\n\n"
            f"Lista de registros completa:\n{complete_list}"
        )
    
    return (
        f"Se tienen {len(rows)} registros de desempeño de marketing. "
        f"El último registro es del canal {rows[0].get('canal_venta')} en la fecha {rows[0].get('fecha')} "
        f"con ROI {rows[0].get('roi')}, CAC {rows[0].get('cac')} y tasa de cambio {rows[0].get('tasa_cambio')}.\n"
        f"El primer registro es del canal {rows[-1].get('canal_venta')} en la fecha {rows[-1].get('fecha')} "
        f"con ROI {rows[-1].get('roi')}, CAC {rows[-1].get('cac')} y tasa de cambio {rows[-1].get('tasa_cambio')}.\n\n"
        f"Lista de registros completa:\n{complete_list}"
    )
