# Insight-Extractor & History Tracker

Implementación base de la prueba técnica **Data & AI Engineer** con:
- Ingesta y gobernanza de datos (validación, homologación y deduplicación)
- Modelo histórico en PostgreSQL con SQLAlchemy
- Agente de IA con grafo de estados (LangGraph) y SQL de solo lectura
- API FastAPI con endpoints `/data/ingest`, `/metrics` y `/chat`

## Estructura

```text
src/
  data/
    models.py
    pipeline.py
    validator.py
  ai/
    agent.py
    tools.py
  main.py
migrations/
Dockerfile
docker-compose.yml
requirements.txt
ARCHITECTURE.md
```

## Ejecutar local

```bash
docker-compose up --build
```

Al iniciar, la app crea tablas con SQLAlchemy y carga el seed `migrations/MARKETING_A.sql` (solo datos, sin DDL).

## Endpoints

- `POST /data/ingest`: dispara ingesta + validación + consolidación histórica.
- `GET /metrics`: devuelve KPIs actuales (ROI, CAC, tasa de conversión).
- `POST /chat`: conversación con el agente para consultas y análisis.

### Ejemplo `/chat`

```json
{
  "message": "Analiza ROI por canal y dame recomendaciones"
}
```
