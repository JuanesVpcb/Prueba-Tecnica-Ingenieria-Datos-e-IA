# Arquitectura propuesta (GCP + Azure DevOps)

## Escalabilidad en GCP

- **API/Agente**: desplegar FastAPI en **Cloud Run** (autoscaling, revisiones, rollback).
- **Base transaccional/analítica inicial**: **Cloud SQL PostgreSQL** con usuario read-only para el agente.
- **Analítica avanzada**: replicar históricos a **BigQuery** para consultas de alto volumen.
- **Transformación y gobernanza**: usar **dbt** + pruebas de calidad (esquema, unicidad, no nulos) y reglas de negocio.
- **Orquestación**: **Cloud Composer** o **Workflows** para pipeline de ingesta programado.
- **IA empresarial**: mover el razonamiento a **Vertex AI** con observabilidad de prompts y seguridad.

## CI/CD en Azure DevOps

1. **CI**:
   - `pytest` + chequeo de estilo.
   - Build de imagen Docker.
   - Escaneo de seguridad (dependencias/secretos).
2. **CD**:
   - Deploy por ambientes (dev/qa/prod) con aprobaciones.
   - Ejecutar migraciones antes de promover versión de API.
   - Despliegue blue/green o canary en Cloud Run.
3. **Gobernanza**:
   - Variables y secretos en Azure Key Vault.
   - Políticas de branch protection + PR reviews obligatorios.
