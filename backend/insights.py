"""
Rule-based AI Insight Engine for the Sales & Operations Intelligence Dashboard.

Generates actionable insights by analysing CRM leads, operations projects,
and targets/forecasts data stored in SQLite.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Any

from database import _get_connection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert sqlite3.Row objects to plain dicts."""
    return [dict(r) for r in rows]


def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Insight generators
# ---------------------------------------------------------------------------

def pipeline_concentration() -> dict[str, Any]:
    """
    Alert if >40% of pipeline value is concentrated in a single stage
    or a single owner.
    """
    conn = _get_connection()
    total_pipeline = conn.execute(
        "SELECT COALESCE(SUM(deal_value), 0) AS total FROM crm_leads WHERE deal_value IS NOT NULL"
    ).fetchone()["total"]

    if total_pipeline == 0:
        conn.close()
        return _insight(
            "pipeline_concentration", "Pipeline Concentration",
            "No pipeline data available.", "info", 0, [],
            "Load CRM data to see pipeline concentration insights."
        )

    # By stage
    stage_rows = conn.execute(
        "SELECT stage, SUM(deal_value) AS val FROM crm_leads "
        "WHERE deal_value IS NOT NULL AND stage IS NOT NULL "
        "GROUP BY stage ORDER BY val DESC"
    ).fetchall()

    # By owner
    owner_rows = conn.execute(
        "SELECT owner, SUM(deal_value) AS val FROM crm_leads "
        "WHERE deal_value IS NOT NULL AND owner IS NOT NULL "
        "GROUP BY owner ORDER BY val DESC"
    ).fetchall()
    conn.close()

    alerts: list[str] = []
    linked: list[dict] = []
    severity = "info"
    max_pct = 0.0

    for row in stage_rows:
        pct = (row["val"] / total_pipeline) * 100 if total_pipeline else 0
        if pct > 40:
            alerts.append(f"Stage '{row['stage']}' holds {pct:.1f}% of pipeline value (${row['val']:,.0f})")
            linked.append({"type": "stage", "stage": row["stage"], "value": row["val"], "pct": round(pct, 1)})
            max_pct = max(max_pct, pct)

    for row in owner_rows:
        pct = (row["val"] / total_pipeline) * 100 if total_pipeline else 0
        if pct > 40:
            alerts.append(f"Owner '{row['owner']}' holds {pct:.1f}% of pipeline value (${row['val']:,.0f})")
            linked.append({"type": "owner", "owner": row["owner"], "value": row["val"], "pct": round(pct, 1)})
            max_pct = max(max_pct, pct)

    if max_pct > 60:
        severity = "critical"
    elif max_pct > 40:
        severity = "warning"

    desc = " | ".join(alerts) if alerts else "Pipeline value is well distributed across stages and owners."
    rec = "Diversify pipeline by developing leads across more stages and distributing ownership." if alerts else "No action needed."

    return _insight("pipeline_concentration", "Pipeline Concentration", desc, severity, f"{max_pct:.1f}%", linked[:10], rec)


def stale_leads() -> dict[str, Any]:
    """Identify leads with last_activity >90 days ago that are still Active."""
    conn = _get_connection()
    max_act = conn.execute("SELECT MAX(last_activity) FROM crm_leads").fetchone()[0]
    ref_dt = datetime.strptime(max_act, "%Y-%m-%d") if max_act else datetime.utcnow()
    cutoff = (ref_dt - timedelta(days=90)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT * FROM crm_leads WHERE status = 'Active' AND last_activity IS NOT NULL AND last_activity < ?",
        (cutoff,),
    ).fetchall()
    conn.close()

    count = len(rows)
    severity = "critical" if count > 20 else ("warning" if count > 5 else "info")
    total_value = sum(r["deal_value"] or 0 for r in rows)

    return _insight(
        "stale_leads", "Stale Leads",
        f"{count} active leads have had no activity in the last 90 days, representing ${total_value:,.0f} in potential revenue.",
        severity, count,
        _rows_to_dicts(rows[:10]),
        "Prioritise outreach to stale leads or update their status if no longer viable."
    )


def sla_breach_trend() -> dict[str, Any]:
    """Calculate SLA breach rate trend over months."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT strftime('%Y-%m', start_date) AS month, "
        "COUNT(*) AS total, "
        "SUM(CASE WHEN sla_status IN ('Breached', 'At Risk', 'Missed') THEN 1 ELSE 0 END) AS breached "
        "FROM operations_projects "
        "WHERE start_date IS NOT NULL "
        "GROUP BY month ORDER BY month"
    ).fetchall()
    conn.close()

    if not rows:
        return _insight(
            "sla_breach_trend", "SLA Breach Trend",
            "No operations data available.", "info", 0, [],
            "Load operations data to see SLA trends."
        )

    trend_data = []
    breach_rates = []
    for r in rows:
        rate = (r["breached"] / r["total"] * 100) if r["total"] > 0 else 0
        trend_data.append({"month": r["month"], "total": r["total"], "breached": r["breached"], "breach_rate": round(rate, 1)})
        breach_rates.append(rate)

    # Check if trending upward (compare last 3 months)
    severity = "info"
    if len(breach_rates) >= 3:
        recent = breach_rates[-3:]
        if recent[-1] > recent[0] and recent[-1] > 30:
            severity = "critical"
        elif recent[-1] > recent[0]:
            severity = "warning"

    avg_rate = sum(breach_rates) / len(breach_rates) if breach_rates else 0

    return _insight(
        "sla_breach_trend", "SLA Breach Trend",
        f"Average SLA breach rate is {avg_rate:.1f}% across {len(rows)} months. "
        f"Latest month breach rate: {breach_rates[-1]:.1f}%." if breach_rates else "No data.",
        severity, f"{avg_rate:.1f}%", trend_data[-12:],
        "Investigate root causes of SLA breaches and allocate more resources to at-risk projects."
    )


def target_gap_analysis() -> dict[str, Any]:
    """Compare actual vs target revenue, flag owners/regions below 80% achievement."""
    conn = _get_connection()
    # By owner
    owner_rows = conn.execute(
        "SELECT owner, SUM(target_revenue) AS target, SUM(actual_revenue) AS actual "
        "FROM targets_forecasts WHERE target_revenue IS NOT NULL "
        "GROUP BY owner"
    ).fetchall()
    # By region
    region_rows = conn.execute(
        "SELECT region, SUM(target_revenue) AS target, SUM(actual_revenue) AS actual "
        "FROM targets_forecasts WHERE target_revenue IS NOT NULL "
        "GROUP BY region"
    ).fetchall()
    conn.close()

    underperformers: list[dict] = []
    for r in owner_rows:
        if r["target"] and r["target"] > 0:
            pct = ((r["actual"] or 0) / r["target"]) * 100
            if pct < 80:
                underperformers.append({
                    "type": "owner", "owner": r["owner"],
                    "target": r["target"], "actual": r["actual"] or 0,
                    "achievement_pct": round(pct, 1)
                })

    for r in region_rows:
        if r["target"] and r["target"] > 0:
            pct = ((r["actual"] or 0) / r["target"]) * 100
            if pct < 80:
                underperformers.append({
                    "type": "region", "region": r["region"],
                    "target": r["target"], "actual": r["actual"] or 0,
                    "achievement_pct": round(pct, 1)
                })

    count = len(underperformers)
    severity = "critical" if count > 5 else ("warning" if count > 0 else "info")

    return _insight(
        "target_gap", "Target Gap Analysis",
        f"{count} owners/regions are below 80% revenue target achievement.",
        severity, count, underperformers[:10],
        "Review sales strategies for underperforming owners/regions and adjust targets or provide additional support."
    )


def revenue_at_risk() -> dict[str, Any]:
    """Calculate total deal value in Negotiation stage with no recent activity."""
    conn = _get_connection()
    max_act = conn.execute("SELECT MAX(last_activity) FROM crm_leads").fetchone()[0]
    ref_dt = datetime.strptime(max_act, "%Y-%m-%d") if max_act else datetime.utcnow()
    cutoff = (ref_dt - timedelta(days=30)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT * FROM crm_leads WHERE stage = 'Negotiation' "
        "AND (last_activity IS NULL OR last_activity < ?)",
        (cutoff,),
    ).fetchall()
    conn.close()

    total_at_risk = sum(r["deal_value"] or 0 for r in rows)
    count = len(rows)
    severity = "critical" if total_at_risk > 500000 else ("warning" if total_at_risk > 100000 else "info")

    return _insight(
        "revenue_at_risk", "Revenue at Risk",
        f"${total_at_risk:,.0f} in deal value across {count} leads in Negotiation stage with no recent activity (>30 days).",
        severity, f"${total_at_risk:,.0f}", _rows_to_dicts(rows[:10]),
        "Immediately engage leads in negotiation stage that have gone quiet to prevent deal loss."
    )


def overdue_projects() -> dict[str, Any]:
    """Highlight teams/service types with highest overdue rates."""
    conn = _get_connection()
    # By team
    team_rows = conn.execute(
        "SELECT assigned_team, "
        "COUNT(*) AS total, "
        "SUM(CASE WHEN status = 'Overdue' THEN 1 ELSE 0 END) AS overdue "
        "FROM operations_projects "
        "WHERE assigned_team IS NOT NULL "
        "GROUP BY assigned_team",
    ).fetchall()

    # By service type
    service_rows = conn.execute(
        "SELECT service_type, "
        "COUNT(*) AS total, "
        "SUM(CASE WHEN status = 'Overdue' THEN 1 ELSE 0 END) AS overdue "
        "FROM operations_projects "
        "WHERE service_type IS NOT NULL "
        "GROUP BY service_type",
    ).fetchall()
    conn.close()

    results: list[dict] = []
    max_rate = 0.0
    for r in team_rows:
        rate = (r["overdue"] / r["total"] * 100) if r["total"] > 0 else 0
        if r["overdue"] > 0:
            results.append({"type": "team", "team": r["assigned_team"], "total": r["total"], "overdue": r["overdue"], "overdue_rate": round(rate, 1)})
            max_rate = max(max_rate, rate)

    for r in service_rows:
        rate = (r["overdue"] / r["total"] * 100) if r["total"] > 0 else 0
        if r["overdue"] > 0:
            results.append({"type": "service_type", "service_type": r["service_type"], "total": r["total"], "overdue": r["overdue"], "overdue_rate": round(rate, 1)})
            max_rate = max(max_rate, rate)

    severity = "critical" if max_rate > 50 else ("warning" if max_rate > 25 else "info")

    return _insight(
        "overdue_projects", "Overdue Projects",
        f"{len(results)} teams/service types have overdue projects. Highest overdue rate: {max_rate:.1f}%.",
        severity, f"{max_rate:.1f}%", results[:10],
        "Reassign resources or adjust timelines for teams with high overdue rates."
    )


def cross_source_match() -> dict[str, Any]:
    """Report how many CRM companies have matching operations projects."""
    conn = _get_connection()
    crm_companies = conn.execute(
        "SELECT DISTINCT company FROM crm_leads WHERE company IS NOT NULL"
    ).fetchall()
    ops_companies = conn.execute(
        "SELECT DISTINCT client_company FROM operations_projects WHERE client_company IS NOT NULL"
    ).fetchall()
    conn.close()

    crm_set = {r["company"].lower() for r in crm_companies}
    ops_set = {r["client_company"].lower() for r in ops_companies}

    matched = crm_set & ops_set
    crm_only = crm_set - ops_set
    ops_only = ops_set - crm_set

    return _insight(
        "cross_source_match", "Cross-Source Match",
        f"{len(matched)} companies appear in both CRM and Operations data. "
        f"{len(crm_only)} CRM-only, {len(ops_only)} Operations-only.",
        "info", len(matched),
        [
            {"matched": sorted(list(matched))[:20]},
            {"crm_only_sample": sorted(list(crm_only))[:10]},
            {"ops_only_sample": sorted(list(ops_only))[:10]},
        ],
        "Investigate CRM-only companies for upsell into operations, and operations-only companies for CRM onboarding."
    )


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

ALL_GENERATORS = {
    "pipeline_concentration": pipeline_concentration,
    "stale_leads": stale_leads,
    "sla_breach_trend": sla_breach_trend,
    "target_gap": target_gap_analysis,
    "revenue_at_risk": revenue_at_risk,
    "overdue_projects": overdue_projects,
    "cross_source_match": cross_source_match,
}


def generate_all_insights() -> list[dict[str, Any]]:
    """Run all insight generators and return a list of insight dicts."""
    results = []
    for name, fn in ALL_GENERATORS.items():
        try:
            results.append(fn())
        except Exception as e:
            results.append(_insight(
                name, f"Error generating {name}",
                str(e), "info", 0, [],
                "Check data quality and reload."
            ))
    return results


def generate_insight(insight_type: str) -> dict[str, Any] | None:
    """Run a single insight generator by name."""
    fn = ALL_GENERATORS.get(insight_type)
    if fn is None:
        return None
    return fn()


# ---------------------------------------------------------------------------
# Helper to build insight dict
# ---------------------------------------------------------------------------

def _insight(
    insight_type: str,
    title: str,
    description: str,
    severity: str,
    metric_value: Any,
    linked_data: list,
    recommendation: str,
) -> dict[str, Any]:
    return {
        "insight_type": insight_type,
        "title": title,
        "description": description,
        "severity": severity,
        "metric_value": metric_value,
        "linked_data": linked_data,
        "recommendation": recommendation,
    }
