# Looker System Activity Query Catalog

This catalog documents the exact Looker API query definitions, dynamic fields, and table calculations extracted from the **Consolidated Healthcheck Dashboard**.

---

## 1. Looker Overhead & Timing Calculations

### Dynamic Dimensions:
- **`is_async_runtime_value_populated`**:
  `query_metrics.async_processing > 0`
- **`was_per_user_throttling_applied_yesno`**:
  `query_metrics.per_user_throttler > 0`
- **`looker_processing_time`**:
  `query_metrics.async_processing - query_metrics.execute_main_query`
- **`looker_overhead`**:
  `(query_metrics.async_processing - (query_metrics.execute_main_query + query_metrics.acquire_connection)) / query_metrics.async_processing`

### Table Calculations:
- **`looker_overhead_pct`**:
  `(((${average_of_execute_main_query} + ${average_of_acquire_connection}) / ${average_of_async_processing}) - 1) * (-1)`
- **`overhead_time_seconds`**:
  `${average_of_async_processing} - (${average_of_execute_main_query} + ${average_of_acquire_connection})`
- **`cache_percent`**:
  `1 - (${history.database_result_query_count} / ${history.query_run_count})`

---

## 2. Query Metrics Exploration Queries

### A. Lifecycle Timing Averages
```json
{
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
    "query_metrics.postprocessing_average"
  ],
  "limit": "1"
}
```

### B. Outlier Max Values
```json
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "query.id",
    "user.name",
    "query.view",
    "dashboard.title",
    "query_metrics.async_processing",
    "query_metrics.execute_main_query",
    "query_metrics.stream_to_cache",
    "query_metrics.per_user_throttler"
  ],
  "sorts": ["query_metrics.async_processing desc"],
  "limit": "20"
}
```

### C. Errors Breakdown
```json
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "history.message",
    "history.query_run_count",
    "query_metrics.async_processing_average"
  ],
  "filters": {
    "history.status": "error",
    "history.message": "-NULL"
  },
  "sorts": ["history.query_run_count desc"],
  "limit": "15"
}
```
