# Merged Queries Diagnostic & Remediation Playbook (Deep-Dive)

This reference document defines the risks, diagnostic audit queries, and native LookML migration protocols extracted from the `google_pso__merged_queries` dashboard.

---

## 1. Why Merged Queries Degrade Cluster Performance

A Looker Merged Query is an **in-memory, client-side join** that bypasses database optimization:

```
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                           MERGED QUERY EXECUTION ARCHITECTURE                               │
 ├─────────────────────────────────────────────────────────────────────────────────────────────┤
 │ 1. Spawns N parallel sub-queries to the database warehouse (saturating user connection cap). │
 │ 2. Downloads raw result sets (up to 5,000 rows each) over the network into Looker memory.  │
 │ 3. Joins datasets in Looker RAM using single-threaded CPU workers.                          │
 │ 4. Applies pivots and table calculations on top of the unindexed in-memory dataset.        │
 └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

> [!WARNING]
> **Performance Threat**: Merged queries lock Looker worker threads in heavy `postprocessing`, cause out-of-memory (OOM) crashes on large datasets, and trigger `per_user_throttler` queueing for other users on the instance.

---

## 2. Key Diagnostic Thresholds

| Metric | System Activity Field / Formula | Target | Warning Threshold | Critical Threshold |
| :--- | :--- | :---: | :---: | :---: |
| **Merged Query % of Total** | `merge_queries / total_queries` | **`< 1.0%`** | `> 5.0%` | `> 10.0%` |
| **Source Queries per Tile** | `merge_query_source_query.count` | **`1` (No merge)** | `2` | `≥ 3` |
| **Compound Overhead** | Merge Query + Dynamic Fields + Pivots | **`None`** | Any table calc | Table calc + Pivot |

---

## 3. Diagnostic Audit Queries

### A. Dashboards with Highest Merged Query Concentration
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "dashboard",
  "fields": [
    "dashboard.id",
    "dashboard.title",
    "dashboard_element.count_merge_query",
    "query.count"
  ],
  "filters": {
    "merge_query_source_query.count": ">0",
    "dashboard.moved_to_trash": "No"
  },
  "sorts": ["dashboard_element.count_merge_query desc"],
  "limit": "25"
}' --verify-ssl=false
```

### B. Worst Merged Queries (High Source Counts, Pivots, Table Calculations)
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "dashboard",
  "fields": [
    "dashboard.id",
    "dashboard.title",
    "dashboard_element.title",
    "user.name",
    "merge_query_source_query.count",
    "merge_query.formatted_pivots",
    "merge_query.dynamic_fields"
  ],
  "filters": {
    "merge_query.id": "NOT NULL",
    "dashboard.moved_to_trash": "No"
  },
  "sorts": ["merge_query_source_query.count desc"],
  "limit": "25"
}' --verify-ssl=false
```

---

## 4. Step-by-Step LookML Migration Playbook

### Step 1: Analyze the Merged Query Components
Inspect the source explores, fields, and join keys used in the merged result.

### Step 2: Implement Native LookML Join or Derived Table
Instead of performing an in-memory merge, model the relationship natively:

```lookml
# ANTI-PATTERN (In-Memory Merged Result in Dashboard UI)
# Explore 1: Orders (5,000 rows) MERGED WITH Explore 2: Ad_Spend (5,000 rows)

# REFACTORED BEST PRACTICE (Native LookML Join or PDT)
view: order_ad_spend_summary {
  derived_table: {
    sql:
      SELECT
        o.order_date,
        o.country,
        SUM(o.order_amount) AS total_revenue,
        SUM(a.spend) AS total_ad_spend
      FROM ${orders.SQL_TABLE_NAME} o
      LEFT JOIN ${ad_spend.SQL_TABLE_NAME} a
        ON o.order_date = a.date AND o.country = a.country
      GROUP BY 1, 2 ;;
  }
}
```

### Step 3: Replace Dashboard Tile
Point the dashboard tile to the new native LookML explore, eliminating in-memory processing and enabling full database pushdown caching.
