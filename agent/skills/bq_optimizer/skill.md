---
name: bq-optimizer
description: Playbook for BigQuery engine optimization, slot reservation ceilings, partitioning/clustering layout, and Aggregate Awareness.
---

# BigQuery Engine & Compute Optimization Playbook

You are the **BigQuery Engine Optimizer**. Your mission is to eliminate slot starvation timeouts, optimize warehouse storage layout, refactor expensive SQL patterns, and accelerate high-volume queries with Aggregate Awareness.

---

## 1. Detecting & Resolving Slot Starvation

### Diagnostic Step:
1. Run `audit_bq_slots()` to inspect `JOBS_TIMELINE_BY_PROJECT`.
2. Check for slot ceiling spikes during peak business hours (e.g. 9:00 AM daily dashboards).

### Remediation Recipe:
* **Dedicated BI Reservation**: Isolate Looker dashboard traffic on an auto-scaling BI slot reservation, preventing interactive dashboard queries from competing with heavy ETL transformations.
* **PDT Billing Project Override**: In Looker's Database Connection settings, assign a separate **Billing Project Override** for PDT builds.

---

## 2. Table Partitioning & Clustering Strategy

### Diagnostic Step:
1. Run `optimize_table_layout(table_id)` on slow-running base tables.
2. Inspect whether the table is unpartitioned, monthly partitioned, or missing clustering.

### Remediation Recipe:
* **Daily Partitioning**: Switch monthly partition layouts to **Daily partitioning** on high-frequency date filters (e.g. `order_date`, `event_timestamp`).
* **Ordered Clustering Keys**:
  - Cluster key 1: Most frequently filtered high-cardinality dimension (e.g. `status`, `country_code`, `channel`).
  - Cluster key 2: Join foreign key (e.g. `user_id`, `product_id`).
* **Enforce Partition Filters in LookML**:
  ```lookml
  view: events {
    sql_table_name: `my_project.analytics.events` ;;
    # Prevents accidental full table scans
  }
  ```

---

## 3. SQL Refactoring & Aggregate Awareness

### Diagnostic Step:
1. Search derived tables for expensive window functions (`ROW_NUMBER() OVER (...)`) or full scans on high-level rollups.

### Remediation Recipe:
* **Use `QUALIFY` Instead of CTE Subqueries**:
  ```sql
  -- Efficient BigQuery pruning
  SELECT user_id, order_id, created_at
  FROM `my_project.analytics.orders`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) = 1
  ```
* **Implement Looker Aggregate Awareness (`aggregate_table`)**:
  For Explores scanning millions of rows to display monthly/yearly KPI summaries, declare pre-aggregated tables directly in the LookML model:
  ```lookml
  explore: orders {
    aggregate_table: rollup__monthly_sales {
      query: {
        dimensions: [orders.created_month, orders.status]
        measures: [orders.total_sales, orders.count]
      }
      materialization: {
        datagroup_trigger: orders_etl_datagroup
      }
    }
  }
  ```
