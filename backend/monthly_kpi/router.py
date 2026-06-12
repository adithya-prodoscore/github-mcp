"""FastAPI router for Monthly KPI Report."""

import logging
from fastapi import APIRouter, HTTPException
from .schemas import MonthlyKPIRequest, MonthlyKPIResponse
from .repository import MonthlyKPIRepository
from .service import MonthlyKPIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monthly-kpi", tags=["monthly-kpi"])

_repository = MonthlyKPIRepository()
_service = MonthlyKPIService(_repository)


@router.post("/report", response_model=MonthlyKPIResponse)
def generate_kpi_report(request: MonthlyKPIRequest) -> MonthlyKPIResponse:
    """Generate a Monthly KPI Report."""
    try:
        logger.info(f"[router] Generating KPI report: domain={request.domain_id}")
        result = _service.assemble_report(request.domain_id, request.start_date, request.end_date)
        return MonthlyKPIResponse(**result)
    except Exception as e:
        logger.error(f"[router] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "monthly-kpi"}
