"""Pydantic models for Monthly KPI Report.

Data contracts matching employees.json shape per REAL_DATA_SPEC.md
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class MetricRecord(BaseModel):
    """Individual metric record in a section."""
    section: str = Field(..., description="Section name (e.g., SCORE, WORK HABITS)")
    label: str = Field(..., description="Metric label (e.g., Productivity Score)")
    value: float = Field(..., description="Metric value")
    roleAvg: Optional[float] = Field(None, description="Role-level average")
    companyAvg: Optional[float] = Field(None, description="Company-level average")


class EmployeeKPI(BaseModel):
    """Complete KPI profile for a single employee."""
    employee_id: str
    name: str
    role: str
    manager: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    score: float
    activeMinutes: int
    status: str  # inactive | needs-attention | most-engaged | on-track
    metrics: List[MetricRecord]


class FilterOptions(BaseModel):
    """Available filter options for the report."""
    departments: List[str]
    roles: List[str]
    managers: List[str]
    employees: List[dict]  # {id, name}


class ReportHeader(BaseModel):
    """Metadata for the report."""
    title: str
    company: str
    startDate: str  # YYYY-MM-DD
    endDate: str    # YYYY-MM-DD
    generatedAt: str  # ISO 8601


class MonthlyKPIReport(BaseModel):
    """Complete Monthly KPI Report."""
    header: ReportHeader
    employees: List[EmployeeKPI]
    filter_options: FilterOptions
    statusCounts: dict  # {status: count}
