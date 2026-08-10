# Recipe 02: Performance Audit Review (Component 2)

## 1. Objective & Scope
Execute a deep diagnostic audit of query lifecycle latencies, database execution times, concurrency bottlenecks, and Looker overhead across the 8 core analytical tabs of the **Consolidated Healthcheck Dashboard**:
1. **Sources Drilldown**: Processing by Model, Dashboard, Explore, User, Connection, and Errors.
2. **KPI Scorecard**: 3-phase timing metrics against benchmark thresholds.
3. **Query Analysis**: Daily timeseries, stacked area phase distribution, query source & status breakdowns.
4. **Outliers**: Max timings per phase, bottom 20 slowest queries, and outlier query links.
5. **History Analysis**: Historical query trends and runtime tiers.
6. **Content Delivery**: Schedules, PDF exports, and delivery failure rates.
7. **Large Dashboards**: Auditing tiles > 25.
8. **Merged Queries**: Identifying queries spawning sub-queries.

---

## 2. Diagnostic Execution Protocols

### A. Core Lifecycle & Overhead Scorecard
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "query_metrics.async_processing_average",
    "query_metrics.execute_main_query_average",
    "query_metrics.acquire_connection_average",
    "query_metrics.project_init_average",
    "query_metrics.model_init_computed_average",
    "query_metrics.model_init_cache_average",
    "query_metrics.explore_init_average",
    "query_metrics.marshalled_cache_load_average",
    "query_metrics.prepare_average",
    "query_metrics.queued_average",
    "query_metrics.per_user_throttler_average",
    "query_metrics.stream_to_cache_average",
    "query_metrics.postprocessing_average",
    "query_metrics.load_main_query_in_memory_average",
    "query_metrics.load_process_and_stream_main_query_average",
    "query_metrics.execute_totals_query_average",
    "query_metrics.execute_row_totals_query_average",
    "query_metrics.execute_grand_totals_query_average",
    "history.query_run_count",
    "history.database_result_query_count"
  ],
  "limit": "1"
}' --verify-ssl=false
```

### B. Sources Breakdown (Identify Top Offenders)
```bash
# 1. Processing by Model
looker-cli api query run_inline_query --body '{
  "model": "system__activity", "view": "query_metrics",
  "fields": ["query.model", "history.query_run_count", "query_metrics.async_processing_average"],
  "filters": {"query.model": "-NULL"},
  "sorts": ["history.query_run_count desc"], "limit": "15"
}' --verify-ssl=false

# 2. Processing by Dashboard
looker-cli api query run_inline_query --body '{
  "model": "system__activity", "view": "query_metrics",
  "fields": ["dashboard.title", "history.query_run_count", "query_metrics.async_processing_average"],
  "filters": {"dashboard.title": "-NULL"},
  "sorts": ["history.query_run_count desc"], "limit": "15"
}' --verify-ssl=false

# 3. Processing by Explore
looker-cli api query run_inline_query --body '{
  "model": "system__activity", "view": "query_metrics",
  "fields": ["query.view", "history.query_run_count", "query_metrics.execute_main_query_average"],
  "filters": {"query.view": "-NULL"},
  "sorts": ["history.query_run_count desc"], "limit": "15"
}' --verify-ssl=false

# 4. Processing by Errors
looker-cli api query run_inline_query --body '{
  "model": "system__activity", "view": "query_metrics",
  "fields": ["history.message", "history.query_run_count", "query_metrics.async_processing_average"],
  "filters": {"history.status": "error", "history.message": "-NULL"},
  "sorts": ["history.query_run_count desc"], "limit": "15"
}' --verify-ssl=false
```

### C. Top 20 Outlier Queries (Slowest Async Runtime)
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity", "view": "query_metrics",
  "fields": [
    "query.id", "user.name", "query.view", "dashboard.title",
    "query_metrics.async_processing", "query_metrics.execute_main_query",
    "query_metrics.acquire_connection", "query_metrics.stream_to_cache"
  ],
  "sorts": ["query_metrics.async_processing desc"], "limit": "20"
}' --verify-ssl=false
```

---

## 3. Diagnostic Decision Tree & Remediation

```
                                  QUERY BOTTLENECK DIAGNOSIS
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ▼                                    ▼                                    ▼
[INIT PHASE SLOW]                    [EXECUTION PHASE SLOW]               [POST-PROCESSING SLOW]
 • project_init > 0.10s               • acquire_connection > 0.238s        • stream_to_cache > 0.223s
   ──► Hub & Spoke modularization       ──► Increase connection pool         ──► Reduce row limits (e.g. 5000 -> 50)
 • model_init_computed > 2.42s        • per_user_throttler > 0             • postprocessing > 0.223s
   ──► Break models into domains        ──► Stagger schedules & tile budget  ──► Move Table Calcs to SQL/LookML
 • explore_init > 0.233s              • execute_main_query > 4.87s         • totals_query > 0.238s
   ──► Prune unneeded joins/fields      ──► PDT Partitioning/Clustering      ──► Disable unnecessary grand totals
```
