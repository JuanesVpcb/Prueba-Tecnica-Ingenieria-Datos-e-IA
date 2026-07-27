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
docker compose build --no-cache
docker compose up -d
```

Para reiniciar y ejecutar nuevamente la aplicación, usar:

```bash
docker compose build --no-cache app
docker compose up -d app
```

Al iniciar, la app crea tablas con SQLAlchemy y carga el seed `migrations/MARKETING_A.sql` (solo datos, sin DDL) con 1000 registros y el esquema estandarizado: `id`, `cliente`, `monto`, `fecha`, `canal_venta`.

## Endpoints

- `POST /data/ingest`: dispara ingesta + validación + consolidación histórica.
- `GET /metrics`: devuelve KPIs actuales (ROI, CAC, tasa de conversión).
- `POST /chat`: conversación con el agente para consultas y análisis.

### Ejemplo `/data/ingest`

```bash
curl -sS -X POST http://localhost:8000/data/ingest \
  -H "Content-Type: application/json" \
  --data-binary @migrations/INGEST_SAMPLE.json
```

### Ejemplo `/metrics`

```bash
curl -sS http://localhost:8000/metrics
```

### Ejemplo `/chat`

Se tienen 3 posibilidades para que el agente de IA realice. Entre estas, se tiene "analysis":

```bash
curl -sS -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Agrupa por fecha los registros y analiza los resultados."}'
```

"data_query":

```bash
curl -sS -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Quiero ver la tabla de datos."}'
```

y "update":

```bash
curl -sS -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Quiero cargar nuevos datos al modelo."}'
```
