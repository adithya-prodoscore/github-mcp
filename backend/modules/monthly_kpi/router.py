"""FastAPI router for Monthly KPI Report endpoints.

Public REST API for report generation and health checks.
"""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from .repository import MonthlyKPIRepository
from .service import MonthlyKPIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monthly-kpi", tags=["monthly-kpi"])

# Initialize dependencies (lazy-load on first request)
_repository = None
_service = None


def get_service() -> MonthlyKPIService:
    """Get or initialize service."""
    global _repository, _service
    if _service is None:
        _repository = MonthlyKPIRepository()
        _service = MonthlyKPIService(_repository)
    return _service


@router.get("/report", response_model=Dict[str, Any])
async def get_monthly_kpi_report(
    domain_id: int = Query(9, description="Prodoscore domain ID (default: 9 = safe, others are live customers)"),
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    role: Optional[str] = Query(None, description="Filter by role"),
    manager: Optional[str] = Query(None, description="Filter by manager"),
    employee: Optional[str] = Query(None, description="Filter by employee name"),
) -> Dict[str, Any]:
    """
    Get monthly KPI report for specified domain and date range.

    **Safety:** Domain 9 (Prodoscore) is the only safe default for testing.
    All other domains are live customers — require explicit authorization.

    Returns complete report with employee list, filter options, and status counts.
    """
    # Validate domain (simple guard; extend with RBAC in production)
    if domain_id != 9:
        logger.warning(f"[router] Non-safe domain requested: {domain_id}")
        raise HTTPException(
            status_code=403,
            detail=f"Domain {domain_id} is a live customer. Authorization required.",
        )

    # Auto-default to current month if not provided
    if not start or not end:
        today = datetime.utcnow()
        start = f"{today.year}-{today.month:02d}-01"
        end = f"{today.year}-{today.month:02d}-28"

    try:
        service = get_service()
        report = service.assemble_report(
            domain_id=domain_id,
            start_date=start,
            end_date=end,
            department=department,
            role=role,
            manager=manager,
            employee=employee,
        )
        logger.info(f"[router] Report generated: domain={domain_id} {start}..{end} "
                    f"employees={len(report.get('employees', []))}")
        return report
    except Exception as e:
        logger.error(f"[router] Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    try:
        service = get_service()
        return {
            "status": "healthy",
            "module": "monthly_kpi",
            "version": "3.3.0",
        }
    except Exception as e:
        logger.error(f"[router] Health check failed: {e}")
        return {
            "status": "unhealthy",
            "module": "monthly_kpi",
            "error": str(e),
        }


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """Return module configuration and metadata."""
    return {
        "version": "3.3.0",
        "module": "monthly_kpi",
        "status_strings": ["needs-attention", "inactive", "most-engaged", "on-track"],
        "safe_domain_id": 9,
        "safe_domain_name": "Prodoscore",
        "triage_config": {
            "min_flagged": 1,
            "max_flagged": 8,
            "min_top_performers": 1,
            "max_top_performers": 8,
        },
        "metrics_sections": [
            "SCORE",
            "WORK HABITS",
            "MOST & LEAST PRODUCTIVE",
            "MEETINGS",
            "TECH MODULES",
            "WEB BROWSER",
        ],
    }
