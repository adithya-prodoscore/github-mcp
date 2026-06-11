"""BigQuery data access layer for Monthly KPI Report.

Executes 11 parameterized SQL queries (01–09, 11, 12) and fetches manager/company data.
Mock fallback for development without BigQuery access.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import date
import logging

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None

logger = logging.getLogger(__name__)


class MonthlyKPIRepository:
    """Data access layer for monthly KPI metrics."""

    def __init__(self, project: str = "prodoscore-prodolab-live", client=None):
        """Initialize repository with BigQuery client (gcloud ADC auth)."""
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
        """Execute KPI query and return aggregated results.

        Executes 11 parameterized BigQuery queries (01–09, 11, 12).

        Args:
            domain_id: Prodoscore domain ID
            start_date: Report start (YYYY-MM-DD)
            end_date: Report end (YYYY-MM-DD)
            department: Optional department filter (post-query)
            role: Optional role filter (post-query)
            manager: Optional manager filter (post-query)
            employee: Optional employee filter (post-query)

        Returns:
            Dictionary with employees, roleAverages, companyAverage, metadata
        """
        if self.use_mock:
            logger.info("[repository] Using mock data (no BigQuery client)")
            return self._mock_data(domain_id, start_date, end_date)

        logger.info(f"[repository] Querying domain={domain_id} window={start_date}..{end_date}")

        try:
            # Run all 11 queries
            core = self._run_sql("01_employee_core.sql", domain_id, start_date, end_date)
            tech = self._run_sql("02_tech_modules.sql", domain_id, start_date, end_date)
            meet = self._run_sql("03_meetings.sql", domain_id, start_date, end_date)
            avg = self._run_sql("04_averages.sql", domain_id, start_date, end_date)
            techavg = self._run_sql("05_tech_module_averages.sql", domain_id, start_date, end_date)
            meetavg = self._run_sql("06_meeting_averages.sql", domain_id, start_date, end_date)
            habit = self._run_sql("07_work_habits.sql", domain_id, start_date, end_date)
            poptime = self._run_sql("08_meeting_popular_time.sql", domain_id, start_date, end_date)
            web = self._run_sql("09_web_browser.sql", domain_id, start_date, end_date)
            wkscore = self._run_sql("11_score_weekday.sql", domain_id, start_date, end_date)
            prod = self._run_sql("12_most_least_productive.sql", domain_id, start_date, end_date)

            # Fetch manager lookup
            mgr_lookup = self._fetch_manager_lookup(domain_id)

            # Fetch company name
            company_name = self._fetch_company_name(domain_id)

            # Aggregate role averages
            role_averages = self._build_role_averages(avg, techavg, meetavg)
            company_average = self._build_company_average(avg)

            # Return aggregated structure
            return {
                "employees": core,
                "tech_modules": tech,
                "meetings": meet,
                "work_habits": habit,
                "popular_times": poptime,
                "web_browser": web,
                "weekday_scores": wkscore,
                "productivity": prod,
                "manager_lookup": mgr_lookup,
                "company_name": company_name,
                "roleAverages": role_averages,
                "companyAverage": company_average,
            }
        except Exception as e:
            logger.error(f"[repository] BigQuery error: {e}")
            logger.info("[repository] Falling back to mock data")
            return self._mock_data(domain_id, start_date, end_date)

    def _run_sql(self, filename: str, domain_id: int, start_date: str, end_date: str) -> List[dict]:
        """Run one SQL query from sql/ directory."""
        if not bigquery:
            raise RuntimeError("google-cloud-bigquery not installed")

        sql_dir = os.path.join(os.path.dirname(__file__), "sql")
        sql_path = os.path.join(sql_dir, filename)

        if not os.path.exists(sql_path):
            logger.warning(f"[repository] SQL file not found: {sql_path}")
            return []

        try:
            with open(sql_path) as f:
                sql = f.read()

            cfg = bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
                bigquery.ScalarQueryParameter("start", "DATE", date.fromisoformat(start_date)),
                bigquery.ScalarQueryParameter("end", "DATE", date.fromisoformat(end_date)),
            ])
            rows = [dict(r) for r in self.client.query(sql, job_config=cfg).result()]
            logger.info(f"  [sql] {filename:<32} {len(rows)} rows")
            return rows
        except Exception as e:
            logger.error(f"[repository] Error running {filename}: {e}")
            return []

    def _fetch_manager_lookup(self, domain_id: int) -> Dict[int, str]:
        """Fetch employee ID → fullname mapping for all employees in domain."""
        if not bigquery:
            return {}

        try:
            sql = """
            SELECT id, fullname FROM `{}.{}.latest_employee_records`
            WHERE domain_id = @domain_id
            """.format(self.project, self.dataset)
            cfg = bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id)
            ])
            rows = [dict(r) for r in self.client.query(sql, job_config=cfg).result()]
            return {r["id"]: r["fullname"] for r in rows if r.get("fullname")}
        except Exception as e:
            logger.error(f"[repository] Manager lookup error: {e}")
            return {}

    def _fetch_company_name(self, domain_id: int) -> str:
        """Fetch company display name (domain title)."""
        if not bigquery:
            return f"Domain {domain_id}"

        try:
            sql = """
            SELECT title FROM `{}.{}.latest_domain_records`
            WHERE id = @domain_id LIMIT 1
            """.format(self.project, self.dataset)
            cfg = bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id)
            ])
            rows = [dict(r) for r in self.client.query(sql, job_config=cfg).result()]
            title = rows[0]["title"] if rows and rows[0].get("title") else None
            return title if title else f"Domain {domain_id}"
        except Exception as e:
            logger.error(f"[repository] Company name lookup error: {e}")
            return f"Domain {domain_id}"

    def _build_role_averages(self, avg: list, techavg: list, meetavg: list) -> Dict[str, Dict]:
        """Build role average lookups from query results."""
        role_avgs = {}
        for row in avg:
            role = row.get("role", "Unknown")
            role_avgs[role] = {
                "score": row.get("role_score", 0),
                "activeTime": row.get("role_active_min", 0),
            }
        return role_avgs

    def _build_company_average(self, avg: list) -> Dict[str, Any]:
        """Build company-level averages."""
        if not avg:
            return {"score": 0, "activeTime": 0}
        company_row = next((r for r in avg if r.get("role") == "(COMPANY)"), None)
        if company_row:
            return {
                "score": company_row.get("role_score", 0),
                "activeTime": company_row.get("role_active_min", 0),
            }
        return {"score": 0, "activeTime": 0}

    def _mock_data(self, domain_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """Return mock data for development and testing."""
        logger.info(f"[repository] Mock data: domain={domain_id} {start_date}..{end_date}")
        return {
            "employees": [
                {
                    "employee_id": 1001.0,
                    "name": "Alice Johnson",
                    "dept": "Sales",
                    "role": "Manager",
                    "manager_id": 5001,
                    "avg_score": 87.5,
                    "avg_active_min_raw": 2150,
                    "days_active": 22,
                    "days_counted": 22,
                },
                {
                    "employee_id": 1002.0,
                    "name": "Bob Smith",
                    "dept": "Engineering",
                    "role": "Engineer",
                    "manager_id": 5002,
                    "avg_score": 72.3,
                    "avg_active_min_raw": 1850,
                    "days_active": 18,
                    "days_counted": 22,
                },
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
            "roleAverages": {
                "Manager": {"score": 80, "activeTime": 2000},
                "Engineer": {"score": 75, "activeTime": 1800},
            },
            "companyAverage": {"score": 76, "activeTime": 1900},
        }
