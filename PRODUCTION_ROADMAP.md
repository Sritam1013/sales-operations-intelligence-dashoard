# Production-Readiness Vision & Engineering Roadmap

**Document Version:** 1.0.0  
**Project:** Sales & Operations Intelligence Dashboard (Braahmam International Limited)  
**Author:** Technical Architecture Submission  

---

## 1. Executive Summary

This prototype successfully proves the analytical, visual, and AI-assisted value of consolidating disparate Sales, Operations, and Planning data. To transition from this 2-day scoped prototype into a mission-critical, enterprise-grade internal platform, this document outlines the end-to-end production architecture, security safeguards, governance frameworks, and execution roadmap.

---

## 2. High-Level Enterprise Architecture

```mermaid
flowchart TD
    subgraph Source_Systems ["Live Source Systems"]
        GHL["GoHighLevel CRM (API v2 / Webhooks)"]
        OPS["Operations ERP / Plunet / Jira"]
        GSheets["Google Sheets / Drive API"]
    end

    subgraph Ingestion_Layer ["Ingestion & Orchestration Layer"]
        Airflow["Apache Airflow / Dagster Orchestrator"]
        WebhookHandler["FastAPI Webhook Receiver"]
        DLQ["Dead-Letter Queue (AWS SQS / Kafka)"]
    end

    subgraph Data_Platform ["Data Warehouse & Transformation"]
        RawLake["S3 / Cloud Storage (Raw Parquet Data Lake)"]
        dbt["dbt Core (Normalization, Dedup, Data Models)"]
        Warehouse["Snowflake / BigQuery / PostgreSQL"]
    end

    subgraph Analytics_AI ["Semantic & AI Governance Layer"]
        Cube["Semantic Layer (Metric Consistency)"]
        LLM["Enterprise LLM Gateway (Gemini API / Claude)"]
        Guardrails["Guardrails / Grounding & Audit Engine"]
    end

    subgraph Presentation ["Presentation & Consumption"]
        AppFastAPI["FastAPI Production API (Caching + Rate Limiting)"]
        ReactApp["React 18 SPA (CDN / Edge Hosted)"]
        SlackBot["Automated Slack/Email Digest Alerts"]
    end

    GHL -->|REST Polling & Webhooks| WebhookHandler
    OPS -->|Nightly ETL Batch| Airflow
    GSheets -->|OAuth Service Account| Airflow

    WebhookHandler --> RawLake
    Airflow --> RawLake
    WebhookHandler -.->|Failed payloads| DLQ

    RawLake --> dbt
    dbt --> Warehouse
    Warehouse --> Cube
    Cube --> AppFastAPI
    Cube --> Guardrails
    Guardrails <--> LLM
    Guardrails --> AppFastAPI

    AppFastAPI --> ReactApp
    AppFastAPI --> SlackBot
```

---

## 3. Detailed Component Architecture & Integration Realities

### 3.1 Source System Integrations
1. **GoHighLevel (GHL) CRM Integration:**
   - **Authentication:** OAuth 2.0 with automated token refresh cycles using secure AWS Secrets Manager / HashiCorp Vault.
   - **Ingestion Strategy:** Hybrid approach:
     - *Real-time Webhooks:* Listen for `OpportunityStageUpdate`, `ContactCreate`, and `TaskCompleted` events.
     - *Scheduled Reconciliation:* Hourly incremental sync via `/opportunities/search` using `updated_at >= :last_sync_timestamp`.
   - **Rate Limit Handling:** GHL enforces rate limits (e.g., 100 requests / 10 seconds). Implement Leaky Bucket rate limiters via Redis with exponential backoff and jitter.

2. **Operations System (Plunet / Jira / Custom):**
   - **Integration:** REST API with pagination cursor support, or direct CDC (Change Data Capture) via Debezium if hosted on a dedicated database.
   - **Incremental Updates:** Track `last_modified` and watermark timestamps to minimize compute overhead.

3. **Google Sheets / Management Context:**
   - **Integration:** Google Workspace Service Account with granular read permissions restricted to designated spreadsheet IDs.
   - **Validation:** Automatic schema validator ensuring named columns exist before ingesting to avoid silent formatting breakage.

---

### 3.2 Canonical Data Model & Identifier Reconciliation
In the prototype, matching relies on normalized company names. In production, we deploy a **Customer Master Data Management (MDM)** pipeline:
- **Canonical Organization Entity:** Assigns an immutable `canonical_account_id` (UUID).
- **Identity Resolution Engine:**
  - Exact match: Domain matching (`@company.com` from contact emails) and tax/business registration IDs.
  - Fuzzy match: Levenshtein distance & Jaro-Winkler string similarity with automated human-in-the-loop validation queue for scores between 0.80 and 0.95.
- **Audit Lineage:** Every row maintains source lineage (`source_system`, `source_id`, `ingested_at`, `dbt_job_id`).

---

### 3.3 Security, Privacy & Compliance (SOC 2 & GDPR)
1. **Role-Based Access Control (RBAC):**
   - **Sales Representatives:** Filtered view showing only their assigned leads, pipeline, and personal quota progress.
   - **Sales Managers / Ops Leads:** Team-level visibility, workload allocation, and SLA breach monitors.
   - **Executive / Admin:** Organization-wide KPIs, cross-system financial reconciliation, and configuration settings.
   - **Authentication:** Corporate SSO (Okta, Microsoft Entra ID, Google Workspace) with multi-factor authentication (MFA).

2. **Data Protection & Encryption:**
   - **At Rest:** AES-256 encryption across all database volumes, S3 buckets, and data warehouse partitions.
   - **In Transit:** TLS 1.3 enforced across all API endpoints and internal microservice communications.
   - **PII Safeguards:** Automated pseudonymization/masking of sensitive customer contact info (phone numbers, personal emails) in analytics environments.

3. **Audit Trails & Retention:**
   - Full immutable audit log tracking every user login, data refresh, filter view, and report export.
   - Automated retention policies enforcing deletion of inactive lead PII after 24 months in compliance with GDPR.

---

### 3.4 AI Governance & Safeguards Against Hallucination
The prototype implements deterministic rule-based algorithms for zero-hallucination accuracy. In production, LLM enhancement follows strict guardrails:
1. **Separation of Fact vs Inference:**
   - Raw aggregations and trend percentages are computed purely in deterministic SQL/Python before being passed to the LLM context.
   - LLMs are strictly prohibited from generating quantitative figures independently.
2. **Grounding & Traceability:**
   - Every generated textual insight must cite exact record identifiers or metric keys in its JSON response schema.
   - Clickable drill-downs allow users to inspect the underlying source records justifying the AI's conclusion.
3. **Guardrails & Evaluation:**
   - Input sanitization to prevent prompt injection.
   - Synthetic or sanitized metadata only: zero customer PII is ever transmitted to external model APIs.
   - Automated evaluation suite checking fact consistency against ground-truth metric values.

---

## 4. Phased Engineering Roadmap

```mermaid
gantt
    title Production Implementation Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1: Core Foundation
    Warehouse Setup & Canonical Schemas   :p1_1, 2026-11-01, 30d
    GHL & Google Sheets Live Connectors   :p1_2, 2026-11-15, 30d
    Automated Ingestion & DLQ             :p1_3, 2026-12-01, 25d
    section Phase 2: Security & MDM
    RBAC & SSO Integration                :p2_1, 2026-12-15, 25d
    MDM Entity Matching Pipeline          :p2_2, 2027-01-05, 30d
    dbt Production Modeling               :p2_3, 2027-01-15, 25d
    section Phase 3: Analytics & AI
    Semantic Metric Layer                 :p3_1, 2027-02-01, 25d
    AI Insight Gateway with Guardrails    :p3_2, 2027-02-15, 30d
    Automated Alerting (Slack/Email)      :p3_3, 2027-03-01, 20d
    section Phase 4: Scale & Launch
    Load Testing & Performance Caching    :p4_1, 2027-03-15, 20d
    Security Audit & SOC 2 Certification  :p4_2, 2027-03-25, 30d
    Full Rollout & User Onboarding        :p4_3, 2027-04-15, 15d
```

| Phase | Duration | Core Deliverables | Indicative Effort | Key Risk & Mitigation |
|---|---|---|---|---|
| **Phase 1: Ingestion & Infrastructure** | 6 Weeks | Production Postgres/Snowflake instance, Airflow DAGs, GHL API & Google Sheets connectors, error handling | 2 Data Engineers, 1 Backend Dev | *API Rate Limits:* Implement Redis token-bucket throttling & webhook fallback. |
| **Phase 2: Security & Entity Matching** | 6 Weeks | RBAC with Okta SSO, dbt transformations, domain-based company entity matching, audit logging | 1 Security Eng, 1 Data Eng | *Unmatched Entities:* Build human review queue in internal dashboard. |
| **Phase 3: AI & Advanced Analytics** | 6 Weeks | Semantic layer, LLM insight generator with strict ground-truth linking, Slack/Email alert dispatchers | 1 AI/ML Eng, 1 Full-Stack Dev | *AI Hallucinations:* Restrict LLM to text summarization of deterministic metrics. |
| **Phase 4: Hardening & Go-Live** | 4 Weeks | Redis caching, end-to-end integration testing, SOC 2 compliance check, user documentation | 1 QA Eng, 1 DevOps, 1 PM | *Data Drift:* Automated schema drift alerts and daily reconciliation tests. |

---

## 5. Ongoing Maintenance & Estimated TCO

| Cost Category | Recommended Service | Monthly Estimate (USD) |
|---|---|---|
| Cloud Compute & Hosting | AWS ECS / Render (FastAPI + React) | \$120 – \$250 |
| Data Warehouse | Snowflake (X-Small) / Managed PostgreSQL | \$200 – \$450 |
| Ingestion & Orchestration | Astronomer Airflow or AWS MWAA | \$150 – \$300 |
| Redis Cache & Secrets | AWS ElastiCache + Secrets Manager | \$80 – \$150 |
| AI API Tokens (Sanitized) | Gemini 1.5 Flash / Claude 3.5 Sonnet | \$30 – \$80 |
| **Total Estimated Operating Cost** | | **\$580 – \$1,230 / month** |
