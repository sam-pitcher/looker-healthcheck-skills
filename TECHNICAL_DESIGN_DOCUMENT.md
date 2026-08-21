---
type: Technical Design Document
title: "Looker Health Check - Technical Design Document"
description: "Comprehensive Looker & BigQuery performance remediation, LookML modeling optimization, and warehouse modernization specification for thelook-antigravity."
status: stable
tags: [looker, bigquery, healthcheck, modernization, tdd, performance, lookml]
generated: { by: looker_healthcheck_agent/gemini-2.5-pro, at: 2026-08-20T17:23:00Z }
verified: { by: human:sampitcher, at: 2026-08-20T17:30:00Z }
sources:
  - id: system-activity-query-metrics
    resource: system__activity/query_metrics
    title: Looker System Activity Query Metrics Explore
    author: process:looker-system-activity
  - id: bq-jobs-timeline
    resource: region-us.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT
    title: BigQuery Jobs Timeline by Project
    author: process:bigquery-information-schema
  - id: thelook-lookml
    resource: /projects/thelook-antigravity
    title: TheLook LookML Repository
    author: human:sampitcher
---

# Looker Health Check - Technical Design Document

**Model:** `thelook-antigravity`
**Timestamp:** 2026-08-20T17:23:00Z

This document outlines the findings and remediation steps from the comprehensive Looker health check, grounded in System Activity telemetry[^system-activity-query-metrics] and BigQuery jobs data.[^bq-jobs-timeline]

---

## Pillar 1: Looker Performance

### 1.1 Unbounded High-Volume Explores (CRITICAL)

*   **Finding:** The `events` and `interaction_logs` explores are not filtered on a partition key.
*   **Impact:** Risk of full table scans, leading to high query costs and slow performance.
*   **Remediation:** Enforce a filter on a date/partition field using `conditionally_filter` or `always_filter`.[^thelook-lookml]

    ```lookml
    # models/thelook.model.lkml

    explore: events {
      conditionally_filter: {
        filters: [created_at_date: "30 days"]
        unless: [user_id]
      }
    }
    ```

### 1.2 Volatile Datagroup Triggers (CRITICAL)

*   **Finding:** Datagroups `thelook_default_datagroup` and `daily` use volatile `sql_trigger` functions (`GENERATE_UUID()`, `current_date()`).
*   **Impact:** Forces cache invalidation on every query, overwhelming database slots.
*   **Remediation:** Use a stable, time-based trigger.

    ```lookml
    # models/thelook.model.lkml

    datagroup: thelook_default_datagroup {
      sql_trigger: SELECT MAX(etl_timestamp) FROM etl_log;;
      max_cache_age: "24 hours"
    }
    ```

### 1.3 Dashboard Performance Anti-Patterns (CRITICAL)

*   **Finding:** Detected dashboards with >25 tiles, aggressive 1-minute auto-refresh, client-side merged queries, and excessive table calculations.
*   **Impact:** Poor user experience, browser lockups, and high database load.
*   **Remediation:**
    *   Break down large dashboards into smaller, more focused ones.
    *   Increase refresh intervals to >30 minutes.
    *   Refactor merged queries into LookML joins.
    *   Materialize table calculations in LookML or PDTs.

---

## Pillar 2: BigQuery & SQL Optimization

### 2.1 Unpartitioned Warehouse Tables (CRITICAL)

*   **Finding:** Key fact tables like `events_table` and `order_items_table` are not partitioned in BigQuery.
*   **Impact:** Full table scans result in high costs and slow query performance.
*   **Remediation:** Partition these tables by a date column (e.g., `created_at`).

    ```sql
    -- Example BigQuery DDL for partitioning
    CREATE TABLE the_look_ca.events_table_partitioned
    PARTITION BY DATE(created_at)
    AS SELECT * FROM the_look_ca.events_table;
    ```

### 2.2 BigQuery Slot Contention (CRITICAL)

*   **Finding:** Peak BigQuery slot usage is hitting the reservation limit of 2000 slots.
*   **Impact:** Queries are being queued and throttled, leading to slow dashboard loads.
*   **Remediation:** Investigate the most resource-intensive queries during peak hours. Optimize the underlying LookML or consider increasing the slot reservation.

---

## Pillar 3: LookML Modeling & Code Quality

### 3.1 Missing Primary Keys (CRITICAL)

*   **Finding:** 5 views are missing a `primary_key: yes` declaration, including `orders` and `users`.
*   **Impact:** Prevents Looker from correctly calculating symmetric aggregates, leading to fanned-out, incorrect results.
*   **Remediation:** Add `primary_key: yes` to the unique identifier field in each view.

    ```lookml
    # thelook_views/orders.view.lkml

    dimension: id {
      primary_key: yes
      type: number
      sql: ${TABLE}.id ;;
    }
    ```

### 3.2 SQL Anti-Patterns in Joins (CRITICAL)

*   **Finding:** Detected inequality joins, functions in `sql_on`, and a `type: cross` join.
*   **Impact:** These patterns disable BigQuery's hash join optimizations, leading to extremely inefficient nested loop or cross product operations.
*   **Remediation:**
    *   Refactor inequality and function-based joins into derived tables.
    *   Remove cross joins unless absolutely necessary and validated.

### 3.3 Raw Key Exposure & Missing Descriptions (WARNING)

*   **Finding:** 20 technical ID fields are exposed to users, and 21 measures are missing `description:` tags.
*   **Impact:** Clutters the UI and makes the model difficult for business users to understand and trust.
*   **Remediation:**
    *   Add `hidden: yes` to all ID fields.
    *   Add clear, concise `description:` tags to all user-facing fields.

---

[^system-activity-query-metrics]: Looker System Activity Query Metrics Explore
[^bq-jobs-timeline]: BigQuery Jobs Timeline by Project
[^thelook-lookml]: TheLook LookML Repository
