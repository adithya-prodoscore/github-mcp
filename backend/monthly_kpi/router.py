"""FastAPI router for Monthly KPI Report endpoints."""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from typing import Optional

from .repository import MonthlyKPIRepository
from .service import MonthlyKPIService

router = APIRouter(prefix="/api/monthly-kpi", tags=["monthly-kpi"])

_repository = MonthlyKPIRepository()
_service = MonthlyKPIService(_repository)


@router.get("/report")
async def get_monthly_kpi_report(
    domain_id: int = Query(9, description="Prodoscore domain ID (default: 9)"),
    start: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end: str = Query(None, description="End date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    role: Optional[str] = Query(None, description="Filter by role"),
):
    """Get monthly KPI report for specified domain and date range."""
    if not start or not end:
        today = datetime.utcnow()
        start = f"{today.year}-{today.month:02d}-01"
        end = f"{today.year}-{today.month:02d}-28"
    
    try:
        report = _service.assemble_report(
            domain_id=domain_id,
            start_date=start,
            end_date=end,
            department=department,
            role=role,
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "module": "monthly_kpi"}
