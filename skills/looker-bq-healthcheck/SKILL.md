---
name: looker-bq-healthcheck
description: Master autonomous 3-pillar healthcheck and optimization engine for Looker and BigQuery. Cross-layer triangulation linking BigQuery slot starvation and costs to LookML join flaws and Looker JVM overhead, compiling an OKF v0.2 Technical Design Document (TDD).
---

# 🚀 Looker & BigQuery Healthcheck Master Skill

This skill guides an autonomous agent to execute an end-to-end, 3-pillar diagnostic healthcheck across a Looker instance and its underlying Google Cloud BigQuery data warehouse.

It correlates telemetry across **Looker System Activity**, **LookML AST code semantics**, and **BigQuery INFORMATION_SCHEMA**, diagnosing performance bottlenecks and compiling an authoritative, publication-grade **Technical Design Document (TDD)** adhering to the **Open Knowledge Format (OKF v0.2)**.

```
                           THE 3-PILLAR TRIANGULATION
 ┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
 │ PILLAR 1: LOOKER PERF   │ PILLAR 2: LOOKML QUALITY│ PILLAR 3: BIGQUERY      │
 ├─────────────────────────┼─────────────────────────┼─────────────────────────┤
 │ • Query Phase Breakdown │ • Primary Key Integrity │ • Partition & Cluster   │
 │ • JVM vs DB Overhead    │ • Explicit Joins        │ • Slot Contention Curve │
 │ • Dashboard Tile Bloat  │ • Masked Foreign Keys   │ • Memory & Disk Spills  │
 │ • Datagroup ETL Caching │ • Snake_case & Gemini   │ • Aggregate Awareness   │
 └─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

---

## 🧭 When to Use This Skill

Activate this skill when the user asks to:
* *"Run a healthcheck on our Looker instance / model"*
* *"Audit slow dashboards or slow queries (>10s–30s)"*
* *"Optimize LookML modeling, symmetric aggregates, or missing primary keys"*
* *"Check BigQuery slot starvation, unpartitioned table scans, or query costs"*
* *"Generate an OKF Technical Design Document (TDD) or remediation roadmap"*

---

## 🛠️ Tooling & Access Strategy

The agent executes investigations through standard CLI primitives:
1. **Looker CLI (`looker-cli`)**:
   - Query System Activity: `looker-cli query runquery '<JSON>'`
   - Stream LookML: `looker-cli project file ls <project>` / `looker-cli project file cat <project> <file>`
   - Parallel streaming helper: `bash skills/looker-bq-healthcheck/scripts/stream_lookml.sh <project_id> <output_dir>`
   - Compiler validation helper: `bash skills/looker-bq-healthcheck/scripts/validate_lookml.sh <project_id>`
   - Safe CLI wrapper: `bash skills/looker-bq-healthcheck/scripts/safe_looker.sh <command>`
2. **BigQuery CLI (`bq`)**:
   - Query `INFORMATION_SCHEMA`: `bq query --use_legacy_sql=false "<SQL>"`
   - Safe BQ helper: `bash skills/bq-jobs-diagnostics/scripts/run_bq_query.sh "<SQL>"`
3. **Upstream Vendor Skills & Sub-Skills**:
   - **Looker CLI & Auth**: Delegate CLI discovery and authentication to `using-looker-cli` and `authenticating-looker-cli` from [looker-skills](https://github.com/looker-open-source/looker-skills).
   - **LookML Code Review**: Delegate AST parsing, field standards, primary keys, and join hygiene to `lookml-reviewer` from [looker-skills](https://github.com/looker-open-source/looker-skills).
   - **Performance Optimization**: Delegate explore/dashboard optimizations to `looker-performance-optimizer`.
   - **BigQuery Diagnostics**: [`skills/bq-jobs-diagnostics/SKILL.md`](../bq-jobs-diagnostics/SKILL.md) (owns BigQuery compute auditing)
   - **Normative Knowledge**: [`bundle/lookml_quality/`](../../bundle/lookml_quality/) (30-check scoring rubric and remediation playbooks)

---

## 📋 The 5-Vector Diagnostic Execution Protocol

Execute these 5 vectors in a single context using progressive disclosure:

### Vector 1: Latency Phase Decomposition (The 3-Way Triage)
Query `system__activity/query_metrics` to break total latency into 3 components:
1. **Looker JVM Overhead %**: `(async_processing - (execute_main_query + acquire_connection)) / async_processing * 100` -> **Target: < 20%**.
   * If high: Flag table calculation bloat, massive dimension lists, or complex Liquid rendering.
2. **Database Execution Time**: `execute_main_query_average` -> **Target: < 5.0s**.
   * If high: Proceed to Vector 2 and Vector 3.
3. **Connection Queue Wait**: `acquire_connection_average` -> **Target: < 0.25s**.
   * If high: Check connection pool limits and dashboard tile density (>25 tiles).
* Consult concept: [`bundle/looker_performance/playbooks/playbook_looker_performance.md`](../../bundle/looker_performance/playbooks/playbook_looker_performance.md)
* Consult computation: [`bundle/looker_performance/computations/query_latency_breakdown.md`](../../bundle/looker_performance/computations/query_latency_breakdown.md)

### Vector 2: SUM(DISTINCT) Fanout & LookML Modeling Integrity
Inspect LookML models and views for the target explore:
* Check every joined view for an unambiguous `primary_key: yes` dimension.
* If missing: Correlate with BigQuery SQL to show the heavy `SUM(DISTINCT ...)` symmetric aggregate subquery overhead.
* Verify explicit `relationship:` definitions (no implicit defaults).
* Consult concept: [`bundle/lookml_quality/references/symmetric_aggregates_deep_dive.md`](../../bundle/lookml_quality/references/symmetric_aggregates_deep_dive.md)

### Vector 3: BigQuery Slot Saturation & Memory/Disk Spills
Inspect `region-us.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT` during peak usage hours:
* Measure `period_slot_ms` vs assigned reservation capacity.
* Check `period_estimated_runnable_units` (queued queries waiting for slots).
* Check `period_shuffle_ram_usage_ratio` for stage spills to disk.
* Check fact table partitions via `INFORMATION_SCHEMA.TABLE_STORAGE`.
* Consult concept: [`bundle/bigquery_compute/references/warehouse_optimization.md`](../../bundle/bigquery_compute/references/warehouse_optimization.md)

### Vector 4: Aggregate Awareness & Rollup Opportunities
* Identify high-frequency explore queries scanning > 10M rows repeatedly.
* Design and prescribe copy-paste LookML `aggregate_table` specifications.
* Consult concept: [`bundle/bigquery_compute/references/aggregate_awareness_and_architecture.md`](../../bundle/bigquery_compute/references/aggregate_awareness_and_architecture.md)

### Vector 5: Concurrency Bursts, Auto-Refresh & Schedule Staggering
* Audit dashboards with > 25 tiles.
* Audit auto-refresh intervals (< 30 minutes).
* Audit scheduled plans stacked on the hour (`:00`).
* Consult concept: [`bundle/looker_performance/playbooks/playbook_content_governance.md`](../../bundle/looker_performance/playbooks/playbook_content_governance.md)

---

## 📑 Deliverable: OKF v0.2 Technical Design Document (TDD)

Synthesize all findings into `TECHNICAL_DESIGN_DOCUMENT.md` following the authoritative 7-section OKF structure:
1. **Section 1: Executive Summary & Modernization Objectives** (Scope, baseline score %, target SLAs)
2. **Section 2: Current State Architecture & Forensic Telemetry** (What works well vs latency breakdown)
3. **Section 3: Target State Architecture & Data Flow** (End-to-end Mermaid diagram)
4. **Section 4: Pillar 1 Technical Design (Looker Performance & Content Governance)**
5. **Section 5: Pillar 2 Technical Design (LookML Modeling & Code Quality)** (Exact before/after LookML diffs)
6. **Section 6: Pillar 3 Technical Design (BigQuery Engine & Physical Storage Layout)** (Exact BigQuery DDL)
7. **Section 7: Phased Migration Roadmap, Risk Matrix & Projected ROI**

Also emit machine-readable findings to `healthcheck_report.json`.

* Consult TDD playbook: [`bundle/shared/playbooks/playbook_technical_design_document.md`](../../bundle/shared/playbooks/playbook_technical_design_document.md)
* Consult master scoring rubric: [`bundle/shared/playbooks/scoring_master_rubric.md`](../../bundle/shared/playbooks/scoring_master_rubric.md)
