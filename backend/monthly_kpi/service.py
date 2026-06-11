"""Business logic layer for Monthly KPI Report.

Handles triage classification, calculations (parity with Python),
and report assembly from raw BigQuery data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import math


class MonthlyKPIService:
    """Service layer for KPI report generation."""
    
    def __init__(self, repository):
        """Initialize service with data repository."""
        self.repository = repository
    
    @staticmethod
    def r0(x: float) -> float:
        """Half-up rounding (parity with R type-7).
        
        Uses epsilon = 1e-9 to handle floating point gaps.
        Formula: floor(x + 0.5 + eps)
        """
        eps = 1e-9
        return math.floor(x + 0.5 + eps)
    
    @staticmethod
    def fmt_hm(minutes: int) -> str:
        """Format minutes as 'Hh MMmin'."""
        if minutes < 0:
            return "0min"
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}min"
        return f"{mins}min"
    
    @staticmethod
    def median_r7(values: List[float]) -> float:
        """R type-7 median: mean of two middles for even n."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        if n % 2 == 1:
            return sorted_vals[n // 2]
        mid1 = sorted_vals[n // 2 - 1]
        mid2 = sorted_vals[n // 2]
        return (mid1 + mid2) / 2.0
    
    def classify_status(
        self,
        score: float,
        active_minutes: int,
        role_avg_score: float,
        company_avg_score: float,
    ) -> str:
        """Classify employee status via triage cascade."""
        if active_minutes < 500:
            return "inactive"
        if score < (role_avg_score * 0.8):
            return "needs-attention"
        if score > (role_avg_score * 1.2):
            return "most-engaged"
        return "on-track"
    
    def assemble_report(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
        department: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assemble complete monthly KPI report."""
        raw_data = self.repository.query(domain_id, start_date, end_date, department, role)
        
        employees = raw_data.get("employees", [])
        role_avgs = raw_data.get("roleAverages", {})
        company_avg = raw_data.get("companyAverage", {})
        
        processed_employees = []
        status_counts = {"inactive": 0, "needs-attention": 0, "most-engaged": 0, "on-track": 0}
        
        for emp in employees:
            role = emp.get("role", "Unknown")
            role_avg_score = role_avgs.get(role, {}).get("score", company_avg.get("score", 75.0))
            
            status = self.classify_status(
                score=emp.get("score", 0),
                active_minutes=emp.get("activeMinutes", 0),
                role_avg_score=role_avg_score,
                company_avg_score=company_avg.get("score", 75.0),
            )
            
            emp["status"] = status
            status_counts[status] += 1
            processed_employees.append(emp)
        
        processed_employees.sort(key=lambda e: e.get("employee_id", ""))
        
        return {
            "header": {
                "title": "Monthly KPI Report",
                "company": f"Domain {domain_id}",
                "startDate": start_date,
                "endDate": end_date,
                "generatedAt": datetime.utcnow().isoformat() + "Z",
            },
            "employees": processed_employees,
            "filter_options": {
                "departments": list(set(e.get("department", "Unknown") for e in processed_employees)),
                "roles": list(set(e.get("role", "Unknown") for e in processed_employees)),
                "managers": list(set(e.get("manager") for e in processed_employees if e.get("manager"))),
                "employees": [{"id": e.get("employee_id"), "name": e.get("name")} for e in processed_employees],
            },
            "statusCounts": status_counts,
        }
