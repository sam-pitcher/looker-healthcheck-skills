# Query Outliers Diagnostic Framework (Deep-Dive)

This reference document defines the **3-Way Outlier Decomposition** and per-phase maximum outlier isolation methodology extracted from the `google_cloud__query_outliers` dashboard.

---

## 1. The 3-Way Outlier Decomposition Model

When investigating slow queries, total runtime (`async_processing`) alone is misleading. Queries must be classified into one of three distinct root-cause buckets:

```
                                  BOTTOM 20 SLOWEST QUERIES
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ▼                                    ▼                                    ▼
[BUCKET 1: DATABASE SLOW]           [BUCKET 2: LOOKER OVERHEAD SLOW]     [BUCKET 3: QUEUE / CONNECTION SLOW]
Sort: execute_main_query desc       Sort: (async - main_query) desc      Sort: queued / per_user_throttler desc
 • Warehouse compute constraint      • Massive unpruned row limits (>5k)  • Dashboard > 25 tiles
 • Unindexed / non-partitioned       • Heavy table calculations & pivots  • 15 queries/node user throttle
 • Compiler symmetric aggregation    • Grand totals / row totals          • Unstaggered concurrent schedules
```

---

## 2. Per-Phase Maximum Outlier Isolation

To pinpoint the exact architectural failure point on an instance, query the single worst query (`limit: 1`, `sort: [field desc]`) across every phase:

| Phase | Target Outlier Field | High Value Diagnostic Interpretation |
| :--- | :--- | :--- |
| **Async Total** | `query_metrics.async_processing` | Absolute worst user-facing query experience. |
| **Queue Time** | `query_metrics.queued` | Looker worker pool exhausted; thread contention. |
| **Connection Pool** | `query_metrics.acquire_connection` | Database connection pool limits reached or slow auth handshake. |
| **Connection Hold** | `query_metrics.connection_held` | Database connection held open too long by streaming/waiting. |
| **Per-User Throttle**| `query_metrics.per_user_throttler` | Single user exceeded 15 concurrent query cap (large dashboard / merged queries). |
| **Project Init** | `query_metrics.project_init` | Monolithic project with too many view/model files. |
| **Model Init (Comp)**| `query_metrics.model_init_computed` | Heavy un-cached model compilation; needs model scoping. |
| **Model Init (Cache)**|`query_metrics.model_init_cache` | Cache validation lag; high deployment frequency at peak hours. |
| **Explore Init (Comp)**|`query_metrics.explore_init` | Complex explore with excessive joins and dimensions. |
| **Explore Init (Cache)**|`query_metrics.marshalled_cache_load`| Heavy serialized explore schema. |
| **Prepare Time** | `query_metrics.prepare` | LookML SQL compilation lag; move calculations to DB/LookML. |
| **Database Execution**| `query_metrics.execute_main_query` | Unoptimized SQL query scanning massive raw warehouse partitions. |
| **Totals Execution**| `query_metrics.execute_totals_query` | Subtotal query executed separately from main query. |
| **Row Totals Exec** | `query_metrics.execute_row_totals_query`| Row total query executed separately from main query. |
| **Grand Totals Exec**| `query_metrics.execute_grand_totals_query`| Grand total query executed separately from main query. |
| **PDT Build** | `query_metrics.pdt` | Slow derived table materialization blocking query. |
| **Post-Processing** | `query_metrics.post_processing` | Client-side calculations, sorting, and formatting overhead. |
| **Stream to Cache** | `query_metrics.stream_to_cache` | High row counts being streamed across network to browser cache. |
| **In-Memory Loading**| `query_metrics.load_main_query_in_memory`| Non-streamed query loading massive result set into Looker RAM. |

---

## 3. Analytical Outlier Queries

### A. Bottom 20 Queries by Database Execution Time
```json
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": ["query.id", "query_metrics.execute_main_query_average"],
  "sorts": ["query_metrics.execute_main_query_average desc"],
  "limit": "20"
}
```

### B. Bottom 20 Queries by Looker Processing / Overhead
```json
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "query.id",
    "query_metrics.async_processing",
    "query_metrics.execute_main_query"
  ],
  "sorts": ["query_metrics.async_processing desc"],
  "limit": "20"
}
```

### C. Explores, Models, Dashboards, and Users Outliers
```json
# Top 20 Explores by Async Runtime
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": ["query.view", "query_metrics.async_processing_average"],
  "sorts": ["query_metrics.async_processing_average desc"],
  "limit": "20"
}

# Top 20 Dashboards by Async Runtime
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": ["dashboard.title", "query_metrics.async_processing_average"],
  "filters": {"dashboard.title": "-NULL"},
  "sorts": ["query_metrics.async_processing_average desc"],
  "limit": "20"
}

# Top 20 Users by Async Runtime
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": ["user.name", "query_metrics.async_processing_average"],
  "filters": {"user.name": "-NULL"},
  "sorts": ["query_metrics.async_processing_average desc"],
  "limit": "20"
}
```
