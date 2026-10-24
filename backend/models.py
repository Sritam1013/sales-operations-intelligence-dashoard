"""
Pydantic models for the Sales & Operations Intelligence Dashboard.

Defines request/response schemas for all entities, KPIs, chart data,
filter parameters, and AI insights.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Entity models
# ---------------------------------------------------------------------------

class CRMLeadOut(BaseModel):
    """Represents a single CRM lead record."""
    id: Optional[int] = None
    lead_id: Optional[str] = None
    company: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    owner: Optional[str] = None
    region: Optional[str] = None
    deal_value: Optional[float] = None
    probability: Optional[float] = None
    created_date: Optional[str] = None
    last_activity: Optional[str] = None
    expected_close: Optional[str] = None
    notes: Optional[str] = None
    is_duplicate: Optional[int] = 0


class OperationsProjectOut(BaseModel):
    """Represents a single operations project record."""
    id: Optional[int] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    client_company: Optional[str] = None
    service_type: Optional[str] = None
    assigned_team: Optional[str] = None
    project_manager: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    deadline: Optional[str] = None
    budget: Optional[float] = None
    actual_cost: Optional[float] = None
    completion_percent: Optional[float] = None
    sla_status: Optional[str] = None
    region: Optional[str] = None
    notes: Optional[str] = None
    is_duplicate: Optional[int] = 0


class TargetForecastOut(BaseModel):
    """Represents a single target/forecast record."""
    id: Optional[int] = None
    month: Optional[str] = None
    year: Optional[int] = None
    owner: Optional[str] = None
    region: Optional[str] = None
    target_revenue: Optional[float] = None
    actual_revenue: Optional[float] = None
    target_leads: Optional[int] = None
    actual_leads: Optional[int] = None
    target_deals: Optional[int] = None
    actual_deals: Optional[int] = None
    notes: Optional[str] = None
    is_duplicate: Optional[int] = 0


# ---------------------------------------------------------------------------
# KPI models
# ---------------------------------------------------------------------------

class SalesKPIs(BaseModel):
    """Key performance indicators for the sales dashboard."""
    total_leads: int = 0
    conversion_rate: float = 0.0
    total_pipeline_value: float = 0.0
    avg_deal_size: float = 0.0
    leads_this_month: int = 0


class OperationsKPIs(BaseModel):
    """Key performance indicators for the operations dashboard."""
    total_projects: int = 0
    open_projects: int = 0
    overdue_projects: int = 0
    completed_projects: int = 0
    sla_compliance_pct: float = 0.0
    avg_project_value: float = 0.0


# ---------------------------------------------------------------------------
# Chart data models
# ---------------------------------------------------------------------------

class TimeSeriesPoint(BaseModel):
    """Single data point in a time-series chart."""
    period: str
    count: int = 0
    value: float = 0.0


class CategoryBreakdown(BaseModel):
    """A category with its count and optional value."""
    category: str
    count: int = 0
    value: float = 0.0


class StageConversion(BaseModel):
    """Funnel stage with conversion metrics."""
    stage: str
    count: int = 0
    value: float = 0.0
    conversion_rate: float = 0.0


class TargetVsActual(BaseModel):
    """Monthly target vs actual comparison."""
    period: str
    owner: Optional[str] = None
    region: Optional[str] = None
    target_revenue: float = 0.0
    actual_revenue: float = 0.0
    achievement_pct: float = 0.0


# ---------------------------------------------------------------------------
# Combined view
# ---------------------------------------------------------------------------

class CompanyCrossMatch(BaseModel):
    """A company that appears in both CRM and Operations data."""
    company: str
    crm_leads: list[CRMLeadOut] = []
    operations_projects: list[OperationsProjectOut] = []


# ---------------------------------------------------------------------------
# AI Insights
# ---------------------------------------------------------------------------

class InsightRecord(BaseModel):
    """A single AI-generated insight."""
    insight_type: str
    title: str
    description: str
    severity: str = Field(..., pattern="^(info|warning|critical)$")
    metric_value: Optional[float | str] = None
    linked_data: list[dict[str, Any]] = []
    recommendation: str = ""


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

class DataQualitySummary(BaseModel):
    """Summary of data quality metrics across all sources."""
    crm_missing: dict[str, int] = {}
    ops_missing: dict[str, int] = {}
    targets_missing: dict[str, int] = {}
    crm_duplicates: int = 0
    ops_duplicates: int = 0
    targets_duplicates: int = 0
    unmatched_crm_companies: int = 0
    unmatched_ops_companies: int = 0


class UnmatchedRecord(BaseModel):
    """A record that couldn't be matched across data sources."""
    source: str
    company: Optional[str] = None
    record_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Data load status
# ---------------------------------------------------------------------------

class DataLoadStatus(BaseModel):
    """Current data load status."""
    last_loaded_at: Optional[str] = None
    record_counts: dict[str, int] = {}
    load_details: list[dict[str, Any]] = []


class DataLoadResult(BaseModel):
    """Result of a data load operation."""
    results: list[dict[str, Any]] = []
    message: str = ""


# ---------------------------------------------------------------------------
# Filter options
# ---------------------------------------------------------------------------

class FilterOptions(BaseModel):
    """All available filter values."""
    owners: list[str] = []
    sources: list[str] = []
    regions: list[str] = []
    statuses: list[str] = []
    stages: list[str] = []
    clients: list[str] = []
    service_types: list[str] = []
    teams: list[str] = []
    priorities: list[str] = []
