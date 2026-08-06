# System Activity Diagnostic Query Catalog

Use these pre-crafted Looker CLI queries against `system__activity` to audit and benchmark any Looker instance.

---

## 1. Top Slowest Outlier Queries
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "query.id",
    "user.name",
    "dashboard.title",
    "query.view",
    "query_metrics.async_processing",
    "query_metrics.execute_main_query",
    "query_metrics.per_user_throttler",
    "history.created_time"
  ],
  "sorts": ["query_metrics.async_processing desc"],
  "limit": "25"
}' --verify-ssl=false
```

---

## 2. Average Phase Breakdown by Model
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "query.model",
    "history.query_run_count",
    "query_metrics.async_processing_average",
    "query_metrics.model_init_computed_average",
    "query_metrics.explore_init_average",
    "query_metrics.execute_main_query_average",
    "query_metrics.stream_to_cache_average"
  ],
  "filters": {
    "query.model": "-NULL"
  },
  "sorts": ["history.query_run_count desc"],
  "limit": "20"
}' --verify-ssl=false
```

---

## 3. High-Throttling Dashboards Audit
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "dashboard.title",
    "history.query_run_count",
    "query_metrics.per_user_throttler_average",
    "query_metrics.queued_average",
    "query_metrics.async_processing_average"
  ],
  "filters": {
    "dashboard.title": "-NULL",
    "query_metrics.per_user_throttler": ">0"
  },
  "sorts": ["query_metrics.per_user_throttler_average desc"],
  "limit": "20"
}' --verify-ssl=false
```

---

## 4. Connection Pool & Acquire Time Bottlenecks
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "history.connection_name",
    "history.query_run_count",
    "query_metrics.acquire_connection_average",
    "query_metrics.async_processing_average"
  ],
  "filters": {
    "history.connection_name": "-NULL"
  },
  "sorts": ["query_metrics.acquire_connection_average desc"],
  "limit": "15"
}' --verify-ssl=false
```
