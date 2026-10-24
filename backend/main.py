"""
FastAPI application for the Sales & Operations Intelligence Dashboard.

Provides REST API endpoints for sales KPIs, operations metrics,
combined views, AI insights, data quality, and filter options.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from database import _get_connection, init_db, load_all_data, get_last_load_info
from insights import generate_all_insights, generate_insight, ALL_GENERATORS
from models import (
    SalesKPIs, OperationsKPIs,
    TimeSeriesPoint, CategoryBreakdown, StageConversion, TargetVsActual,
    CompanyCrossMatch, CRMLeadOut, OperationsProjectOut,
    InsightRecord, DataQualitySummary, UnmatchedRecord,
    DataLoadStatus, DataLoadResult, FilterOptions,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Sales & Operations Intelligence Dashboard API",
    description="Backend API powering the Sales & Operations Intelligence Dashboard.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rows(cursor) -> list[dict]:
    return [dict(r) for r in cursor.fetchall()]


def _build_crm_where(
    date_from: str | None, date_to: str | None,
    owner: str | None, source: str | None,
    region: str | None, status: str | None,
) -> tuple[str, list]:
    """Build WHERE clause fragments for CRM leads filtering."""
    clauses: list[str] = []
    params: list = []
    if date_from:
        clauses.append("created_date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("created_date <= ?")
        params.append(date_to)
    if owner:
        clauses.append("owner = ?")
        params.append(owner)
    if source:
        clauses.append("source = ?")
        params.append(source)
    if region:
        clauses.append("region = ?")
        params.append(region)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


def _build_ops_where(
    date_from: str | None, date_to: str | None,
    status: str | None, client: str | None,
    service_type: str | None, team: str | None,
    region: str | None,
) -> tuple[str, list]:
    """Build WHERE clause fragments for operations projects filtering."""
    clauses: list[str] = []
    params: list = []
    if date_from:
        clauses.append("start_date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("start_date <= ?")
        params.append(date_to)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if client:
        clauses.append("client_company = ?")
        params.append(client)
    if service_type:
        clauses.append("service_type = ?")
        params.append(service_type)
    if team:
        clauses.append("assigned_team = ?")
        params.append(team)
    if region:
        clauses.append("region = ?")
        params.append(region)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


def _build_targets_where(
    date_from: str | None, date_to: str | None,
    owner: str | None, region: str | None,
) -> tuple[str, list]:
    """Build WHERE clause fragments for targets/forecasts filtering."""
    clauses: list[str] = []
    params: list = []
    if owner:
        clauses.append("owner = ?")
        params.append(owner)
    if region:
        clauses.append("region = ?")
        params.append(region)
    # For targets we filter by year/month derived from date_from/date_to
    if date_from:
        # e.g. "2024-01-01" → year >= 2024
        try:
            dt = datetime.strptime(date_from, "%Y-%m-%d")
            clauses.append("(year > ? OR (year = ? AND month >= ?))")
            params.extend([dt.year, dt.year, dt.strftime("%B")])
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d")
            clauses.append("(year < ? OR (year = ? AND month <= ?))")
            params.extend([dt.year, dt.year, dt.strftime("%B")])
        except ValueError:
            pass
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


# ---------------------------------------------------------------------------
# Data Loading Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/data/load", response_model=DataLoadResult, tags=["Data Loading"])
def api_load_data():
    """Load or reload all data from source files into SQLite."""
    try:
        init_db()
        results = load_all_data()
        return DataLoadResult(results=results, message="Data loaded successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {e}")


@app.get("/api/data/status", response_model=DataLoadStatus, tags=["Data Loading"])
def api_data_status():
    """Return last load time, record counts, and data quality summary."""
    try:
        info = get_last_load_info()
        return DataLoadStatus(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Sales Dashboard Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/sales/kpis", response_model=SalesKPIs, tags=["Sales Dashboard"])
def sales_kpis(
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    owner: Optional[str] = None,
    source: Optional[str] = None,
    region: Optional[str] = None,
    status: Optional[str] = None,
):
    """Return sales key performance indicators."""
    where, params = _build_crm_where(date_from, date_to, owner, source, region, status)
    conn = _get_connection()
    row = conn.execute(
        f"SELECT COUNT(*) AS total_leads, "
        f"COALESCE(SUM(deal_value), 0) AS total_pipeline_value, "
        f"COALESCE(AVG(deal_value), 0) AS avg_deal_size "
        f"FROM crm_leads{where}", params
    ).fetchone()

    won = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM crm_leads{where}"
        + (" AND " if where else " WHERE ") + "stage IN ('Closed Won', 'Won')",
        params
    ).fetchone()["cnt"]

    latest_lead = conn.execute(
        f"SELECT MAX(created_date) AS m FROM crm_leads{where}", params
    ).fetchone()["m"]
    month_start = (latest_lead[:7] + "-01") if latest_lead else datetime.utcnow().strftime("%Y-%m-01")
    this_month = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM crm_leads{where}"
        + (" AND " if where else " WHERE ") + "created_date >= ?",
        params + [month_start]
    ).fetchone()["cnt"]
    conn.close()

    total = row["total_leads"]
    conversion = (won / total * 100) if total > 0 else 0

    return SalesKPIs(
        total_leads=total,
        conversion_rate=round(conversion, 2),
        total_pipeline_value=row["total_pipeline_value"],
        avg_deal_size=round(row["avg_deal_size"], 2),
        leads_this_month=this_month,
    )


@app.get("/api/sales/leads-over-time", response_model=list[TimeSeriesPoint], tags=["Sales Dashboard"])
def sales_leads_over_time(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    owner: Optional[str] = None, source: Optional[str] = None,
    region: Optional[str] = None, status: Optional[str] = None,
):
    """Return leads grouped by month for line chart."""
    where, params = _build_crm_where(date_from, date_to, owner, source, region, status)
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT strftime('%Y-%m', created_date) AS period, COUNT(*) AS count, "
        f"COALESCE(SUM(deal_value), 0) AS value "
        f"FROM crm_leads{where} AND created_date IS NOT NULL "
        f"GROUP BY period ORDER BY period"
        if where else
        "SELECT strftime('%Y-%m', created_date) AS period, COUNT(*) AS count, "
        "COALESCE(SUM(deal_value), 0) AS value "
        "FROM crm_leads WHERE created_date IS NOT NULL "
        "GROUP BY period ORDER BY period",
        params
    ).fetchall()
    conn.close()
    return [TimeSeriesPoint(**dict(r)) for r in rows]


@app.get("/api/sales/leads-by-source", response_model=list[CategoryBreakdown], tags=["Sales Dashboard"])
def sales_leads_by_source(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    owner: Optional[str] = None, source: Optional[str] = None,
    region: Optional[str] = None, status: Optional[str] = None,
):
    """Return lead count by source for pie/bar chart."""
    where, params = _build_crm_where(date_from, date_to, owner, source, region, status)
    extra = " AND source IS NOT NULL" if where else " WHERE source IS NOT NULL"
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT source AS category, COUNT(*) AS count, COALESCE(SUM(deal_value), 0) AS value "
        f"FROM crm_leads{where}{extra} GROUP BY source ORDER BY count DESC",
        params
    ).fetchall()
    conn.close()
    return [CategoryBreakdown(**dict(r)) for r in rows]


@app.get("/api/sales/leads-by-stage", response_model=list[CategoryBreakdown], tags=["Sales Dashboard"])
def sales_leads_by_stage(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    owner: Optional[str] = None, source: Optional[str] = None,
    region: Optional[str] = None, status: Optional[str] = None,
):
    """Return lead count and value by pipeline stage for funnel chart."""
    where, params = _build_crm_where(date_from, date_to, owner, source, region, status)
    extra = " AND stage IS NOT NULL" if where else " WHERE stage IS NOT NULL"
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT stage AS category, COUNT(*) AS count, COALESCE(SUM(deal_value), 0) AS value "
        f"FROM crm_leads{where}{extra} GROUP BY stage ORDER BY count DESC",
        params
    ).fetchall()
    conn.close()
    return [CategoryBreakdown(**dict(r)) for r in rows]


@app.get("/api/sales/leads-by-owner", response_model=list[CategoryBreakdown], tags=["Sales Dashboard"])
def sales_leads_by_owner(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    owner: Optional[str] = None, source: Optional[str] = None,
    region: Optional[str] = None, status: Optional[str] = None,
):
    """Return lead count and value by owner for bar chart."""
    where, params = _build_crm_where(date_from, date_to, owner, source, region, status)
    extra = " AND owner IS NOT NULL" if where else " WHERE owner IS NOT NULL"
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT owner AS category, COUNT(*) AS count, COALESCE(SUM(deal_value), 0) AS value "
        f"FROM crm_leads{where}{extra} GROUP BY owner ORDER BY value DESC",
        params
    ).fetchall()
    conn.close()
    return [CategoryBreakdown(**dict(r)) for r in rows]


@app.get("/api/sales/leads-by-region", response_model=list[CategoryBreakdown], tags=["Sales Dashboard"])
def sales_leads_by_region(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    owner: Optional[str] = None, source: Optional[str] = None,
    region: Optional[str] = None, status: Optional[str] = None,
):
    """Return lead count and value by region for bar chart."""
    where, params = _build_crm_where(date_from, date_to, owner, source, region, status)
    extra = " AND region IS NOT NULL" if where else " WHERE region IS NOT NULL"
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT region AS category, COUNT(*) AS count, COALESCE(SUM(deal_value), 0) AS value "
        f"FROM crm_leads{where}{extra} GROUP BY region ORDER BY value DESC",
        params
    ).fetchall()
    conn.close()
    return [CategoryBreakdown(**dict(r)) for r in rows]


@app.get("/api/sales/stage-conversion", response_model=list[StageConversion], tags=["Sales Dashboard"])
def sales_stage_conversion(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    owner: Optional[str] = None, source: Optional[str] = None,
    region: Optional[str] = None, status: Optional[str] = None,
):
    """Return stage conversion rates for funnel chart."""
    where, params = _build_crm_where(date_from, date_to, owner, source, region, status)
    extra = " AND stage IS NOT NULL" if where else " WHERE stage IS NOT NULL"
    conn = _get_connection()

    total_leads = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM crm_leads{where}", params
    ).fetchone()["cnt"]

    rows = conn.execute(
        f"SELECT stage, COUNT(*) AS count, COALESCE(SUM(deal_value), 0) AS value "
        f"FROM crm_leads{where}{extra} GROUP BY stage ORDER BY count DESC",
        params
    ).fetchall()
    conn.close()

    # Define a standard funnel order (fallback to data order)
    funnel_order = [
        "New", "Lead", "Prospect", "Qualification", "Qualified",
        "Proposal", "Negotiation", "Closed Won", "Won", "Closed Lost", "Lost",
    ]
    stage_data = {r["stage"]: dict(r) for r in rows}

    result = []
    for stage in funnel_order:
        if stage in stage_data:
            d = stage_data.pop(stage)
            rate = (d["count"] / total_leads * 100) if total_leads > 0 else 0
            result.append(StageConversion(stage=stage, count=d["count"], value=d["value"], conversion_rate=round(rate, 2)))
    # Append any remaining stages not in the standard order
    for stage, d in stage_data.items():
        rate = (d["count"] / total_leads * 100) if total_leads > 0 else 0
        result.append(StageConversion(stage=stage, count=d["count"], value=d["value"], conversion_rate=round(rate, 2)))

    return result


@app.get("/api/sales/stale-leads", response_model=list[CRMLeadOut], tags=["Sales Dashboard"])
def sales_stale_leads(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    owner: Optional[str] = None, source: Optional[str] = None,
    region: Optional[str] = None, status: Optional[str] = None,
):
    """Return leads with last_activity > 90 days ago that are still Active."""
    where, params = _build_crm_where(date_from, date_to, owner, source, region, status)
    conn = _get_connection()
    max_act_row = conn.execute(f"SELECT MAX(last_activity) AS m FROM crm_leads{where}", params).fetchone()
    max_act = max_act_row["m"] if max_act_row else None
    if max_act:
        ref_dt = datetime.strptime(max_act, "%Y-%m-%d")
    else:
        ref_dt = datetime.utcnow()
    cutoff = (ref_dt - __import__("datetime").timedelta(days=90)).strftime("%Y-%m-%d")
    stale_clause = "status = 'Active' AND last_activity IS NOT NULL AND last_activity < ?"
    if where:
        full_where = f"{where} AND {stale_clause}"
    else:
        full_where = f" WHERE {stale_clause}"
    params.append(cutoff)
    rows = conn.execute(f"SELECT * FROM crm_leads{full_where}", params).fetchall()
    conn.close()
    return [CRMLeadOut(**dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Operations Dashboard Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/operations/kpis", response_model=OperationsKPIs, tags=["Operations Dashboard"])
def operations_kpis(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    status: Optional[str] = None, client: Optional[str] = None,
    service_type: Optional[str] = None, team: Optional[str] = None,
    region: Optional[str] = None,
):
    """Return operations key performance indicators."""
    where, params = _build_ops_where(date_from, date_to, status, client, service_type, team, region)
    conn = _get_connection()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    row = conn.execute(
        f"SELECT COUNT(*) AS total, COALESCE(AVG(budget), 0) AS avg_val FROM operations_projects{where}", params
    ).fetchone()

    open_cnt = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM operations_projects{where}"
        + (" AND " if where else " WHERE ")
        + "status NOT IN ('Completed', 'Closed', 'Done')",
        params
    ).fetchone()["cnt"]

    completed_cnt = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM operations_projects{where}"
        + (" AND " if where else " WHERE ")
        + "status IN ('Completed', 'Closed', 'Done')",
        params
    ).fetchone()["cnt"]

    overdue_cnt = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM operations_projects{where}"
        + (" AND " if where else " WHERE ")
        + "status = 'Overdue'",
        params
    ).fetchone()["cnt"]

    total_for_sla = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM operations_projects{where}"
        + (" AND " if where else " WHERE ")
        + "sla_status IS NOT NULL",
        params
    ).fetchone()["cnt"]

    met_sla = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM operations_projects{where}"
        + (" AND " if where else " WHERE ")
        + "sla_status IN ('Met', 'On Track', 'Compliant', 'Within SLA')",
        params
    ).fetchone()["cnt"]
    conn.close()

    sla_pct = (met_sla / total_for_sla * 100) if total_for_sla > 0 else 0

    return OperationsKPIs(
        total_projects=row["total"],
        open_projects=open_cnt,
        overdue_projects=overdue_cnt,
        completed_projects=completed_cnt,
        sla_compliance_pct=round(sla_pct, 2),
        avg_project_value=round(row["avg_val"], 2),
    )


@app.get("/api/operations/projects-by-status", response_model=list[CategoryBreakdown], tags=["Operations Dashboard"])
def ops_projects_by_status(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    status: Optional[str] = None, client: Optional[str] = None,
    service_type: Optional[str] = None, team: Optional[str] = None,
    region: Optional[str] = None,
):
    """Return project count by status for donut chart."""
    where, params = _build_ops_where(date_from, date_to, status, client, service_type, team, region)
    extra = " AND status IS NOT NULL" if where else " WHERE status IS NOT NULL"
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT status AS category, COUNT(*) AS count, COALESCE(SUM(budget), 0) AS value "
        f"FROM operations_projects{where}{extra} GROUP BY status ORDER BY count DESC",
        params
    ).fetchall()
    conn.close()
    return [CategoryBreakdown(**dict(r)) for r in rows]


@app.get("/api/operations/projects-over-time", response_model=list[TimeSeriesPoint], tags=["Operations Dashboard"])
def ops_projects_over_time(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    status: Optional[str] = None, client: Optional[str] = None,
    service_type: Optional[str] = None, team: Optional[str] = None,
    region: Optional[str] = None,
):
    """Return projects created by month for line chart."""
    where, params = _build_ops_where(date_from, date_to, status, client, service_type, team, region)
    date_filter = " AND start_date IS NOT NULL" if where else " WHERE start_date IS NOT NULL"
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT strftime('%Y-%m', start_date) AS period, COUNT(*) AS count, "
        f"COALESCE(SUM(budget), 0) AS value "
        f"FROM operations_projects{where}{date_filter} GROUP BY period ORDER BY period",
        params
    ).fetchall()
    conn.close()
    return [TimeSeriesPoint(**dict(r)) for r in rows]


@app.get("/api/operations/workload-by-team", response_model=list[CategoryBreakdown], tags=["Operations Dashboard"])
def ops_workload_by_team(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    status: Optional[str] = None, client: Optional[str] = None,
    service_type: Optional[str] = None, team: Optional[str] = None,
    region: Optional[str] = None,
):
    """Return project count/value by assigned team for bar chart."""
    where, params = _build_ops_where(date_from, date_to, status, client, service_type, team, region)
    extra = " AND assigned_team IS NOT NULL" if where else " WHERE assigned_team IS NOT NULL"
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT assigned_team AS category, COUNT(*) AS count, COALESCE(SUM(budget), 0) AS value "
        f"FROM operations_projects{where}{extra} GROUP BY assigned_team ORDER BY value DESC",
        params
    ).fetchall()
    conn.close()
    return [CategoryBreakdown(**dict(r)) for r in rows]


@app.get("/api/operations/workload-by-service", response_model=list[CategoryBreakdown], tags=["Operations Dashboard"])
def ops_workload_by_service(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    status: Optional[str] = None, client: Optional[str] = None,
    service_type: Optional[str] = None, team: Optional[str] = None,
    region: Optional[str] = None,
):
    """Return project count by service type for bar chart."""
    where, params = _build_ops_where(date_from, date_to, status, client, service_type, team, region)
    extra = " AND service_type IS NOT NULL" if where else " WHERE service_type IS NOT NULL"
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT service_type AS category, COUNT(*) AS count, COALESCE(SUM(budget), 0) AS value "
        f"FROM operations_projects{where}{extra} GROUP BY service_type ORDER BY count DESC",
        params
    ).fetchall()
    conn.close()
    return [CategoryBreakdown(**dict(r)) for r in rows]


@app.get("/api/operations/sla-overview", response_model=list[CategoryBreakdown], tags=["Operations Dashboard"])
def ops_sla_overview(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    status: Optional[str] = None, client: Optional[str] = None,
    service_type: Optional[str] = None, team: Optional[str] = None,
    region: Optional[str] = None,
):
    """Return SLA status breakdown for donut chart."""
    where, params = _build_ops_where(date_from, date_to, status, client, service_type, team, region)
    extra = " AND sla_status IS NOT NULL" if where else " WHERE sla_status IS NOT NULL"
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT sla_status AS category, COUNT(*) AS count, COALESCE(SUM(budget), 0) AS value "
        f"FROM operations_projects{where}{extra} GROUP BY sla_status ORDER BY count DESC",
        params
    ).fetchall()
    conn.close()
    return [CategoryBreakdown(**dict(r)) for r in rows]


@app.get("/api/operations/targets-vs-actuals", response_model=list[TargetVsActual], tags=["Operations Dashboard"])
def ops_targets_vs_actuals(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    owner: Optional[str] = None, region: Optional[str] = None,
):
    """Return monthly targets vs actuals by owner/region for bar chart."""
    where, params = _build_targets_where(date_from, date_to, owner, region)
    conn = _get_connection()
    rows = conn.execute(
        f"SELECT month, year, owner, region, "
        f"COALESCE(target_revenue, 0) AS target_revenue, "
        f"COALESCE(actual_revenue, 0) AS actual_revenue "
        f"FROM targets_forecasts{where} ORDER BY year, month",
        params
    ).fetchall()
    conn.close()

    result = []
    for r in rows:
        period = f"{r['year']}-{r['month']}" if r['year'] and r['month'] else "Unknown"
        target = r["target_revenue"]
        actual = r["actual_revenue"]
        pct = (actual / target * 100) if target > 0 else 0
        result.append(TargetVsActual(
            period=period, owner=r["owner"], region=r["region"],
            target_revenue=target, actual_revenue=actual,
            achievement_pct=round(pct, 2),
        ))
    return result


@app.get("/api/operations/overdue-projects", response_model=list[OperationsProjectOut], tags=["Operations Dashboard"])
def ops_overdue_projects(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    status: Optional[str] = None, client: Optional[str] = None,
    service_type: Optional[str] = None, team: Optional[str] = None,
    region: Optional[str] = None,
):
    """Return list of overdue projects."""
    where, params = _build_ops_where(date_from, date_to, status, client, service_type, team, region)
    overdue_clause = "status = 'Overdue'"
    if where:
        full = f"{where} AND {overdue_clause}"
    else:
        full = f" WHERE {overdue_clause}"
    conn = _get_connection()
    rows = conn.execute(f"SELECT * FROM operations_projects{full}", params).fetchall()
    conn.close()
    return [OperationsProjectOut(**dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Combined View Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/combined/sales-to-ops", response_model=list[CompanyCrossMatch], tags=["Combined View"])
def combined_sales_to_ops(
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    owner: Optional[str] = None, source: Optional[str] = None,
    region: Optional[str] = None, status: Optional[str] = None,
    client: Optional[str] = None, service_type: Optional[str] = None,
    team: Optional[str] = None,
):
    """Return companies appearing in both CRM and Operations with their data."""
    conn = _get_connection()
    # Get matched companies via case-insensitive comparison
    crm_rows = conn.execute("SELECT * FROM crm_leads WHERE company IS NOT NULL").fetchall()
    ops_rows = conn.execute("SELECT * FROM operations_projects WHERE client_company IS NOT NULL").fetchall()
    conn.close()

    # Build company → records mapping
    crm_by_company: dict[str, list[dict]] = {}
    for r in crm_rows:
        key = r["company"].lower()
        crm_by_company.setdefault(key, []).append(dict(r))

    ops_by_company: dict[str, list[dict]] = {}
    for r in ops_rows:
        key = r["client_company"].lower()
        ops_by_company.setdefault(key, []).append(dict(r))

    matched = set(crm_by_company.keys()) & set(ops_by_company.keys())

    result = []
    for company in sorted(matched):
        result.append(CompanyCrossMatch(
            company=company.title(),
            crm_leads=[CRMLeadOut(**lead) for lead in crm_by_company[company]],
            operations_projects=[OperationsProjectOut(**proj) for proj in ops_by_company[company]],
        ))
    return result


# ---------------------------------------------------------------------------
# AI Insights Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/insights", response_model=list[InsightRecord], tags=["AI Insights"])
def api_get_insights():
    """Return all AI-generated insights."""
    try:
        insights = generate_all_insights()
        return [InsightRecord(**i) for i in insights]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {e}")


@app.get("/api/insights/{insight_type}", response_model=InsightRecord, tags=["AI Insights"])
def api_get_insight(insight_type: str):
    """Return a specific AI insight by type.

    Available types: pipeline_concentration, stale_leads, sla_breach_trend,
    target_gap, revenue_at_risk, overdue_projects, cross_source_match
    """
    if insight_type not in ALL_GENERATORS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown insight type '{insight_type}'. Available: {list(ALL_GENERATORS.keys())}"
        )
    try:
        result = generate_insight(insight_type)
        return InsightRecord(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Data Quality Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/data-quality/summary", response_model=DataQualitySummary, tags=["Data Quality"])
def data_quality_summary():
    """Return missing values count, duplicate count, and unmatched records."""
    conn = _get_connection()

    # CRM missing values
    crm_cols = ["company", "contact_name", "email", "source", "status", "stage", "owner", "region", "deal_value", "created_date"]
    crm_missing = {}
    for col in crm_cols:
        cnt = conn.execute(f"SELECT COUNT(*) AS cnt FROM crm_leads WHERE {col} IS NULL OR {col} = ''").fetchone()["cnt"]
        if cnt > 0:
            crm_missing[col] = cnt

    # Ops missing values
    ops_cols = ["client_company", "service_type", "assigned_team", "status", "start_date", "deadline", "budget", "sla_status"]
    ops_missing = {}
    for col in ops_cols:
        cnt = conn.execute(f"SELECT COUNT(*) AS cnt FROM operations_projects WHERE {col} IS NULL OR {col} = ''").fetchone()["cnt"]
        if cnt > 0:
            ops_missing[col] = cnt

    # Targets missing values
    tgt_cols = ["owner", "region", "target_revenue", "actual_revenue", "month", "year"]
    tgt_missing = {}
    for col in tgt_cols:
        cnt = conn.execute(f"SELECT COUNT(*) AS cnt FROM targets_forecasts WHERE {col} IS NULL OR {col} = ''").fetchone()["cnt"]
        if cnt > 0:
            tgt_missing[col] = cnt

    # Duplicates
    crm_dups = conn.execute("SELECT COUNT(*) AS cnt FROM crm_leads WHERE is_duplicate = 1").fetchone()["cnt"]
    ops_dups = conn.execute("SELECT COUNT(*) AS cnt FROM operations_projects WHERE is_duplicate = 1").fetchone()["cnt"]
    tgt_dups = conn.execute("SELECT COUNT(*) AS cnt FROM targets_forecasts WHERE is_duplicate = 1").fetchone()["cnt"]

    # Unmatched companies
    crm_companies = {r[0].lower() for r in conn.execute(
        "SELECT DISTINCT company FROM crm_leads WHERE company IS NOT NULL"
    ).fetchall()}
    ops_companies = {r[0].lower() for r in conn.execute(
        "SELECT DISTINCT client_company FROM operations_projects WHERE client_company IS NOT NULL"
    ).fetchall()}
    conn.close()

    return DataQualitySummary(
        crm_missing=crm_missing,
        ops_missing=ops_missing,
        targets_missing=tgt_missing,
        crm_duplicates=crm_dups,
        ops_duplicates=ops_dups,
        targets_duplicates=tgt_dups,
        unmatched_crm_companies=len(crm_companies - ops_companies),
        unmatched_ops_companies=len(ops_companies - crm_companies),
    )


@app.get("/api/data-quality/unmatched", response_model=list[UnmatchedRecord], tags=["Data Quality"])
def data_quality_unmatched():
    """Return records that couldn't be matched across data sources."""
    conn = _get_connection()
    crm_companies = {r[0].lower(): r[0] for r in conn.execute(
        "SELECT DISTINCT company FROM crm_leads WHERE company IS NOT NULL"
    ).fetchall()}
    ops_companies = {r[0].lower(): r[0] for r in conn.execute(
        "SELECT DISTINCT client_company FROM operations_projects WHERE client_company IS NOT NULL"
    ).fetchall()}
    conn.close()

    results: list[UnmatchedRecord] = []
    for key in sorted(set(crm_companies.keys()) - set(ops_companies.keys())):
        results.append(UnmatchedRecord(source="crm_leads", company=crm_companies[key]))
    for key in sorted(set(ops_companies.keys()) - set(crm_companies.keys())):
        results.append(UnmatchedRecord(source="operations_projects", company=ops_companies[key]))

    return results


# ---------------------------------------------------------------------------
# Filter Options Endpoint
# ---------------------------------------------------------------------------

@app.get("/api/filters/options", response_model=FilterOptions, tags=["Filters"])
def filter_options():
    """Return all unique values for each filter field."""
    conn = _get_connection()

    def _distinct(table: str, col: str) -> list[str]:
        rows = conn.execute(
            f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL AND {col} != '' ORDER BY {col}"
        ).fetchall()
        return [r[0] for r in rows]

    opts = FilterOptions(
        owners=sorted(set(_distinct("crm_leads", "owner") + _distinct("targets_forecasts", "owner"))),
        sources=_distinct("crm_leads", "source"),
        regions=sorted(set(
            _distinct("crm_leads", "region") +
            _distinct("operations_projects", "region") +
            _distinct("targets_forecasts", "region")
        )),
        statuses=sorted(set(
            _distinct("crm_leads", "status") +
            _distinct("operations_projects", "status")
        )),
        stages=_distinct("crm_leads", "stage"),
        clients=_distinct("operations_projects", "client_company"),
        service_types=_distinct("operations_projects", "service_type"),
        teams=_distinct("operations_projects", "assigned_team"),
        priorities=_distinct("operations_projects", "priority"),
    )
    conn.close()
    return opts


# ---------------------------------------------------------------------------
# Serve Production Frontend SPA
# ---------------------------------------------------------------------------
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="spa-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

