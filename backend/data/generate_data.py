"""
Synthetic Data Generator for Sales & Operations Intelligence Dashboard.
Generates: crm_leads.csv, operations_projects.json, targets_forecasts.csv
"""

import csv
import json
import random
import math
from datetime import date, timedelta

random.seed(42)

# ─── Shared Constants ────────────────────────────────────────────────────────

SALES_REPS = ["Sarah Johnson", "Mike Chen", "Priya Patel", "James Wilson", "Emma Davis"]
REGIONS = ["North America", "Europe", "Asia Pacific", "Middle East", "Latin America"]
LEAD_SOURCES = ["Website", "Referral", "LinkedIn", "Cold Call", "Trade Show", "Email Campaign", "Partner"]
PIPELINE_STAGES = ["New Lead", "Contacted", "Qualified", "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost"]
# Realistic funnel weights (more early, fewer closed)
PIPELINE_WEIGHTS = [0.20, 0.18, 0.18, 0.15, 0.12, 0.10, 0.07]

SERVICE_TYPES = ["Implementation", "Consulting", "Support", "Training", "Migration", "Integration", "Custom Development"]
PROJECT_STATUSES = ["Open", "In Progress", "Completed", "Overdue", "On Hold", "Cancelled"]
TEAMS = ["Team Alpha", "Team Beta", "Team Gamma", "Team Delta", "Team Omega"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
PRIORITY_WEIGHTS = [0.15, 0.40, 0.30, 0.15]

ACCOUNT_SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Strategic"]
CAMPAIGNS = ["Spring Campaign", "Summer Push", "Q4 Blitz", "Year-Round", "Partner Drive"]
MANUAL_CATEGORIES = ["On Track", "At Risk", "Below Target", "Exceeded", "Pending Review"]
REFERENCE_VALUES = [
    "Q1 adjusted", "Board approved", "Carry-over from previous", "Revised mid-quarter",
    "Initial target", "Stretch goal", "Conservative estimate", "Pipeline-based",
    "Historical trend", "Manager override", "Marketing aligned",
]

# ─── Realistic Name / Company Pools ─────────────────────────────────────────

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa",
    "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
    "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Raymond", "Christine", "Gregory", "Debra",
    "Frank", "Rachel", "Alexander", "Carolyn", "Patrick", "Janet", "Jack", "Catherine",
    "Dennis", "Maria", "Jerry", "Heather", "Tyler", "Diane", "Aaron", "Ruth",
    "Jose", "Julie", "Adam", "Olivia", "Nathan", "Joyce", "Henry", "Virginia",
    "Aisha", "Raj", "Wei", "Yuki", "Carlos", "Fatima", "Omar", "Priya",
    "Ivan", "Suki", "Miguel", "Anya", "Leo", "Rosa", "Ali", "Nina",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
    "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales",
    "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson",
    "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward",
    "Richardson", "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray",
    "Mendoza", "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel",
    "Myers", "Long", "Ross", "Foster", "Sharma", "Nakamura", "Chen", "Singh",
    "Yamamoto", "Petrov", "Johansson", "Mueller", "Tanaka", "Weber", "Ali", "Khan",
]

# ~50 unique companies for CRM + extras for ops
SHARED_COMPANIES = [
    "Apex Dynamics", "BrightWave Solutions", "CloudNova Inc", "DataStream Analytics",
    "Evergreen Partners", "Falcon Industries", "GlobalTech Systems", "Horizon Digital",
    "InnoVate Corp", "JetStream Networks", "KeyStone Consulting", "Luminar Technologies",
    "MeridianX Group", "NexGen Software", "Orbit Solutions", "Pinnacle Health",
    "Quantum Leap AI", "RedRock Ventures", "SilverLine Media", "TerraFirma Logistics",
    "UltraVision Labs", "Vertex Capital", "WavePoint Energy", "Xenon Robotics",
    "Yellowstone Data", "ZenithWorks", "Atlas Financial", "BlueShift Dynamics",
    "CrestView Enterprises", "DuoTech Solutions",
]

CRM_ONLY_COMPANIES = [
    "EliteForce Security", "FusionGrid Power", "GreenLeaf Biotech", "HyperLoop Transit",
    "IronClad Defense", "Jupiter Analytics", "KaleidoScope Media", "LightSpeed Comm",
    "MapleStar Retail", "NorthStar Logistics", "OceanView Properties", "PulseRate Health",
    "QuickSilver Trading", "RiverBend Manufacturing", "SkyBridge Telecom",
    "TrueNorth Advisors", "UniCore Pharma", "VistaPeak Mining", "WindRose Energy",
    "Zephyr Aerospace",
]

OPS_ONLY_COMPANIES = [
    "ArcLight Engineering", "BoldEdge Creative", "CipherLock Security",
    "DawnBreak Studios", "EcoVault Systems", "FireStone Analytics",
    "GridIron Networks", "HarborPoint Shipping", "InfoBridge Consulting",
    "JadeTree Wellness", "KineticFlow Labs", "LandMark Realty",
    "MicroPulse Electronics", "NetScope Digital", "OpenField Agriculture",
    "PrimeAxis Robotics", "QuestBridge Education", "RapidCore Software",
    "SummitView Capital", "TideWater Marine",
]

ALL_CRM_COMPANIES = SHARED_COMPANIES + CRM_ONLY_COMPANIES  # 50 companies
ALL_OPS_COMPANIES = SHARED_COMPANIES + OPS_ONLY_COMPANIES   # 50 companies

EMAIL_DOMAINS = [
    "gmail.com", "outlook.com", "yahoo.com", "protonmail.com",
    "company.com", "work.io", "corp.net", "enterprise.org", "biz.co",
]

DATE_START = date(2024, 1, 1)
DATE_END = date(2025, 9, 30)
TODAY = date(2025, 9, 30)  # Reference date for staleness calculations
TOTAL_DAYS = (DATE_END - DATE_START).days


def random_date(start=DATE_START, end=DATE_END):
    return start + timedelta(days=random.randint(0, (end - start).days))


def make_email(first, last):
    styles = [
        f"{first.lower()}.{last.lower()}",
        f"{first[0].lower()}{last.lower()}",
        f"{first.lower()}{last[0].lower()}",
        f"{first.lower()}_{last.lower()}",
        f"{first.lower()}{random.randint(1, 99)}",
    ]
    local = random.choice(styles)
    domain = random.choice(EMAIL_DOMAINS)
    return f"{local}@{domain}"


# ─── 1. CRM Data ────────────────────────────────────────────────────────────

def generate_crm_data(n=500):
    records = []
    used_names = []

    # Pre-generate names, allowing ~3% duplicates
    for i in range(n):
        if i > 20 and random.random() < 0.03 and used_names:
            # Duplicate name from earlier
            name = random.choice(used_names[:i])
        else:
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        used_names.append(name)

    for i in range(n):
        lead_id = f"LEAD-{i+1:04d}"
        contact_name = used_names[i]
        first, last = contact_name.split(" ", 1)
        email = make_email(first, last)

        # ~5% missing company
        if random.random() < 0.05:
            company = ""
        else:
            company = random.choice(ALL_CRM_COMPANIES)

        source = random.choice(LEAD_SOURCES)
        owner = random.choice(SALES_REPS)
        stage = random.choices(PIPELINE_STAGES, weights=PIPELINE_WEIGHTS, k=1)[0]

        # Deal value: ~8% missing, rest in 5000-500000
        if random.random() < 0.08:
            deal_value = ""
        else:
            deal_value = round(random.uniform(5000, 500000), 2)

        created = random_date()

        # last_activity >= created_date
        days_since = (TODAY - created).days
        if stage in ("Closed Won", "Closed Lost"):
            # Closed deals: activity within a reasonable window after creation
            activity_offset = random.randint(7, min(180, days_since)) if days_since > 7 else days_since
            last_activity = created + timedelta(days=activity_offset)
        elif random.random() < 0.12:
            # ~12% stale: last_activity > 90 days ago
            stale_max = max(0, days_since - 90)
            if stale_max > 0:
                activity_offset = random.randint(0, min(stale_max, days_since))
                last_activity = created + timedelta(days=activity_offset)
                # Ensure staleness
                if (TODAY - last_activity).days < 91:
                    last_activity = TODAY - timedelta(days=random.randint(91, 200))
                    if last_activity < created:
                        last_activity = created
            else:
                last_activity = created
        else:
            activity_offset = random.randint(0, days_since)
            last_activity = created + timedelta(days=activity_offset)

        # Status correlated with pipeline stage
        if stage == "Closed Won":
            status = "Converted"
        elif stage == "Closed Lost":
            status = "Inactive"
        elif stage in ("New Lead", "Contacted"):
            status = random.choices(["Active", "Inactive"], weights=[0.75, 0.25], k=1)[0]
        else:
            status = random.choices(["Active", "Inactive"], weights=[0.85, 0.15], k=1)[0]

        region = random.choice(REGIONS)

        records.append({
            "lead_id": lead_id,
            "contact_name": contact_name,
            "email": email,
            "company": company,
            "source": source,
            "owner": owner,
            "pipeline_stage": stage,
            "deal_value": deal_value,
            "created_date": created.isoformat(),
            "last_activity": last_activity.isoformat(),
            "status": status,
            "region": region,
        })

    return records


def write_crm_csv(records, path="crm_leads.csv"):
    fields = [
        "lead_id", "contact_name", "email", "company", "source", "owner",
        "pipeline_stage", "deal_value", "created_date", "last_activity", "status", "region",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(f"  OK {path}: {len(records)} records")


# ─── 2. Operations Data ─────────────────────────────────────────────────────

def generate_operations_data(n=300):
    records = []
    # Build client pool: ~80 unique clients, ~30 from shared companies
    client_names = list(SHARED_COMPANIES)  # 30 shared
    remaining = ALL_OPS_COMPANIES.copy()
    for c in SHARED_COMPANIES:
        if c in remaining:
            remaining.remove(c)
    # Fill to 80 from ops-only
    extra_needed = 80 - len(client_names)
    client_names += remaining[:extra_needed]
    random.shuffle(client_names)

    client_map = {}
    for idx, name in enumerate(client_names):
        client_map[name] = f"CLT-{idx+1:03d}"

    for i in range(n):
        project_id = f"PRJ-{i+1:04d}"
        client_name = random.choice(client_names)
        client_id = client_map[client_name]
        service_type = random.choice(SERVICE_TYPES)

        created = random_date()
        # Duration: 2 weeks to 6 months
        duration_days = random.randint(14, 180)
        due = created + timedelta(days=duration_days)

        priority = random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS, k=1)[0]
        team = random.choice(TEAMS)

        # Determine status
        is_past_due = due < TODAY
        rand_val = random.random()

        if rand_val < 0.15 and is_past_due:
            # ~15% overdue
            status = "Overdue"
            completed_date = None
        elif rand_val < 0.45 and is_past_due:
            status = "Completed"
            # Completed sometime between created and due (or slightly after)
            comp_offset = random.randint(duration_days - 14, duration_days + 30)
            completed_date = created + timedelta(days=max(1, comp_offset))
        elif rand_val < 0.55:
            status = "In Progress"
            completed_date = None
        elif rand_val < 0.65:
            status = "Open"
            completed_date = None
        elif rand_val < 0.72:
            status = "On Hold"
            completed_date = None
        elif rand_val < 0.78 and is_past_due:
            status = "Cancelled"
            cancel_offset = random.randint(7, max(8, duration_days))
            completed_date = created + timedelta(days=cancel_offset)
        else:
            status = "In Progress"
            completed_date = None

        # Force enough overdue: if we haven't hit 15% by end, adjust
        # (handled by the probability above, close enough)

        # SLA status — correlated with due_date and status
        if status == "Overdue":
            sla = random.choices(["Breached", "At Risk"], weights=[0.8, 0.2], k=1)[0]
        elif status == "Completed":
            sla = random.choices(["Within SLA", "Breached"], weights=[0.85, 0.15], k=1)[0]
        elif is_past_due and status not in ("Completed", "Cancelled"):
            sla = "Breached"
        else:
            days_to_due = (due - TODAY).days
            if days_to_due < 7 and status == "In Progress":
                sla = random.choices(["At Risk", "Within SLA"], weights=[0.7, 0.3], k=1)[0]
            else:
                sla = random.choices(["Within SLA", "At Risk"], weights=[0.85, 0.15], k=1)[0]

        amount = round(random.uniform(10000, 300000), 2)

        records.append({
            "project_id": project_id,
            "client_id": client_id,
            "client_name": client_name,
            "service_type": service_type,
            "status": status,
            "created_date": created.isoformat(),
            "due_date": due.isoformat(),
            "completed_date": completed_date.isoformat() if completed_date else None,
            "amount": amount,
            "assigned_team": team,
            "sla_status": sla,
            "priority": priority,
        })

    return records


def write_operations_json(records, path="operations_projects.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"  OK {path}: {len(records)} records")


# ─── 3. Targets & Forecasts ─────────────────────────────────────────────────

def generate_targets_data():
    records = []
    # Monthly periods from 2024-01 to 2025-09
    periods = []
    for year in (2024, 2025):
        end_month = 12 if year == 2024 else 9
        for month in range(1, end_month + 1):
            periods.append(f"{year}-{month:02d}")

    # Generate entries: each owner × region for a subset of months
    # ~120 records total → we pick combos strategically
    combos = []
    for owner in SALES_REPS:
        # Each rep covers 2-3 regions
        rep_regions = random.sample(REGIONS, k=random.randint(2, 3))
        for region in rep_regions:
            combos.append((owner, region))

    # Distribute periods across combos to hit ~120 records
    target_count = 120
    entries_per_combo = max(3, target_count // len(combos))

    for owner, region in combos:
        # Pick a segment for this owner-region combo
        segment = random.choice(ACCOUNT_SEGMENTS)
        # Select a subset of months
        selected_periods = sorted(random.sample(periods, k=min(entries_per_combo, len(periods))))

        base_target = random.uniform(50000, 500000)

        for period in selected_periods:
            year, month = map(int, period.split("-"))
            period_date = date(year, month, 1)

            # Seasonal variation
            seasonal = 1.0 + 0.1 * math.sin(2 * math.pi * month / 12)
            target_revenue = round(base_target * seasonal * random.uniform(0.9, 1.1), 2)

            # Forecast: close to target with some variance
            forecast_revenue = round(target_revenue * random.uniform(0.85, 1.15), 2)

            # Actual: null for future months (after 2025-06)
            if period_date > date(2025, 6, 1):
                actual_revenue = ""
                manual = random.choice(["Pending Review", "On Track", "At Risk"])
            else:
                # Actual with meaningful gaps
                performance = random.choice([0.7, 0.85, 0.95, 1.0, 1.05, 1.15, 1.3])
                actual_revenue = round(target_revenue * performance * random.uniform(0.9, 1.1), 2)

                ratio = actual_revenue / target_revenue if target_revenue > 0 else 1
                if ratio >= 1.1:
                    manual = "Exceeded"
                elif ratio >= 0.95:
                    manual = "On Track"
                elif ratio >= 0.8:
                    manual = "At Risk"
                else:
                    manual = "Below Target"

            # Campaign mapping: ~20% null
            if random.random() < 0.20:
                campaign = ""
            else:
                campaign = random.choice(CAMPAIGNS)

            ref = random.choice(REFERENCE_VALUES)

            records.append({
                "period": period,
                "owner": owner,
                "region": region,
                "account_segment": segment,
                "target_revenue": target_revenue,
                "forecast_revenue": forecast_revenue,
                "actual_revenue": actual_revenue,
                "manual_category": manual,
                "reference_values": ref,
                "campaign_mapping": campaign,
            })

        if len(records) >= target_count:
            break

    # Trim to ~120 if over
    if len(records) > 130:
        records = records[:125]

    return records


def write_targets_csv(records, path="targets_forecasts.csv"):
    fields = [
        "period", "owner", "region", "account_segment", "target_revenue",
        "forecast_revenue", "actual_revenue", "manual_category",
        "reference_values", "campaign_mapping",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(f"  OK {path}: {len(records)} records")


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os

    data_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(data_dir)

    print("Generating synthetic datasets...\n")

    # 1. CRM
    crm = generate_crm_data(500)
    write_crm_csv(crm)

    # 2. Operations
    ops = generate_operations_data(300)
    write_operations_json(ops)

    # 3. Targets
    targets = generate_targets_data()
    write_targets_csv(targets)

    # ── Verification ──
    print("\n-- Verification --")

    # CRM checks
    missing_company = sum(1 for r in crm if not r["company"])
    missing_deal = sum(1 for r in crm if r["deal_value"] == "")
    names = [r["contact_name"] for r in crm]
    dup_names = len(names) - len(set(names))
    stale = sum(
        1 for r in crm
        if r["status"] == "Active"
        and (TODAY - date.fromisoformat(r["last_activity"])).days > 90
    )
    print(f"  CRM: {len(crm)} records")
    print(f"    Missing company:  {missing_company} ({missing_company/len(crm)*100:.1f}%)")
    print(f"    Missing deal_val: {missing_deal} ({missing_deal/len(crm)*100:.1f}%)")
    print(f"    Duplicate names:  {dup_names}")
    print(f"    Stale leads:      {stale}")

    # Ops checks
    overdue = sum(1 for r in ops if r["status"] == "Overdue")
    breached = sum(1 for r in ops if r["sla_status"] == "Breached")
    ops_companies = set(r["client_name"] for r in ops)
    crm_companies = set(r["company"] for r in crm if r["company"])
    overlap = ops_companies & crm_companies
    print(f"  Operations: {len(ops)} records")
    print(f"    Overdue:          {overdue} ({overdue/len(ops)*100:.1f}%)")
    print(f"    SLA Breached:     {breached}")
    print(f"    Company overlap with CRM: {len(overlap)}")

    # Targets checks
    owners_in_targets = set(r["owner"] for r in targets)
    regions_in_targets = set(r["region"] for r in targets)
    future_nulls = sum(1 for r in targets if r["actual_revenue"] == "")
    print(f"  Targets: {len(targets)} records")
    print(f"    Owners match CRM: {owners_in_targets == set(SALES_REPS)}")
    print(f"    Regions match CRM: {regions_in_targets <= set(REGIONS)}")
    print(f"    Future (null actual): {future_nulls}")

    print("\nAll datasets generated successfully!")
