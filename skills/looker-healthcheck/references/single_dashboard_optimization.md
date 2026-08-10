# Single Dashboard Optimization & Forensic Audit (Deep-Dive)

This reference document defines the **Single Dashboard Forensic Audit Framework** extracted from the `google_pso__dashboard_optimisation_` dashboard. It provides the exact 10-point checklist and per-tile breakdown query for optimizing any individual Looker dashboard.

---

## 1. The 10-Point Dashboard Optimization Checklist

When diagnosing a slow dashboard (`Dashboard ID`), evaluate these 10 architectural criteria:

```
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                       10-POINT DASHBOARD FORENSIC AUDIT CHECKLIST                           │
 ├────┬─────────────────────────────┬───────────────────────────┬──────────────────────────────┤
 │ #  │ Audit Dimension             │ Target Best Practice      │ Optimization Trigger         │
 ├────┼─────────────────────────────┼───────────────────────────┼──────────────────────────────┤
 │ 1  │ Total Query Tiles           │ ≤ 25 query tiles          │ > 25 (Deconstruct / tabs)    │
 │ 2  │ Run on Load Setting         │ Disabled if filtered      │ Enabled when filters required│
 │ 3  │ Date Filters Present        │ Mandatory for time-series │ Missing (Scans full history) │
 │ 4  │ Max Row Limits              │ ≤ 50 for KPI / single-val │ 5,000 limit on single value  │
 │ 5  │ Auto-Refresh Interval       │ Off (or > 30 mins for TV) │ < 5 mins (Saturates pool)    │
 │ 6  │ Merged Query Tiles          │ 0 (Native LookML joins)   │ ≥ 1 (In-memory merge lag)    │
 │ 7  │ Formatted Pivots            │ Low cardinality only      │ High cardinality pivots      │
 │ 8  │ Custom Fields / Table Calcs │ Built in LookML           │ > 3 ad-hoc dynamic fields    │
 │ 9  │ Number of Explores Used     │ Scoped lightweight views  │ Heavy transaction explores   │
 │ 10 │ Full Completed Runtime      │ < 5.0 seconds             │ > 10.0s (Tile bottleneck)    │
 └────┴─────────────────────────────┴───────────────────────────┴──────────────────────────────┘
```

---

## 2. Forensic Single-Dashboard Queries

### A. Dashboard 360-Degree Metadata Scorecard
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "dashboard",
  "fields": [
    "dashboard.id",
    "dashboard.title",
    "dashboard.run_on_load",
    "dashboard.refresh_interval_ordered",
    "dashboard_element.total_query_tiles",
    "dashboard_element.count_text",
    "dashboard_element.count_merge_query",
    "user.name",
    "updated_by.name"
  ],
  "filters": {
    "dashboard.id": "<TARGET_DASHBOARD_ID>",
    "dashboard.moved_to_trash": "No"
  },
  "limit": "1"
}' --verify-ssl=false
```

### B. Per-Tile Query Lifecycle Breakdown (Isolate Slowest Tiles)
Identify which specific tiles are database-bound vs post-processing bound:
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "dashboard_element.id",
    "dashboard_element.title",
    "history.average_runtime",
    "query_metrics.execute_main_query_average",
    "query_metrics.acquire_connection_average",
    "query_metrics.per_user_throttler_average",
    "query_metrics.prepare_average",
    "query_metrics.stream_to_cache_average",
    "query_metrics.postprocessing_average"
  ],
  "filters": {
    "dashboard.id": "<TARGET_DASHBOARD_ID>",
    "dashboard_element.title": "-NULL"
  },
  "sorts": ["history.average_runtime desc"],
  "limit": "50"
}' --verify-ssl=false
```

### C. Row Limit & Custom Field Audit per Tile
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "dashboard",
  "fields": [
    "dashboard_element.id",
    "dashboard_element.title",
    "query.limit",
    "query.dynamic_fields",
    "query.formatted_pivots"
  ],
  "filters": {
    "dashboard.id": "<TARGET_DASHBOARD_ID>",
    "dashboard_element.type": "vis,data"
  },
  "limit": "50"
}' --verify-ssl=false
```

---

## 3. High-Impact Remediation Recipes

### 1. Disable "Run on Load" for Filter-Heavy Dashboards
* If a dashboard requires users to select specific date ranges, accounts, or regions before analyzing, uncheck **Run on Load**. This prevents 15-25 default unpartitioned queries from firing upon every page open.

### 2. Rightsize Row Limits
* Ensure single-value cards, pie charts, and top-10 bar charts set `limit: 10` or `limit: 50` rather than defaulting to `limit: 5000`.

### 3. Replace High-Cardinality Pivots with Native Metrics
* Instead of pivoting a dimension with 50 unique values (creating 50 memory columns), define specific filtered measures in LookML (e.g. `type: sum`, `filters: [status: "complete"]`).
