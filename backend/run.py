"""
Runner script for the Sales & Operations Intelligence Dashboard backend.

Initializes the database, loads data from source files, and starts the
FastAPI server on port 8000.
"""

import uvicorn
from database import init_db, load_all_data
from main import app

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Loading data from files...")
    results = load_all_data()
    for r in results:
        print(f"  {r['source']}: {r['status']} — {r['records']} records, {r['duplicates']} duplicates")
    print("Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
