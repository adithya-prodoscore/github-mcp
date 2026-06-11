"""Monthly KPI Report module.

FastAPI router for monthly KPI report generation and retrieval.
Integrates with BigQuery for data access and service layer for business logic.
"""

from .router import router

__all__ = ["router"]
