# Looker System Activity Query Catalog & Telemetry Bank

This reference catalog documents the exact JSON query definitions, dimensions, and table calculation formulas for querying Looker's internal `system__activity` models.

---

## 1. System Activity Calculation Formulas

### Table Calculations:
* **`looker_overhead_pct`**:
  `(((${average_of_execute_main_query} + ${average_of_acquire_connection}) / ${average_of_async_processing}) - 1) * (-1)`
* **`overhead_time_seconds`**:
  `${average_of_async_processing} - (${average_of_execute_main_query} + ${average_of_acquire_connection})`
* **`cache_hit_ratio`**:
  `1 - (${history.database_result_query_count} / ${history.query_run_count})`
* **`dashboard_error_rate`**:
  `(${history.error_query_count} / ${history.total_query_count}) * 100`

---

## 2. Complete Telemetry Query Bank

### Query 1: Master 12-Stage Query Lifecycle Scorecard
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

### Query 2: Dashboards Exceeding 25 Query Tiles
```json
{
  "model": "system__activity",
  "view": "dashboard",
  "fields": [
    "dashboard.id",
    "dashboard.title",
    "dashboard_element.count",
    "dashboard_element.count_text",
    "dashboard_element.count_look",
    "dashboard_element.count_merge_query"
  ],
  "filters": {
    "dashboard_element.count": ">25",
    "dashboard.moved_to_trash": "No"
  },
  "sorts": ["dashboard_element.count desc"],
  "limit": "50"
}
```

### Query 3: Active Scheduled Deliveries Owned by Inactive Users (Zombie Schedules)
```json
{
  "model": "system__activity",
  "view": "user",
  "fields": [
    "user.id",
    "user.name",
    "user_facts.last_ui_login_date",
    "scheduled_plan.count",
    "scheduled_plan.name"
  ],
  "filters": {
    "user_facts.last_ui_login_date": "before 90 days ago",
    "user.is_disabled": "No",
    "scheduled_plan.count": ">0"
  },
  "limit": "50"
}
```

### Query 4: Unused Dashboards (0 Views in Past 90 Days)
```json
{
  "model": "system__activity",
  "view": "dashboard",
  "fields": [
    "dashboard.id",
    "dashboard.title",
    "dashboard.created_time",
    "user.name",
    "history.most_recent_run_at_date",
    "history.query_run_count"
  ],
  "filters": {
    "dashboard.moved_to_trash": "No",
    "history.most_recent_run_at_date": "before 90 days ago"
  },
  "sorts": ["history.query_run_count desc"],
  "limit": "50"
}
```

### Query 5: Persistent Derived Table (PDT) Build Failures
```json
{
  "model": "system__activity",
  "view": "pdt_event_log",
  "fields": [
    "pdt_event_log.view_name",
    "pdt_event_log.action",
    "pdt_event_log.message",
    "pdt_event_log.created_time"
  ],
  "filters": {
    "pdt_event_log.action": "%error%",
    "pdt_event_log.created_time": "7 days"
  },
  "sorts": ["pdt_event_log.created_time desc"],
  "limit": "25"
}
```

### Query 6: Direct Role Assignments (GBAC Violation Audit)
```json
{
  "model": "system__activity",
  "view": "user",
  "fields": [
    "user.id",
    "user.name",
    "user.email",
    "role.name"
  ],
  "filters": {
    "role.embed": "No",
    "user.is_disabled": "No"
  },
  "limit": "50"
}
```
