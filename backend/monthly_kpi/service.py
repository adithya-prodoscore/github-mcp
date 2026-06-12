"""Business logic layer for Monthly KPI Report."""

import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

EMDASH = "—"
MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
EPS = 1e-9


def _na(x):
    """Check if value is NA/None/NaN."""
    return x is None or (isinstance(x, float) and math.isnan(x))


def _floor_half_up(x):
    """Half-up rounding (parity with R)."""
    return math.floor(x + 0.5 + EPS)


def fmt_hm(minutes):
    """Format minutes as 'Hh MMmin'."""
    if _na(minutes):
        return EMDASH
    m = _floor_half_up(minutes)
    return f"{m // 60}h {m % 60:02d}min"


def fmt_date(s):
    """Format ISO date as 'Mon DD, YYYY'."""
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
        return f"{MONTHS[d.month]} {d.day:02d}, {d.year}"
    except:
        return EMDASH


class MonthlyKPIService:
    """Service layer for KPI report generation."""

    def __init__(self, repository):
        """Initialize service with data repository."""
        self.repository = repository

    def assemble_report(self, domain_id: int, start_date: str, end_date: str, **filters) -> Dict[str, Any]:
        """Assemble complete monthly KPI report."""
        raw = self.repository.query(domain_id, start_date, end_date)
        employees = []
        for c in raw.get("employees", []):
            emp = self._build_employee(c, raw)
            employees.append(emp)
        
        return {
            "header": self._build_header(domain_id, raw, start_date, end_date),
            "employees": employees,
            "filter_options": self._generate_filters(employees),
            "statusCounts": self._count_statuses(employees),
        }

    def _build_employee(self, c: dict, raw: dict) -> dict:
        """Build one employee object."""
        eid = c.get("employee_id", 0)
        role = c.get("role", "Unassigned")
        score = int(c.get("avg_score", 0))
        active_min = c.get("avg_active_min_raw")
        active_time = fmt_hm(active_min) if not _na(active_min) else "0h 00min"
        
        rAvg = 0
        for ra in raw.get("roleAverages", []):
            if ra.get("role") == role:
                rAvg = int(ra.get("role_score", 0))
                break
        
        return {
            "id": str(eid),
            "name": c.get("name", "Unknown"),
            "dept": c.get("dept", "Unassigned"),
            "role": role,
            "manager": raw.get("manager_lookup", {}).get(int(c.get("manager_id", 0)), ""),
            "score": score,
            "roleAvg": rAvg,
            "delta": f"{'+'if score >= rAvg else ''}{score - rAvg}",
            "activeTime": active_time,
            "trendCy": [float(score)],
            "trendColor": "var(--blue-500)" if score >= 70 else "var(--red-500)",
            "status": "on-track",
            "metrics": [{"section": "SCORE", "label": "Avg Score", "value": str(score), "roleAvg": str(rAvg)}],
        }

    def _generate_filters(self, employees: list) -> Dict[str, List[str]]:
        """Generate unique filter options."""
        return {
            "dept": sorted(set(e.get("dept", "Unassigned") for e in employees)),
            "role": sorted(set(e.get("role", "Unassigned") for e in employees)),
            "manager": sorted(set(e.get("manager", "") for e in employees if e.get("manager"))),
            "employee": sorted(set(e.get("name", "") for e in employees)),
        }

    def _build_header(self, domain_id: int, raw: dict, start_date: str, end_date: str) -> Dict[str, str]:
        """Build report header."""
        company_name = raw.get("company_name", f"Domain {domain_id}")
        return {
            "title": "Monthly KPI Report",
            "breadcrumb": company_name,
            "dateRange": f"{fmt_date(start_date)} – {fmt_date(end_date)}",
            "dateFrom": fmt_date(start_date),
            "dateTo": fmt_date(end_date),
        }

    def _count_statuses(self, employees: list) -> Dict[str, int]:
        """Count employees per status."""
        counts = Counter(e.get("status", "on-track") for e in employees)
        return {
            "needs-attention": counts.get("needs-attention", 0),
            "inactive": counts.get("inactive", 0),
            "most-engaged": counts.get("most-engaged", 0),
            "on-track": counts.get("on-track", 0),
        }
