---
name: looker-bq-healthcheck
description: Master autonomous 3-pillar healthcheck and optimization engine for Looker and BigQuery. Cross-layer triangulation linking BigQuery slot starvation and costs to LookML join flaws and Looker JVM overhead, compiling an executive Technical Design Document (TDD).
---

# 🚀 Looker & BigQuery Healthcheck Master Skill

This skill guides an autonomous agent to execute an end-to-end, 3-pillar diagnostic healthcheck across a Looker instance and its underlying Google Cloud BigQuery data warehouse.

It correlates telemetry across **Looker System Activity**, **LookML AST code semantics**, and **BigQuery INFORMATION_SCHEMA**, diagnosing performance bottlenecks and compiling an authoritative, publication-grade **Technical Design Document (TDD)** with an executive 0–100% health score.

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
* *"Generate an executive Technical Design Document (TDD) or remediation roadmap"*

---

## 🛠️ Tooling & Architecture

The master healthcheck orchestrates three specialized pillar skills:
1. **Looker Performance & Content**: [`skills/looker-performance-auditor/SKILL.md`](../looker-performance-auditor/SKILL.md)
   * System Activity latency phase triage (Looker JVM overhead % vs DB execution vs connection wait).
2. **LookML Modeling & Code Quality**: [`skills/lookml-quality-auditor/SKILL.md`](../lookml-quality-auditor/SKILL.md)
   * 0–4 Transcriber rubric scoring, primary key integrity (eliminating `SUM(DISTINCT)` hashing), explicit relationships.
3. **BigQuery Warehouse & Compute**: [`skills/bq-jobs-diagnostics/SKILL.md`](../bq-jobs-diagnostics/SKILL.md)
   * Slot contention, stage spills to disk, partition & clustering DDL, bytes billed outliers.

### Safe Command Primitives
* **Looker CLI Guardrail**: `bash skills/looker-bq-healthcheck/scripts/safe_looker.sh <command>`
* **BigQuery CLI Wrapper**: `bash skills/bq-jobs-diagnostics/scripts/run_bq_query.sh "<SQL>"`
* **LookML Streaming**: `bash skills/lookml-quality-auditor/scripts/stream_lookml.sh <project_id> <output_dir>`
* **LookML Validation**: `bash skills/lookml-quality-auditor/scripts/validate_lookml.sh <project_id>`

---

## 📋 The 5-Vector Diagnostic Protocol

Execute these 5 vectors across the 3 pillars:

### Vector 1: Latency Phase Decomposition (The 3-Way Triage)
Query `system__activity/query_metrics`:
1. **Looker JVM Overhead %**: `(async_processing - (execute_main_query + acquire_connection)) / async_processing * 100` -> **Target: < 20%**.
2. **Database Execution Time**: `execute_main_query_average` -> **Target: < 5.0s**.
3. **Connection Queue Wait**: `acquire_connection_average` -> **Target: < 0.25s**.
* Deep Dive: [`skills/looker-performance-auditor/references/query_latency_breakdown.md`](../looker-performance-auditor/references/query_latency_breakdown.md)

### Vector 2: SUM(DISTINCT) Fanout & LookML Modeling Integrity
Inspect LookML models and views for the target explore:
* Check every joined view for an unambiguous `primary_key: yes` dimension.
* If missing: Correlate with BigQuery SQL showing CPU-intensive symmetric aggregate subqueries.
* Verify explicit `relationship:` definitions (no implicit defaults).
* Deep Dive: [`skills/lookml-quality-auditor/references/playbook_lookml_quality.md`](../lookml-quality-auditor/references/playbook_lookml_quality.md)
* Rubric: [`skills/lookml-quality-auditor/references/playbook_transcriber_scoring.md`](../lookml-quality-auditor/references/playbook_transcriber_scoring.md)

### Vector 3: BigQuery Slot Saturation & Memory/Disk Spills
Inspect `region-us.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT` during peak usage hours:
* Measure `period_slot_ms` vs assigned reservation capacity.
* Check `period_estimated_runnable_units` (queued queries waiting for slots).
* Check `period_shuffle_ram_usage_ratio` for stage spills to disk.
* Check fact table partitions via `INFORMATION_SCHEMA.TABLE_STORAGE`.
* Deep Dive: [`skills/bq-jobs-diagnostics/references/warehouse_optimization.md`](../bq-jobs-diagnostics/references/warehouse_optimization.md)

### Vector 4: Aggregate Awareness & Rollup Opportunities
* Identify high-frequency explore queries scanning > 10M rows repeatedly.
* Design and prescribe copy-paste LookML `aggregate_table` specifications.
* Deep Dive: [`skills/bq-jobs-diagnostics/references/aggregate_awareness_and_architecture.md`](../bq-jobs-diagnostics/references/aggregate_awareness_and_architecture.md)

### Vector 5: Concurrency Bursts, Auto-Refresh & Schedule Staggering
* Audit dashboards with > 25 tiles.
* Audit auto-refresh intervals (< 30 minutes).
* Audit scheduled plans stacked on the hour (`:00`).
* Deep Dive: [`skills/looker-performance-auditor/references/playbook_content_governance.md`](../looker-performance-auditor/references/playbook_content_governance.md)

---

## 📑 Deliverable: Technical Design Document (TDD)

Synthesize all findings into `TECHNICAL_DESIGN_DOCUMENT.md` following the standard 7-section architecture:
1. **Section 1: Executive Summary & Modernization Objectives** (Scope, baseline score %, target SLAs)
2. **Section 2: Current State Architecture & Forensic Telemetry** (What works well vs latency breakdown)
3. **Section 3: Target State Architecture & Data Flow** (End-to-end Mermaid diagram)
4. **Section 4: Pillar 1 Technical Design (Looker Performance & Content Governance)**
5. **Section 5: Pillar 2 Technical Design (LookML Modeling & Code Quality)** (Exact before/after LookML diffs)
6. **Section 6: Pillar 3 Technical Design (BigQuery Engine & Physical Storage Layout)** (Exact BigQuery DDL)
7. **Section 7: Phased Migration Roadmap, Risk Matrix & Projected ROI**

* Consult TDD Guide: [references/playbook_technical_design_document.md](references/playbook_technical_design_document.md)
* Consult Master Scoring Rubric: [references/scoring_master_rubric.md](references/scoring_master_rubric.md)
* Consult Delivery Guide: [references/playbook_healthcheck_delivery.md](references/playbook_healthcheck_delivery.md)
