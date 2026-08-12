# Query Outliers Diagnostic & Forensic Isolation Playbook

This reference document defines the **3-Way Outlier Decomposition** and per-phase maximum outlier isolation methodology for locating and remediating anomalous query runtimes.

---

## 🔍 Part 1: How to Review & Diagnose Outliers

### 1. The 3-Way Outlier Decomposition Model

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

### 2. Per-Phase Maximum Outlier Isolation

To pinpoint the exact architectural failure point on an instance, query the single worst outlier across every query lifecycle phase:

| Phase | Target Outlier Field | High-Value Diagnostic Interpretation |
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

### 3. Outlier Extraction Telemetry Queries

#### A. Bottom 20 Queries by Database Execution Time
```json
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "query.id",
    "query.model",
    "query.view",
    "dashboard.title",
    "query_metrics.execute_main_query"
  ],
  "filters": {
    "history.created_date": "7 days"
  },
  "sorts": ["query_metrics.execute_main_query desc"],
  "limit": "20"
}
```

#### B. Bottom 20 Queries by Looker Processing / Overhead
```json
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "query.id",
    "query.model",
    "query.view",
    "query_metrics.async_processing",
    "query_metrics.execute_main_query",
    "query_metrics.postprocessing"
  ],
  "filters": {
    "history.created_date": "7 days"
  },
  "sorts": ["query_metrics.async_processing desc"],
  "limit": "20"
}
```

---

## 🛠️ Part 2: How to Rectify & Remediate Outliers

### Protocol 1: Remediating Database Outliers (`execute_main_query > 15.0s`)
1. **Analyze Generated SQL & EXPLAIN Plan**:
   * Copy the query SQL from Looker and run `EXPLAIN` in BigQuery / Snowflake. Look for unpruned partition scans or high-cardinality nested joins.
2. **Apply Partition/Cluster Filter Guards**:
   * Enforce `conditionally_filter` in the explore to prevent full-table historical scans.
3. **Materialize into PDTs**:
   * If a query joins 5+ tables with complex row aggregations, build a Persistent Derived Table with `datagroup_trigger:`.

### Protocol 2: Remediating Looker Overhead Outliers (`postprocessing > 0.5s`)
1. **Prune High-Cardinality Pivots**:
   * Pivots containing $>50$ unique columns generate extreme browser rendering lag. Limit pivots to small categorical dimensions.
2. **Remove Complex String Table Calculations**:
   * Replace regex-heavy frontend table calculations with database SQL dimensions.

### Protocol 3: Remediating Throttler & Queue Outliers (`per_user_throttler > 0.0s`)
1. **Deconstruct Multiplying Dashboards**:
   * Large dashboards with $>25$ tiles trigger Looker's 15 queries/node limit, putting subsequent tiles in a wait state. Deconstruct into tabs.
2. **Eliminate Merged Tiles**:
   * Merged tiles run $N$ independent queries per tile simultaneously, quickly exhausting user concurrency limits.
