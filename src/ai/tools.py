from __future__ import annotations

from typing import Any

from sqlalchemy import text
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
    normalized = query.strip().lower()
    if not (normalized.startswith("select") or normalized.startswith("with")):
        raise ValueError("Only SELECT/CTE statements are allowed")

    if ";" in normalized:
        raise ValueError("Multiple statements are not allowed")

    for forbidden in READ_ONLY_BLOCKLIST:
        if forbidden in normalized:
            raise ValueError("Potentially unsafe SQL detected")


def execute_read_only_query(session: Session, query: str) -> list[dict[str, Any]]:
    validate_read_only_query(query)
    result = session.execute(text(query))
    return [dict(row._mapping) for row in result]


def query_for_intent(intent: str, user_input: str) -> str:
    base_kpi = """
WITH kpis AS (
  SELECT
    perf_date,
    channel,
    total_sales,
    total_spend,
    impressions,
    clicks,
    transactions,
    customers_acquired,
    CASE WHEN total_spend = 0 THEN 0 ELSE ((total_sales - total_spend) / total_spend) END AS roi,
    CASE WHEN customers_acquired = 0 THEN 0 ELSE (total_spend / customers_acquired) END AS cac,
    CASE WHEN impressions = 0 THEN 0 ELSE (CAST(clicks AS FLOAT) / impressions) END AS conversion_rate
  FROM fact_campaign_performance
)
""".strip()

    lowered = user_input.lower()
    if intent == "analysis":
        return (
            f"{base_kpi} "
            "SELECT perf_date, channel, roi, cac, conversion_rate "
            "FROM kpis ORDER BY perf_date DESC, roi DESC LIMIT 50"
        )

    if "canal" in lowered or "channel" in lowered:
        return (
            f"{base_kpi} "
            "SELECT channel, AVG(roi) AS avg_roi, AVG(cac) AS avg_cac "
            "FROM kpis GROUP BY channel ORDER BY avg_roi DESC"
        )

    return (
        f"{base_kpi} "
        "SELECT perf_date, channel, total_sales, total_spend, roi, cac, conversion_rate "
        "FROM kpis ORDER BY perf_date DESC LIMIT 30"
    )


def summarize_result(intent: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No hay datos disponibles todavía. Ejecuta /data/ingest para cargar información."

    if intent == "analysis":
        best = max(rows, key=lambda row: float(row.get("roi", 0) or 0))
        worst = min(rows, key=lambda row: float(row.get("roi", 0) or 0))
        return (
            f"Mejor desempeño: {best.get('channel')} ({best.get('perf_date')}) con ROI {best.get('roi')}. "
            f"Peor desempeño: {worst.get('channel')} ({worst.get('perf_date')}) con ROI {worst.get('roi')}."
        )

    return f"Consulta completada con {len(rows)} registros."
