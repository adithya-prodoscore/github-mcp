"""Pydantic schemas for Monthly KPI Report."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class MonthlyKPIRequest(BaseModel):
    """Request parameters for monthly KPI report."""
    domain_id: int = Field(default=9, description="Prodoscore domain ID")
    start_date: str = Field(default="2026-05-01", description="Report start (YYYY-MM-DD)")
    end_date: str = Field(default="2026-05-29", description="Report end (YYYY-MM-DD)")
    department: Optional[str] = Field(default=None, description="Optional department filter")
    role: Optional[str] = Field(default=None, description="Optional role filter")
    manager: Optional[str] = Field(default=None, description="Optional manager filter")
    employee: Optional[str] = Field(default=None, description="Optional employee filter")


class EmployeeMetric(BaseModel):
    """Single metric entry in employee profile."""
    section: str
    label: str
    value: str
    roleAvg: Optional[str] = None


class EmployeeRecord(BaseModel):
    """Per-employee record in KPI report."""
    id: str
    name: str
    dept: str
    role: str
    manager: str
    score: int
    roleAvg: int
    delta: str
    activeTime: str
    trendCy: List[float]
    trendColor: str
    status: str
    metrics: List[EmployeeMetric]


class HeaderInfo(BaseModel):
    """Report header metadata."""
    title: str
    breadcrumb: str
    dateRange: str
    dateFrom: str
    dateTo: str


class FilterOptions(BaseModel):
    """Available filter values."""
    dept: List[str]
    role: List[str]
    manager: List[str]
    employee: List[str]


class StatusCounts(BaseModel):
    """Status distribution counts."""
    needs_attention: int = Field(default=0, alias="needs-attention")
    inactive: int = Field(default=0)
    most_engaged: int = Field(default=0, alias="most-engaged")
    on_track: int = Field(default=0, alias="on-track")

    class Config:
        populate_by_name = True


class MonthlyKPIResponse(BaseModel):
    """Complete monthly KPI report response."""
    header: HeaderInfo
    employees: List[EmployeeRecord]
    filter_options: FilterOptions
    statusCounts: StatusCounts
