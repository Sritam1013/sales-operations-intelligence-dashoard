# Cloud Deployment & Hosting Guide

This guide explains how to get a **public HTTPS website URL** to share with your manager and evaluators, satisfying Section 13 of the PRD (*"Publicly hosted working prototype URL accessible to the evaluator"*).

---

## 🌟 Architecture Note: Unified Single-Server Mode
The application is already configured to serve **both** the React Frontend and the FastAPI Backend from the same server:
- Frontend static assets are built into `frontend/dist`
- FastAPI serves the frontend at `/` and the REST API at `/api`
- **Result:** You only need to deploy **one single service** on any free hosting platform!

---

## 🚀 Option 1: Render.com (Recommended — 100% Free)

Render provides free hosting for Python/Node web services and gives you a free `https://<your-app>.onrender.com` URL.

### Step-by-Step:
1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "feat: complete sales and operations intelligence dashboard"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

2. **Create Web Service on Render:**
   - Go to [dashboard.render.com](https://dashboard.render.com/) and sign in (with GitHub).
   - Click **New +** > **Web Service**.
   - Select your GitHub repository.

3. **Configure the Service:**
   - **Name:** `sales-ops-dashboard` (or any name you like)
   - **Environment:** `Python 3`
   - **Region:** Any (e.g. Frankfurt or Oregon)
   - **Branch:** `main`
   - **Build Command:**
     ```bash
     cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     cd backend && python run.py
     ```
   - **Instance Type:** Free

4. **Click "Create Web Service"**:
   - Render will build the React app and start FastAPI.
   - Within 2-3 minutes, your live URL will be ready:  
     `https://sales-ops-dashboard.onrender.com`

---

## ⚡ Option 2: Instant Public Link in 30 Seconds (No Cloud Setup)

If you have a meeting with your manager right now and need an instant public HTTPS link from your machine:

Open a new terminal and run:
```bash
npx localtunnel --port 8000
```
> This will instantly output a public URL like:
> `your url is: https://brave-frog-42.loca.lt`

Anyone with this link (including your manager on their laptop or phone) can open it and see the full dashboard while your local server is running!

---

## 🚂 Option 3: Railway.app

1. Go to [railway.app](https://railway.app) and click **Start a New Project**.
2. Select **Deploy from GitHub repo**.
3. Railway detects the project. In Settings, set:
   - **Build Command:** `cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt`
   - **Start Command:** `cd backend && python run.py`
4. Click **Generate Domain** under Networking to get your public `https://....up.railway.app` URL.

---

## 🖥️ Presentation Checklist for Your Manager Meeting

When demonstrating the project to your manager, use this walkthrough flow:

1. **Executive Overview (30s):**
   - Explain that data is consolidated from 3 isolated business silos: CRM (Sales), Operational delivery (Projects), and Google Sheets (Targets).
2. **Sales Dashboard (`/sales`):**
   - Show the 4 KPIs (Leads, Conversion Rate 8.6%, Pipeline Value \$118.6M).
   - Demonstrate the monthly lead creation velocity and pipeline stage funnel.
   - Open the **Stale Leads** table showing deals inactive for >90 days that need follow-up.
3. **Operations Dashboard (`/operations`):**
   - Highlight delivery metrics: 40 Overdue projects (13.3%) and 37% SLA compliance.
   - Show Team workload distribution and Targets vs. Actuals revenue pacing.
4. **Combined Sales-to-Ops View (`/combined`):**
   - Point out the 30 mutual client companies matched across sales and delivery.
   - Explain how this reveals complete account valuation and prevents handoff blindspots.
5. **Data Quality & Reconciliation (`/data-quality`):**
   - Show transparency: missing values tracked, duplicate contacts flagged, and unlinked accounts isolated.
   - Click the **"Refresh Data"** button to show real-time ingestion.
6. **AI-Assisted Insights (`/insights`):**
   - Walk through the 7 actionable alerts (Revenue at Risk, Capacity Bottlenecks, Target Gaps).
   - Expand the "View linked data" evidence to prove every insight is strictly grounded in data without hallucination.
7. **Production Roadmap (`PRODUCTION_ROADMAP.md`):**
   - Show your manager the phased architecture plan for GoHighLevel API integration, RBAC, and SOC 2 compliance.
