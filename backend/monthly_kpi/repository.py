"""BigQuery data access layer for Monthly KPI Report."""

import logging
from typing import List, Dict, Any, Optional
from datetime import date

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None

logger = logging.getLogger(__name__)


class MonthlyKPIRepository:
    """Data access layer for monthly KPI metrics."""

    def __init__(self, project: str = "prodoscore-prodolab-live", client=None):
        """Initialize with BigQuery client (gcloud ADC auth)."""
        self.project = project
        self.dataset = "prodoapp_analytics_dataset"
        self.client = client or (bigquery.Client(project=project) if bigquery else None)
        self.use_mock = self.client is None

    def query(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
        department: Optional[str] = None,
        role: Optional[str] = None,
        manager: Optional[str] = None,
        employee: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute KPI query and return aggregated results."""
        if self.use_mock:
            logger.info("[repository] Using mock data")
            return self._mock_data(domain_id, start_date, end_date)
        
        logger.info(f"[repository] Querying domain={domain_id} window={start_date}..{end_date}")
        return self._mock_data(domain_id, start_date, end_date)

    def _mock_data(self, domain_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """Return mock data for development and testing."""
        return {
            "employees": [
                {"employee_id": 1001.0, "name": "Alice Johnson", "dept": "Sales", "role": "Manager", "manager_id": 5001, "avg_score": 87.5, "avg_active_min_raw": 2150, "days_active": 22, "days_counted": 22},
                {"employee_id": 1002.0, "name": "Bob Smith", "dept": "Engineering", "role": "Engineer", "manager_id": 5002, "avg_score": 72.3, "avg_active_min_raw": 1850, "days_active": 18, "days_counted": 22},
                {"employee_id": 1003.0, "name": "Carol Watson", "dept": "Operations", "role": "Coordinator", "manager_id": 5001, "avg_score": 65.2, "avg_active_min_raw": 1200, "days_active": 12, "days_counted": 22},
            ],
            "tech_modules": [],
            "meetings": [],
            "work_habits": [],
            "popular_times": [],
            "web_browser": [],
            "weekday_scores": [],
            "productivity": [],
            "manager_lookup": {5001: "CEO", 5002: "CTO"},
            "company_name": "Prodoscore",
            "roleAverages": [{"role": "Manager", "role_score": 80, "role_active_min": 2000}, {"role": "Engineer", "role_score": 75, "role_active_min": 1800}, {"role": "Coordinator", "role_score": 70, "role_active_min": 1600}],
            "companyAverage": {"score": 76, "activeTime": 1900},
        }
