---
type: Technical Design Document
title: "Looker Health Check - Technical Design Document (thelook)"
description: "Comprehensive Looker & BigQuery performance remediation and modernization specification for thelook."
status: stable
tags: [looker, bigquery, healthcheck, modernization, tdd, performance]
generated: { by: looker_healthcheck_agent/gemini-2.5-pro, at: 2026-08-21T15:19:40Z }
verified: { by: human:sampitcher, at: 2026-08-21T15:19:40Z }
sources:
  - id: system-activity-query-metrics
    resource: "system__activity/query_metrics"
    title: "Looker System Activity Query Metrics Explore"
    author: process:looker-system-activity
  - id: bq-jobs-timeline
    resource: "region-us.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT"
    title: "BigQuery Jobs Timeline by Project"
    author: process:bigquery-information-schema
---

### Technical Design Document: `thelook` Model Health Audit

**1. Executive Summary**

This document outlines the findings of a comprehensive health audit of the `thelook` LookML model. The audit covered three pillars: Looker Performance & Lifecycle, BigQuery Engine & Compute, and LookML Modeling & Code Quality. The overall health score is a critical 18%, with significant issues identified across the board. The most severe problems are the lack of partitioning in BigQuery, which causes extremely slow queries, and severe anti-patterns in the LookML model, including cross joins and joins on functions.

**2. Pillar 1: Looker Performance & Query Lifecycle**

*   **LPA-001: Slow Query Outlier (Fail)**: A query on the `order_items` explore took over 52 seconds, with 99% of the time spent in the database.
*   **LPA-002: No Active Dashboards (Pass)**: No dashboards have used this model in the last 90 days.
*   **LPA-003: No Scheduled Plans (Pass)**: No scheduled plans are linked to this model.

**3. Pillar 2: BigQuery Engine & Compute**

*   **BQA-001: Unpartitioned Fact Table (Fail)**: The `order_items` table is not partitioned, leading to full table scans and poor performance.
*   **BQA-002: Slot Contention (Fail)**: The BigQuery project is experiencing severe slot contention, hitting its 2,000-slot limit for extended periods.
*   **BQA-003: Inefficient Queries (Warning)**: While current query costs are low, they will grow exponentially as data volumes increase due to the lack of partitioning.

**4. Pillar 3: LookML Modeling & Code Quality**

*   **LMA-001: Missing Primary Keys (Fail)**: Five views are missing primary keys, which can lead to incorrect metric calculations.
*   **LMA-002: Non-Equi Inequality Join (Fail)**: A non-equi join disables BigQuery's hash join optimization.
*   **LMA-003: SQL Anti-Pattern in Join (Fail)**: A join uses functions in the `sql_on` clause, forcing a full table scan.
*   **LMA-004: Cartesian Cross Join (Fail)**: A cross join will cause a massive increase in row count and likely cause query failure.
*   **LMA-005: Henry Vacuum Skipped (Not Applicable)**: The tool for identifying unused fields failed to run.
*   **LMA-006: Un-hidden Technical Keys (Warning)**: Twenty technical keys are exposed to business users, cluttering the explore interface.

**5. Recommendations**

The highest priority is to address the BigQuery performance issues by partitioning the `order_items` table. The LookML model requires significant refactoring to remove the join anti-patterns. Finally, basic LookML hygiene, such as adding primary keys and hiding technical fields, should be addressed.
