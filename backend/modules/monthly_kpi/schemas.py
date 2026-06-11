"""Pydantic models for Monthly KPI Report.

Data contracts matching REAL_DATA_SPEC.md exactly.
Every field type and structure must align with the injection template.
"""

from typing import Optional, List, Union, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class MetricRecord(BaseModel):
    """Individual metric in a section."""
    section: str = Field(..., description="Section: SCORE, WORK HABITS, MEETINGS, TECH MODULES, WEB BROWSER, MOST & LEAST PRODUCTIVE")
    label: str = Field(..., description="Metric label (e.g., 'Productivity Score')")
    value: Union[float, str, int] = Field(..., description="Metric value (number, percentage, duration, or '—')")
    roleAvg: Optional[Union[float, str, int]] = Field(None, description="Role-level average (same format as value, or '—')")

    class Config:
        use_enum_values = True


class EmployeeKPI(BaseModel):
    """Complete KPI profile for a single employee."""
    id: str = Field(..., alias="employee_id", description="Employee ID (string)")
    name: str = Field(..., description="Display name")
    dept: str = Field(..., description="Department")
    role: str = Field(..., description="Role (drives peer comparisons)")
    manager: str = Field(..., description="Manager name")
    score: int = Field(..., description="Overall score (0–100)")
    roleAvg: int = Field(..., description="Role average score")
    delta: str = Field(..., description="Signed delta string ('+44' or '-15')")
    activeTime: str = Field(..., description="Format: 'Hh MMmin' (e.g., '10h 49min')")
    trendCy: List[float] = Field(..., description="Sparkline points (~5–10 values)")
    trendColor: str = Field(..., description="CSS var: 'var(--blue-500)' or 'var(--red-500)'")
    status: Literal["needs-attention", "inactive", "most-engaged", "on-track"] = Field(..., description="Triage status")
    metrics: List[MetricRecord] = Field(..., description="Detailed metrics (all 6 sections)")

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True


class FilterOptions(BaseModel):
    """Available filter options for the report."""
    dept: List[str] = Field(default_factory=list, description="Unique departments")
    role: List[str] = Field(default_factory=list, description="Unique roles")
    manager: List[str] = Field(default_factory=list, description="Unique managers")
    employee: List[str] = Field(default_factory=list, description="Unique employee names")

    class Config:
        use_enum_values = True


class ReportHeader(BaseModel):
    """Report metadata."""
    title: str = Field(..., description="Report title")
    breadcrumb: str = Field(..., description="Company display name")
    dateRange: str = Field(..., description="Formatted date range string")
    dateFrom: str = Field(..., description="ISO date (YYYY-MM-DD)")
    dateTo: str = Field(..., description="ISO date (YYYY-MM-DD)")

    class Config:
        use_enum_values = True


class MonthlyKPIReport(BaseModel):
    """Complete Monthly KPI Report."""
    header: ReportHeader = Field(..., description="Report metadata")
    employees: List[EmployeeKPI] = Field(..., description="All employees (after triage)")
    filter_options: FilterOptions = Field(..., description="Unique filter values")
    statusCounts: Dict[str, int] = Field(..., description="Count per status")
    roleTab: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Role averages (optional)")

    class Config:
        use_enum_values = True


# Triage output enrichment (intermediate)
class TriageEmployee(BaseModel):
    """Employee record enriched with triage outputs."""
    employee_id: float = Field(..., description="Internal ID (float from BigQuery)")
    name: str
    role: str
    avg_score: float = Field(..., description="Raw score average")
    active_min: float = Field(..., description="Raw active minutes")
    days_active: int = Field(..., description="Days with activity")
    days_total: int = Field(..., description="Total working days")
    status: Optional[str] = Field(None, description="'inactive' | 'needs-attention' | 'most-engaged' | 'on-track'")
    severity: Optional[str] = Field(None, description="'CRITICAL' | 'HIGH' | 'MEDIUM' (flagged only)")
    tier: Optional[str] = Field(None, description="'STAR' | 'STRONG' | 'STABLE' (most-engaged only)")
    reason: Optional[str] = Field(None, description="Inactive reason string")

    class Config:
        use_enum_values = True
