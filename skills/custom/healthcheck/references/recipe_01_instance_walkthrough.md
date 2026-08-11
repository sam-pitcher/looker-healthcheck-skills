# Recipe 01: Instance Overview & Strategy Walkthrough (Component 1)

## 1. Objective & Purpose
Establish a comprehensive baseline of the Looker environment, identifying core business use cases, licensed developers, high-level query throughput, and primary stakeholder pain points.

---

## 2. Diagnostic Execution Protocol

### Step 1: Query Instance Metadata & High-Level KPIs
Execute query against `system__activity.query_metrics` and `history` to capture instance scale:
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "history.query_run_count",
    "query_metrics.async_processing_average",
    "query_metrics.execute_main_query_average"
  ],
  "limit": "1"
}' --verify-ssl=false
```

### Step 2: License & Developer Count
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "user",
  "fields": ["user.count"],
  "filters": {
    "user.is_disabled": "No",
    "permission_set.permissions": "%develop%"
  },
  "limit": "1"
}' --verify-ssl=false
```

---

## 3. Discovery & Evaluation Questions
When engaging with the customer or evaluating the codebase:
1. **Use Case**: Embedded analytics vs internal business intelligence?
2. **Data Sources**: Which database warehouse (BigQuery, Snowflake, Redshift) powers the connection?
3. **Pain Points**: What specific dashboards or explores are reported as painfully slow by end users?

---

## 4. Output Deliverable
Generate the **Executive Summary Scorecard** documenting:
- Total historical query volume.
- Average async query processing latency vs benchmark (< 5.0s).
- Number of active developer seats and business users.
