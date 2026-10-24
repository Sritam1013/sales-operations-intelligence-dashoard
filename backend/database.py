"""
Database module for the Sales & Operations Intelligence Dashboard.

Handles SQLite database initialization, schema creation, and data loading
from CSV/JSON source files with normalization and deduplication tracking.
"""

import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "dashboard.db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with WAL mode and row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _normalize_company(name: str | None) -> str | None:
    """Trim whitespace and convert to title case."""
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return None
    return str(name).strip().title()


def _parse_date(val) -> str | None:
    """Try to parse a value as a date string (YYYY-MM-DD). Return None on failure."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(val).strip(), fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    # Last resort – let pandas try
    try:
        return pd.to_datetime(val).strftime("%Y-%m-%d")
    except Exception:
        return None


def _safe_float(val) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS crm_leads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id         TEXT,
    company         TEXT,
    contact_name    TEXT,
    email           TEXT,
    phone           TEXT,
    source          TEXT,
    status          TEXT,
    stage           TEXT,
    owner           TEXT,
    region          TEXT,
    deal_value      REAL,
    probability     REAL,
    created_date    TEXT,
    last_activity   TEXT,
    expected_close  TEXT,
    notes           TEXT,
    is_duplicate    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS operations_projects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          TEXT,
    project_name        TEXT,
    client_company      TEXT,
    service_type        TEXT,
    assigned_team       TEXT,
    project_manager     TEXT,
    status              TEXT,
    priority            TEXT,
    start_date          TEXT,
    end_date            TEXT,
    deadline            TEXT,
    budget              REAL,
    actual_cost         REAL,
    completion_percent  REAL,
    sla_status          TEXT,
    region              TEXT,
    notes               TEXT,
    is_duplicate        INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS targets_forecasts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    month           TEXT,
    year            INTEGER,
    owner           TEXT,
    region          TEXT,
    target_revenue  REAL,
    actual_revenue  REAL,
    target_leads    INTEGER,
    actual_leads    INTEGER,
    target_deals    INTEGER,
    actual_deals    INTEGER,
    notes           TEXT,
    is_duplicate    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS data_load_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    loaded_at   TEXT NOT NULL,
    source_file TEXT,
    records     INTEGER,
    duplicates  INTEGER,
    status      TEXT
);
"""


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

def init_db():
    """Create the database and tables if they don't exist."""
    conn = _get_connection()
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _mark_duplicates(df: pd.DataFrame, subset: list[str]) -> pd.DataFrame:
    """Add an ``is_duplicate`` column; first occurrence is kept, rest flagged."""
    df = df.copy()
    df["is_duplicate"] = df.duplicated(subset=subset, keep="first").astype(int)
    return df


def load_crm_leads() -> dict:
    """Load CRM leads from CSV into SQLite. Returns load summary dict."""
    filepath = os.path.join(DATA_DIR, "crm_leads.csv")
    if not os.path.exists(filepath):
        return {"source": "crm_leads.csv", "status": "file_not_found", "records": 0, "duplicates": 0}

    df = pd.read_csv(filepath)

    # Normalize columns – lowercase, strip
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Map common column name variants
    col_map = {
        "lead_id": "lead_id", "leadid": "lead_id", "id": "lead_id",
        "company": "company", "company_name": "company",
        "contact_name": "contact_name", "contact": "contact_name",
        "email": "email", "phone": "phone",
        "source": "source", "lead_source": "source",
        "status": "status", "lead_status": "status",
        "stage": "stage", "pipeline_stage": "stage",
        "owner": "owner", "lead_owner": "owner", "sales_rep": "owner",
        "region": "region",
        "deal_value": "deal_value", "value": "deal_value", "amount": "deal_value",
        "probability": "probability", "win_probability": "probability",
        "created_date": "created_date", "created_at": "created_date", "date_created": "created_date",
        "last_activity": "last_activity", "last_activity_date": "last_activity",
        "expected_close": "expected_close", "expected_close_date": "expected_close", "close_date": "expected_close",
        "notes": "notes",
    }
    rename = {}
    for orig in df.columns:
        if orig in col_map:
            rename[orig] = col_map[orig]
    df.rename(columns=rename, inplace=True)

    # Ensure expected columns exist
    for col in ["lead_id", "company", "contact_name", "email", "phone", "source",
                 "status", "stage", "owner", "region", "deal_value", "probability",
                 "created_date", "last_activity", "expected_close", "notes"]:
        if col not in df.columns:
            df[col] = None

    # Normalize
    df["company"] = df["company"].apply(_normalize_company)
    df["deal_value"] = df["deal_value"].apply(_safe_float)
    df["probability"] = df["probability"].apply(_safe_float)
    df["created_date"] = df["created_date"].apply(_parse_date)
    df["last_activity"] = df["last_activity"].apply(_parse_date)
    df["expected_close"] = df["expected_close"].apply(_parse_date)

    # Duplicate detection
    df = _mark_duplicates(df, subset=["company", "contact_name", "email"])

    duplicates = int(df["is_duplicate"].sum())

    conn = _get_connection()
    conn.execute("DELETE FROM crm_leads;")
    df[["lead_id", "company", "contact_name", "email", "phone", "source",
        "status", "stage", "owner", "region", "deal_value", "probability",
        "created_date", "last_activity", "expected_close", "notes", "is_duplicate"]].to_sql(
        "crm_leads", conn, if_exists="append", index=False
    )
    conn.commit()
    conn.close()

    return {"source": "crm_leads.csv", "status": "loaded", "records": len(df), "duplicates": duplicates}


def load_operations_projects() -> dict:
    """Load operations projects from JSON into SQLite. Returns load summary dict."""
    filepath = os.path.join(DATA_DIR, "operations_projects.json")
    if not os.path.exists(filepath):
        return {"source": "operations_projects.json", "status": "file_not_found", "records": 0, "duplicates": 0}

    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Handle both list and {"projects": [...]} formats
    if isinstance(raw, dict):
        raw = raw.get("projects", raw.get("data", []))
    df = pd.DataFrame(raw)

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    col_map = {
        "project_id": "project_id", "projectid": "project_id",
        "project_name": "project_name", "name": "project_name",
        "client_company": "client_company", "client": "client_company", "company": "client_company", "client_name": "client_company",
        "service_type": "service_type", "service": "service_type",
        "assigned_team": "assigned_team", "team": "assigned_team",
        "project_manager": "project_manager", "manager": "project_manager", "pm": "project_manager",
        "status": "status",
        "priority": "priority",
        "start_date": "start_date", "created_date": "start_date",
        "end_date": "end_date", "completed_date": "end_date",
        "deadline": "deadline", "due_date": "deadline",
        "budget": "budget", "amount": "budget",
        "actual_cost": "actual_cost", "cost": "actual_cost",
        "completion_percent": "completion_percent", "completion": "completion_percent", "progress": "completion_percent",
        "sla_status": "sla_status", "sla": "sla_status",
        "region": "region",
        "notes": "notes",
    }
    rename = {}
    for orig in df.columns:
        if orig in col_map:
            rename[orig] = col_map[orig]
    df.rename(columns=rename, inplace=True)

    for col in ["project_id", "project_name", "client_company", "service_type",
                 "assigned_team", "project_manager", "status", "priority",
                 "start_date", "end_date", "deadline", "budget", "actual_cost",
                 "completion_percent", "sla_status", "region", "notes"]:
        if col not in df.columns:
            df[col] = None

    df["client_company"] = df["client_company"].apply(_normalize_company)
    df["budget"] = df["budget"].apply(_safe_float)
    df["actual_cost"] = df["actual_cost"].apply(_safe_float)
    df["completion_percent"] = df["completion_percent"].apply(_safe_float)
    df["start_date"] = df["start_date"].apply(_parse_date)
    df["end_date"] = df["end_date"].apply(_parse_date)
    df["deadline"] = df["deadline"].apply(_parse_date)

    df = _mark_duplicates(df, subset=["project_id"])
    duplicates = int(df["is_duplicate"].sum())

    conn = _get_connection()
    conn.execute("DELETE FROM operations_projects;")
    df[["project_id", "project_name", "client_company", "service_type",
        "assigned_team", "project_manager", "status", "priority",
        "start_date", "end_date", "deadline", "budget", "actual_cost",
        "completion_percent", "sla_status", "region", "notes", "is_duplicate"]].to_sql(
        "operations_projects", conn, if_exists="append", index=False
    )
    conn.commit()
    conn.close()

    return {"source": "operations_projects.json", "status": "loaded", "records": len(df), "duplicates": duplicates}


def load_targets_forecasts() -> dict:
    """Load targets/forecasts from CSV into SQLite. Returns load summary dict."""
    filepath = os.path.join(DATA_DIR, "targets_forecasts.csv")
    if not os.path.exists(filepath):
        return {"source": "targets_forecasts.csv", "status": "file_not_found", "records": 0, "duplicates": 0}

    df = pd.read_csv(filepath)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    col_map = {
        "month": "month",
        "year": "year",
        "owner": "owner", "sales_rep": "owner",
        "region": "region",
        "target_revenue": "target_revenue", "revenue_target": "target_revenue",
        "actual_revenue": "actual_revenue", "revenue_actual": "actual_revenue",
        "target_leads": "target_leads", "leads_target": "target_leads",
        "actual_leads": "actual_leads", "leads_actual": "actual_leads",
        "target_deals": "target_deals", "deals_target": "target_deals",
        "actual_deals": "actual_deals", "deals_actual": "actual_deals",
        "notes": "notes",
    }
    rename = {}
    for orig in df.columns:
        if orig in col_map:
            rename[orig] = col_map[orig]
    df.rename(columns=rename, inplace=True)

    # Handle 'period' column (e.g., "2024-01") → split into month and year
    if "period" in df.columns and "month" not in df.columns:
        import calendar
        def _parse_period_month(val):
            try:
                parts = str(val).split("-")
                month_num = int(parts[1])
                return calendar.month_name[month_num]
            except (IndexError, ValueError):
                return None
        def _parse_period_year(val):
            try:
                return int(str(val).split("-")[0])
            except (IndexError, ValueError):
                return None
        df["month"] = df["period"].apply(_parse_period_month)
        df["year"] = df["period"].apply(_parse_period_year)

    for col in ["month", "year", "owner", "region", "target_revenue", "actual_revenue",
                 "target_leads", "actual_leads", "target_deals", "actual_deals", "notes"]:
        if col not in df.columns:
            df[col] = None

    df["target_revenue"] = df["target_revenue"].apply(_safe_float)
    df["actual_revenue"] = df["actual_revenue"].apply(_safe_float)
    df["target_leads"] = df["target_leads"].apply(_safe_int)
    df["actual_leads"] = df["actual_leads"].apply(_safe_int)
    df["target_deals"] = df["target_deals"].apply(_safe_int)
    df["actual_deals"] = df["actual_deals"].apply(_safe_int)
    df["year"] = df["year"].apply(_safe_int)

    df = _mark_duplicates(df, subset=["month", "year", "owner", "region"])
    duplicates = int(df["is_duplicate"].sum())

    conn = _get_connection()
    conn.execute("DELETE FROM targets_forecasts;")
    df[["month", "year", "owner", "region", "target_revenue", "actual_revenue",
        "target_leads", "actual_leads", "target_deals", "actual_deals", "notes", "is_duplicate"]].to_sql(
        "targets_forecasts", conn, if_exists="append", index=False
    )
    conn.commit()
    conn.close()

    return {"source": "targets_forecasts.csv", "status": "loaded", "records": len(df), "duplicates": duplicates}


def load_all_data() -> list[dict]:
    """Load all data sources and log the results. Returns list of summaries."""
    results = [
        load_crm_leads(),
        load_operations_projects(),
        load_targets_forecasts(),
    ]

    conn = _get_connection()
    now = datetime.utcnow().isoformat()
    for r in results:
        conn.execute(
            "INSERT INTO data_load_log (loaded_at, source_file, records, duplicates, status) VALUES (?, ?, ?, ?, ?)",
            (now, r["source"], r["records"], r["duplicates"], r["status"]),
        )
    conn.commit()
    conn.close()

    return results


def get_last_load_info() -> dict:
    """Return the last data load timestamp and per-source summary."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM data_load_log ORDER BY loaded_at DESC LIMIT 3"
    ).fetchall()

    if not rows:
        conn.close()
        return {"last_loaded_at": None, "sources": []}

    # Record counts
    crm_count = conn.execute("SELECT COUNT(*) FROM crm_leads").fetchone()[0]
    ops_count = conn.execute("SELECT COUNT(*) FROM operations_projects").fetchone()[0]
    tgt_count = conn.execute("SELECT COUNT(*) FROM targets_forecasts").fetchone()[0]
    conn.close()

    return {
        "last_loaded_at": rows[0]["loaded_at"],
        "record_counts": {
            "crm_leads": crm_count,
            "operations_projects": ops_count,
            "targets_forecasts": tgt_count,
        },
        "load_details": [dict(r) for r in rows],
    }
