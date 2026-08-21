---
type: Technical Design Document
title: "Looker Health Check - Technical Design Document (thelook)"
description: "Comprehensive Looker & BigQuery performance remediation and modernization specification for thelook."
status: stable
tags: [looker, bigquery, healthcheck, modernization, tdd, performance]
generated: { by: looker_healthcheck_agent/gemini-2.5-pro, at: 2026-08-21T14:10:03Z }
verified: { by: human:sampitcher, at: 2026-08-21T14:10:03Z }
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

# Looker & BigQuery Complete Healthcheck Scorecard
- **Audited Scope**: Model: `thelook`
- **Execution Timestamp**: `2026-08-21 14:10:03 UTC`
- **Overall Instance Health Score**: **98.3 / 100**
- **Scorecard Summary**: ✅ **29 Passed** | ⚠️ **1 Warnings** | ❌ **0 Critical** (Total: 30)

---
## 📋 30-Check Master Verification Table

| No. | Pillar | Check / Diagnostic | Status | Score | Findings & Prescribed Remediation | Playbook |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- |
| `P1-01` | Pillar 1: Looker Performance | **Subsystem Status & Endpoint Health** | ✅ PASSED | 100 | Looker cluster responsive. — *Verify load balancer.* | `benchmarks.md` |
| `P1-02` | Pillar 1: Looker Performance | **Database Connections & Pool Limits** | ✅ PASSED | 100 | Audited 95 connection pools. — *Tune max_connections.* | `playbook_looker_performance.md` |
| `P1-03` | Pillar 1: Looker Performance | **Dashboard Query Density (>25 Tiles)** | ✅ PASSED | 100 | Dashboard density within limits. — *Split dashboards.* | `large_dashboards_optimization.md` |
| `P1-04` | Pillar 1: Looker Performance | **Auto-Refresh Rate Limits (<30m)** | ✅ PASSED | 100 | Auto-refresh rates verified. — *Set auto-refresh >=30m.* | `large_dashboards_optimization.md` |
| `P1-05` | Pillar 1: Looker Performance | **Schedule Time Spacing & Distribution** | ✅ PASSED | 100 | Audited 5 scheduled plans. — *Stagger cron schedules.* | `content_delivery_schedules.md` |
| `P1-06` | Pillar 1: Looker Performance | **Concurrency Peaks & Queue Depths** | ✅ PASSED | 100 | Concurrency distribution audited. — *Enable query pooling.* | `playbook_looker_performance.md` |
| `P1-07` | Pillar 1: Looker Performance | **Unused Content & Stale Dashboards** | ✅ PASSED | 100 | Unused content checked. — *Archive unused content.* | `playbook_content_governance.md` |
| `P1-08` | Pillar 1: Looker Performance | **Unfiltered Dashboard Queries** | ✅ PASSED | 100 | Dashboard filters verified. — *Add dashboard filters.* | `playbook_looker_performance.md` |
| `P1-09` | Pillar 1: Looker Performance | **In-Memory Merged Query Risks** | ✅ PASSED | 100 | Zero merged queries detected. — *Migrate to LookML joins.* | `merged_queries_remediation.md` |
| `P1-10` | Pillar 1: Looker Performance | **Legacy Features Deprecation** | ✅ PASSED | 100 | All legacy features deprecated. — *Deprecate legacy flags.* | `benchmarks.md` |
| `P2-11` | Pillar 2: LookML & Modeling | **LookML Syntax & Compiler Validation** | ⚠️ WARNING | 50 | LookML syntax validation complete. — *Fix syntax errors.* | `development_workflows_and_ci.md` |
| `P2-12` | Pillar 2: LookML & Modeling | **Primary Key Integrity & Fanout Safety** | ✅ PASSED | 100 | Primary keys verified. — *Add primary_key: yes.* | `playbook_lookml_quality.md` |
| `P2-13` | Pillar 2: LookML & Modeling | **Join Relationship Declarations** | ✅ PASSED | 100 | Explicit relationship: verified. — *Add explicit relationship: parameter.* | `playbook_lookml_quality.md` |
| `P2-14` | Pillar 2: LookML & Modeling | **Henry Vacuum Dead Field Pruning** | ✅ PASSED | 100 | Henry vacuum analysis complete. — *Prune unused fields.* | `playbook_content_governance.md` |
| `P2-15` | Pillar 2: LookML & Modeling | **Key Field Exposure (hidden: yes)** | ✅ PASSED | 100 | Raw ID keys masked. — *Set hidden: yes on raw ID fields.* | `playbook_lookml_quality.md` |
| `P2-16` | Pillar 2: LookML & Modeling | **Directory Structure & Folder Hygiene** | ✅ PASSED | 100 | Folder structure verified. — *Organize into views/ and models/.* | `playbook_lookml_quality.md` |
| `P2-17` | Pillar 2: LookML & Modeling | **Naming Casing Conventions (snake_case)** | ✅ PASSED | 100 | Snake_case naming verified. — *Enforce lowercase snake_case.* | `playbook_lookml_quality.md` |
| `P2-18` | Pillar 2: LookML & Modeling | **Metadata Descriptions on Fields** | ✅ PASSED | 100 | Field descriptions verified. — *Add description: to key dimensions.* | `playbook_lookml_quality.md` |
| `P2-19` | Pillar 2: LookML & Modeling | **Explore Unused Join Pruning** | ✅ PASSED | 100 | Unused joins audited. — *Remove unqueried joins.* | `playbook_content_governance.md` |
| `P2-20` | Pillar 2: LookML & Modeling | **Table Calculation Heavy Queries** | ✅ PASSED | 100 | Table calculations checked. — *Migrate calculations to LookML measures.* | `playbook_looker_performance.md` |
| `P3-21` | Pillar 3: BigQuery & Compute | **Partition & Cluster Filter Enforcement** | ✅ PASSED | 100 | Audited `the_look_ca.events_table` partition & clustering layout. — *Add always_filter: or conditionally_filter:.* | `connecting-looker-to-bigquery` |
| `P3-22` | Pillar 3: BigQuery & Compute | **BI Engine Acceleration Reservation** | ✅ PASSED | 100 | BI Engine reservation verified. — *Allocate BI Engine memory.* | `connecting-looker-to-bigquery` |
| `P3-23` | Pillar 3: BigQuery & Compute | **PDT Build Failures & Event Log** | ✅ PASSED | 100 | Zero PDT build failures in last 7 days. — *Fix SQL DDL errors in PDTs.* | `playbook_looker_performance.md` |
| `P3-24` | Pillar 3: BigQuery & Compute | **Incremental PDT Increment Key Config** | ✅ PASSED | 100 | Incremental PDTs verified. — *Configure increment_key:.* | `connecting-looker-to-bigquery` |
| `P3-25` | Pillar 3: BigQuery & Compute | **Datagroup ETL Cache Synchronization** | ✅ PASSED | 100 | Datagroup ETL triggers verified. — *Align datagroups with ETL pipeline.* | `playbook_looker_performance.md` |
| `P3-26` | Pillar 3: BigQuery & Compute | **OAuth Connection Caching** | ✅ PASSED | 100 | Connection persistence verified. — *Enable persistent connections.* | `playbook_looker_performance.md` |
| `P3-27` | Pillar 3: BigQuery & Compute | **Aggregate Awareness Rollup Utilization** | ✅ PASSED | 100 | Aggregate Awareness checked. — *Add aggregate_table: definitions.* | `aggregate_awareness_and_architecture.md` |
| `P3-28` | Pillar 3: BigQuery & Compute | **Join SQL Key Syntax (Hash Joins)** | ✅ PASSED | 100 | Join key syntax checked. — *Avoid function calls in sql_on:.* | `connecting-looker-to-bigquery` |
| `P3-29` | Pillar 3: BigQuery & Compute | **Snowflake Schema Denormalization** | ✅ PASSED | 100 | Explore join complexity verified. — *Denormalize dimensional tables.* | `playbook_looker_performance.md` |
| `P3-30` | Pillar 3: BigQuery & Compute | **INFORMATION_SCHEMA Query Cost Audit** | ✅ PASSED | 100 | Query billing costs analyzed. — *Enforce partition pruning.* | `connecting-looker-to-bigquery` |

### 🔗 Provenance & Telemetry Sources
[^system-activity-query-metrics]: Looker System Activity Query Metrics Explore
[^bq-jobs-timeline]: BigQuery Jobs Timeline by Project
