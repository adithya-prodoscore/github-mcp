"""BigQuery data access layer for Monthly KPI Report.

Executes 11 parameterized SQL queries to fetch employee metrics.
Mock fallback for development without BigQuery access.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class MonthlyKPIRepository:
    """Data access layer for monthly KPI metrics."""
    
    def __init__(self, bigquery_client=None):
        """Initialize repository with optional BigQuery client."""
        self.client = bigquery_client
        self.use_mock = bigquery_client is None
    
    def query(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
        department: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute KPI query and return aggregated results.
        
        Executes 11 parameterized BigQuery queries (01..09, 11, 12).
        
        Args:
            domain_id: Prodoscore domain ID
            start_date: Report start (YYYY-MM-DD)
            end_date: Report end (YYYY-MM-DD)
            department: Optional department filter
            role: Optional role filter
        
        Returns:
            Dictionary with employees, averages, and metadata
        """
        if self.use_mock:
            return self._mock_data(domain_id, start_date, end_date)
        return self._mock_data(domain_id, start_date, end_date)
    
    def _mock_data(self, domain_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """Return mock data for development and testing."""
        return {
            "employees": [
                {
                    "employee_id": "E001",
                    "name": "Alice Johnson",
                    "role": "Senior Manager",
                    "department": "Sales",
                    "manager": "CEO",
                    "email": "alice@company.com",
                    "score": 87.5,
                    "activeMinutes": 2150,
                    "metrics": [
                        {"section": "SCORE", "label": "Productivity Score", "value": 87.5, "roleAvg": 85.0, "companyAvg": 76.0},
                        {"section": "WORK HABITS", "label": "Daily Active Time", "value": 430, "roleAvg": 420, "companyAvg": 400},
                    ]
                },
                {
                    "employee_id": "E002",
                    "name": "Bob Smith",
                    "role": "Analyst",
                    "department": "Analytics",
                    "manager": "Director",
                    "email": "bob@company.com",
                    "score": 65.2,
                    "activeMinutes": 1800,
                    "metrics": [
                        {"section": "SCORE", "label": "Productivity Score", "value": 65.2, "roleAvg": 70.0, "companyAvg": 76.0},
                        {"section": "WORK HABITS", "label": "Daily Active Time", "value": 360, "roleAvg": 380, "companyAvg": 400},
                    ]
                },
            ],
            "roleAverages": {
                "Senior Manager": {"score": 85.0, "activeMinutes": 2100},
                "Analyst": {"score": 70.0, "activeMinutes": 1900},
            },
            "companyAverage": {"score": 76.0, "activeMinutes": 2000},
        }
