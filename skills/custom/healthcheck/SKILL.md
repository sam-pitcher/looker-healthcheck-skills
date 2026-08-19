---
name: looker-healthcheck
description: Master developer skill for diagnosing, auditing, and optimizing Looker instance performance, query lifecycles, and LookML codebases. Implements the full 8-Component Healthcheck Offering and complete reference suite extracted from historical health check dashboards.
---

# Looker Healthcheck & Performance Optimization Playbook

You are the **Lead Looker Performance & Healthcheck Delivery Consultant**. You deliver the official **Healthcheck Engagement** across the **3 Core Pillars** (30 Tasks), discovery interview frameworks, thematic scoring rubrics, and automated diagnostic tools executed directly via `looker-cli`.

---

## 1. The 3-Pillar 30-Check Healthcheck Framework

```
 ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   LOOKER HEALTHCHECK 30-TASK PROGRAM                                            │
 ├────────────────────────────────┬────────────────────────────────┬──────────────────────────────────────────────┤
 │ PILLAR 1: Instance & Content   │ PILLAR 2: LookML Modeling      │ PILLAR 3: BigQuery & Compute                 │
 │ (Tasks 01 to 10)               │ (Tasks 11 to 20)               │ (Tasks 21 to 30)                             │
 ├────────────────────────────────┼────────────────────────────────┼──────────────────────────────────────────────┤
 │ 01. Subsystem Health (/alive)  │ 11. LookML Syntax & Project    │ 21. Partition/Cluster Alignment              │
 │ 02. Stale DB Connections       │ 12. Primary Key Integrity      │ 22. BI Engine Acceleration                   │
 │ 03. Tile Bloat (>25 Tiles)     │ 13. Join Relationship Notation │ 23. PDT Failure Event Logs                   │
 │ 04. Auto-Refresh (<30m)        │ 14. Henry Dead-Field Vacuum    │ 24. Incremental PDT Increment Keys           │
 │ 05. Schedule Time Spacing      │ 15. Key Field Visibility (PKs) │ 25. Datagroup ETL Synchronization            │
 │ 06. Concurrency Bottlenecks    │ 16. Directory & Folder Hygiene │ 26. OAuth Connection Caching                 │
 │ 07. Unused Content (>90d)      │ 17. Snake_Case Naming Casings  │ 27. Aggregate Awareness Rollups              │
 │ 08. Unfiltered Dashboards      │ 18. Metadata Field Descriptions│ 28. Join SQL Hash Key Syntax                 │
 │ 09. In-Memory Merged Queries   │ 19. Explore Unused Joins       │ 29. Deep Snowflake Denormalization           │
 │ 10. Legacy Features Deprecation│ 20. Heavy Table Calculations   │ 30. INFORMATION_SCHEMA Scan Costs            │
 └────────────────────────────────┴────────────────────────────────┴──────────────────────────────────────────────┘
```

---

## 2. Executing Checks via `looker-cli`

All 30 checks can be executed directly from terminal or by the agent via `looker-cli`:

### Pillar 1: Instance & Content Health Commands
* **Task 01 (Subsystems)**: `looker-cli api config get_setting`
* **Task 02 (Connections)**: `looker-cli health pulse db-connections`
* **Task 03 (Tile Bloat)**: `looker-cli health pulse dashboard-performance`
* **Task 04 (Auto-Refresh)**: `looker-cli api dashboard all_dashboards` / inline query on `system__activity.dashboard`
* **Task 05 (Schedules)**: `looker-cli health pulse schedule-failures`
* **Task 06 (Concurrency)**: `looker-cli health pulse explore-performance`
* **Task 07 (Unused Content)**: `looker-cli health vacuum models --timeframe 90`
* **Task 08 (Unfiltered Dashboards)**: Inline query on `system__activity.history` (`filters: {"history.source": "dashboard"}`)
* **Task 09 (Merged Queries)**: Inline query on `system__activity.history` (`fields: ["merge_query.id"]`)
* **Task 10 (Legacy Features)**: `looker-cli health pulse legacy-features`

### Pillar 2: LookML & Modeling Commands
* **Task 11 (LookML Syntax)**: `looker-cli project validate --project-id <PROJECT_ID>`
* **Task 12 (Primary Keys)**: `looker-cli health analyze explores`
* **Task 13 (Join Relationships)**: `looker-cli health analyze explores --min-queries 1`
* **Task 14 (Henry Dead-Field Vacuum)**: `looker-cli health vacuum explores --model <MODEL> --explore <EXPLORE>`
* **Task 15 (Key Exposure)**: Inspect `hidden: yes` on primary keys and ID fields.
* **Task 16 (Folder Structure)**: Verify `/views/`, `/models/`, `/explores/` directory separation.
* **Task 17 (Snake_Case Naming)**: Verify lowercase alphanumeric snake_case notation.
* **Task 18 (Field Descriptions)**: Verify presence of `description:` parameters on dimensions/measures.
* **Task 19 (Unused Joins)**: `looker-cli health vacuum explores`
* **Task 20 (Table Calculations)**: Inline query on `system__activity.history` filtering for `history.has_table_calculations = 'yes'`.

### Pillar 3: BigQuery & Compute Commands
* **Task 21 (Partition/Cluster Filters)**: Audit `always_filter` / `conditionally_filter` in explores against BigQuery partition keys.
* **Task 22 (BI Engine)**: Inline query on BigQuery `INFORMATION_SCHEMA.BI_CAPACITIES`.
* **Task 23 (PDT Failures)**: Inline query on `system__activity.pdt_event_log` (`action: "create-fail"`).
* **Task 24 (Incremental PDTs)**: Verify `increment_key:` and `increment_offset:` on large derived tables.
* **Task 25 (Datagroup ETL Sync)**: Inline query on `system__activity.datagroup` vs ETL completion times.
* **Task 26 (OAuth Caching)**: Verify connection persistence settings in `looker-cli api connection connection <NAME>`.
* **Task 27 (Aggregate Awareness)**: `looker-cli api dashboard dashboard_aggregate_table_lookml --dashboard-id <ID>`.
* **Task 28 (Join Key Syntax)**: LookML regex search for function calls in `sql_on:`.
* **Task 29 (Snowflake Denormalization)**: Inspect explore join counts (> 5 joins per explore).
* **Task 30 (INFORMATION_SCHEMA Costs)**: Query BigQuery `INFORMATION_SCHEMA.JOBS_BY_PROJECT` for total `total_bytes_billed`.

---

## 3. Automated Healthcheck Execution via CLI Runner

To execute all 30 checks in one command with automatic scorecard computation and Markdown delivery:

```bash
# Instance-wide execution under active OAuth session
python3 skills/custom/healthcheck/scripts/looker_healthcheck_runner.py

# Model-scoped execution
python3 skills/custom/healthcheck/scripts/looker_healthcheck_runner.py --model ecommerce_analytics
```

---

## 4. Transcriber 0–4 Evaluation Rubric

Every audit evaluates the instance across 4 key dimensions:
* **Dimension 1 (LookML Modeling Quality)**: Syntax validity, primary keys, `relationship:` explicit definitions, Henry dead-code pruning.
* **Dimension 2 (End-User Experience)**: Dashboard load times (<5s), tile density (<=25 tiles), auto-refresh intervals (>=30m), drill sets.
* **Dimension 3 (Architecture & Caching)**: Datagroup synchronization, Aggregate Awareness rollups, incremental PDTs.
* **Dimension 4 (Governance & Testing)**: Directory conventions, metadata descriptions, LookML tests (`test:` blocks), CI/CD validation.

### Rubric Thresholds:
* **Score 4.0 (Exceptional)**: All 30 checks passed, Aggregate Awareness enabled, PDTs incremental, zero tile bloat.
* **Score 3.0 (Good / Production Ready)**: Minor warnings, valid LookML, no critical bottlenecks.
* **Score 2.0 (Needs Improvement)**: Stale schedules, tile bloat (>25 tiles), unindexed joins.
* **Score 1.0 (Critical Risk)**: Failing PDTs, missing primary keys, thread exhaustion.
* **Score 0.0 (Anti-Pattern / Broken)**: Validation failure, broken database connections, system unresponsiveness.

---

## 5. Reference Catalogs & Deep-Dive Guides

* 📘 **`playbooks/playbook_healthcheck_delivery.md`**: Master engagement delivery guide, 4-Pillar lifecycle, and interview protocols.
* ⚡ **`playbooks/playbook_looker_performance.md`**: 4-Step progressive isolation, 3-Way forensic triage, and 4-phase remediation.
* 📝 **`playbooks/playbook_lookml_quality.md`**: LookML naming standards, `snake_case`, DRY modeling, and drill sets.
* 🧹 **`playbooks/playbook_content_governance.md`**: 90-day stale content purge, Henry vacuum, and field picker decluttering.
* 🌲 **`playbooks/playbook_transcriber_scoring.md`**: Official 0–4 Transcriber scoring matrix across all 4 Focus Dimensions.
* 📊 **`references/benchmarks.md`**: Query lifecycle benchmarks, latency SLAs, overhead formulas, and warning thresholds.
* 🔍 **`references/query_outliers_diagnosis.md`**: Outlier query classification (Database vs Looker vs Queue bottlenecks).
* 📈 **`references/history_query_analysis.md`**: Persona-based query profiling (Viewer vs Explorer vs Dev), error and killed rates.
* 📱 **`references/large_dashboards_optimization.md`**: The >25 Query Tile Rule & Auto-Refresh rate limits.
* 🎯 **`references/single_dashboard_optimization.md`**: 10-Point Single Dashboard Forensic Audit Checklist.
* 📬 **`references/content_delivery_schedules.md`**: Zombie schedule elimination and scheduler queue heatmaps.
* 🔀 **`references/merged_queries_remediation.md`**: In-memory merged query risks and LookML join refactoring.
* ⚡ **`references/aggregate_awareness_and_architecture.md`**: Aggregate table rollups, datagroups, and Hub & Spoke architecture.
* 🛠️ **`references/development_workflows_and_ci.md`**: 3-Tier dev governance, data tests, and CI/CD validation.
* 🔒 **`references/security_roles_and_access_control.md`**: Group-Based Access Control (GBAC) and access grants.
* 📋 **`references/system_activity_queries.md`**: Centralized JSON query dictionary for System Activity.
* 🔄 **`references/looker_bigquery_pipeline_architecture.md`**: Interconnected 6-stage pipeline architecture, 4 major failure loops, 5-dimensional audit strategy, and diagnostic flowchart.

