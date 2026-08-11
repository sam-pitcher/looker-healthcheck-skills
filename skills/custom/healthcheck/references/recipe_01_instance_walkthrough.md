# Recipe 01: Instance Overview & Strategy Walkthrough (Component 1)

## 1. Objective & Purpose
Establish a quantitative baseline of the Looker environment, auditing instance topology, developer licensing, query throughput capacity, and strategic stakeholder pain points across business domains.

```
                   INSTANCE STRATEGY DISCOVERY FRAMEWORK
 ┌───────────────────────────┬───────────────────────────┬───────────────────────────┐
 │ Technical Baseline        │ Stakeholder Pain Points   │ Architectural Governance  │
 ├───────────────────────────┼───────────────────────────┼───────────────────────────┤
 │ • Query Throughput & SLAs │ • Slow Dashboards & Looks │ • Multi-tier Environments │
 │ • Worker & Pool Capacity  │ • Confusing Field Pickers │ • Git & PR Workflows      │
 │ • Developer License Ratio │ • Unresponsive Schedules  │ • Group-Based RBAC & GBAC │
 └───────────────────────────┴───────────────────────────┴───────────────────────────┘
```

---

## 2. Diagnostic Execution Protocols (Looker System Activity)

### Step 1: Query Instance Scale & High-Level KPIs
Execute query against `system__activity.query_metrics` and `history` to capture instance scale over the past 30 days:
```json
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "history.query_run_count",
    "history.database_result_query_count",
    "query_metrics.async_processing_average",
    "query_metrics.execute_main_query_average",
    "query_metrics.acquire_connection_average"
  ],
  "filters": {
    "history.created_date": "30 days"
  },
  "limit": "1"
}
```

### Step 2: Developer & User License Audit
Audit active versus assigned licenses to detect license bloat:
```json
{
  "model": "system__activity",
  "view": "user",
  "fields": [
    "user.count",
    "permission_set.name",
    "user.is_disabled"
  ],
  "filters": {
    "user.is_disabled": "No"
  },
  "pivots": ["permission_set.name"],
  "limit": "50"
}
```

### Step 3: Top 10 Most Queried Explores & Dashboards
```json
{
  "model": "system__activity",
  "view": "history",
  "fields": [
    "query.view",
    "dashboard.title",
    "history.query_run_count",
    "history.average_runtime"
  ],
  "filters": {
    "history.created_date": "30 days",
    "query.view": "-NULL"
  },
  "sorts": ["history.query_run_count desc"],
  "limit": "10"
}
```

---

## 3. Stakeholder Discovery Interview Matrix

| Stakeholder Role | Key Discovery Focus Questions | Diagnostic Target |
| :--- | :--- | :--- |
| **Head of Data / BI Lead** | • What are the core 3–5 executive business dashboards?<br>• What is the target dashboard load SLA (e.g. < 5s)?<br>• How is data team capacity allocated between new builds vs. maintenance? | Define business SLAs and critical KPI paths. |
| **Lead LookML Developer** | • What is the Git branching and code review strategy?<br>• Are models organized as monolithic files or modular explores?<br>• How often are PDTs rebuilt during business hours? | Identify code maintainability and modeling anti-patterns. |
| **Department Business Analyst** | • Which explores are confusing or contain too many fields?<br>• Are you frequently forced to use Merged Queries or Excel exports?<br>• Which dashboards take longer than 15 seconds to load? | Uncover usability friction and user-side workarounds. |
| **Cloud FinOps / Infrastructure** | • What database warehouse powers Looker (BigQuery, Snowflake)?<br>• What are the monthly query compute cost trends?<br>• Are dedicated BI slot reservations or warehouse clusters configured? | Identify database cost runaway and compute bottlenecks. |

---

## 4. Environment Topology & Architectural Governance Checklist

- [ ] **Multi-Tier Environment Setup**: Are Development, QA/Staging, and Production separated (either via multiple instances or protected Git branches)?
- [ ] **Connection Pool Sizing**: Is `max_connections` sized appropriately for the number of cluster nodes (typical baseline: 30–50 connections per node)?
- [ ] **PDT Maintenance Window**: Are Persistent Derived Tables scheduled to build off-peak via Datagroup ETL triggers rather than arbitrary intervals?
- [ ] **Developer Mode Deployment Frequency**: Are developers deploying directly to production during peak morning dashboard usage hours?

---

## 5. Deliverable: Executive Baseline Scorecard Template

```markdown
# Looker Instance Healthcheck: Executive Baseline
* **Instance URL**: `https://<instance_url>.looker.com`
* **Audit Period**: Past 30 Days

### 📈 Throughput & SLA Metrics
* **Total 30-Day Query Volume**: `<TOTAL_QUERIES>` queries
* **Average Async Query Processing**: `<ASYNC_AVG>`s *(Target: < 5.0s)*
* **Average Database Execution**: `<EXECUTE_AVG>`s *(Target: < 4.5s)*
* **Cache Hit Rate**: `<CACHE_HIT_PCT>`% *(Target: > 50.0%)*

### 👥 User & License Footprint
* **Active Licensed Developers**: `<DEV_COUNT>`
* **Active Viewers / Explorers**: `<VIEWER_COUNT>`
* **Deactivated / Inactive Accounts**: `<INACTIVE_COUNT>`
```
