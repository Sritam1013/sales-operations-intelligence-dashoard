import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000/api"

endpoints = [
    "/data/status",
    "/sales/kpis",
    "/sales/leads-over-time",
    "/sales/leads-by-source",
    "/sales/leads-by-stage",
    "/sales/leads-by-owner",
    "/sales/leads-by-region",
    "/sales/stage-conversion",
    "/sales/stale-leads",
    "/operations/kpis",
    "/operations/projects-by-status",
    "/operations/projects-over-time",
    "/operations/workload-by-team",
    "/operations/workload-by-service",
    "/operations/sla-overview",
    "/operations/targets-vs-actuals",
    "/operations/overdue-projects",
    "/combined/sales-to-ops",
    "/insights",
    "/data-quality/summary",
    "/data-quality/unmatched",
    "/filters/options",
]

errors = 0
for ep in endpoints:
    url = f"{BASE_URL}{ep}"
    try:
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode())
        count = len(data) if isinstance(data, list) else (len(data.keys()) if isinstance(data, dict) else 1)
        print(f"OK  [200] {ep:35} (items/keys: {count})")
    except Exception as e:
        print(f"ERR [FAIL] {ep:35} -> {e}")
        errors += 1

print(f"\nTotal endpoints tested: {len(endpoints)}, Errors: {errors}")
sys.exit(errors)
