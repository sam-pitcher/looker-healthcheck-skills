---
type: Playbook
title: Master Healthcheck Scoring & Diagnostic Rubric
description: Authoritative Google Cloud PSO multi-pillar scoring methodology, mathematical formulas, and 30-check evaluation standards.
tags: [scoring, methodology, rubric, benchmarks, pso, multi-pillar, evaluation]
status: stable
generated: { by: looker_healthcheck_agent/v0.2, at: "2026-08-28T12:30:00Z" }
verified: { by: "human:sampitcher", at: "2026-08-28T12:30:00Z" }
sources:
  - id: pso-benchmarks
    resource: /skills/looker_performance/references/benchmarks.md
    title: Google Cloud PSO Latency Benchmarks
  - id: transcriber-scoring
    resource: /skills/lookml_quality/playbooks/playbook_transcriber_scoring.md
    title: LookML Transcriber Scoring Rubric
  - id: bq-optimization
    resource: /skills/bigquery_compute/references/warehouse_optimization.md
    title: BigQuery Warehouse Optimization Reference
---

# Master Healthcheck Scoring & Diagnostic Rubric

This playbook establishes the unified scoring architecture across all **3 Healthcheck Pillars** (30 automated checks).

---

## 🏛️ 1. The 3-Tier Scoring Architecture

```
                                  OVERALL HEALTH SCORE (0–100)
                                               │
         ┌─────────────────────────────────────┼─────────────────────────────────────┐
         ▼                                     ▼                                     ▼
   [ PILLAR 1: LOOKER PERF ]         [ PILLAR 2: LOOKML QUALITY ]      [ PILLAR 3: BIGQUERY COMPUTE ]
   10 Automated Checks (P1-01..10)   10 Automated Checks (P2-11..20)   10 Automated Checks (P3-21..30)
```

---

## 🧮 2. Mathematical Scoring Formulation

### A. Micro-Check Point Assignment:
Every check receives one of three standardized outcomes:
* ✅ **`PASSED`**: **100 points** (Meets or exceeds Google Cloud PSO standards).
* ⚠️ **`WARNING`**: **50 points** (Sub-optimal implementation; performance degradation risk).
* ❌ **`CRITICAL / FAIL`**: **0 points** (Active bottleneck; severe compute cost or query timeout).

### B. Pillar Score Calculation (0–100):
$$\text{Pillar Score} = \frac{\sum_{i=1}^{10} \text{Check Score}_i}{10}$$

### C. Overall Instance Health Score (0–100):
$$\text{Overall Health Score} = \frac{\text{Pillar 1 Score} + \text{Pillar 2 Score} + \text{Pillar 3 Score}}{3}$$

---

## 📋 3. Complete Catalog of the 30 Healthcheck Checks

### Pillar 1: Looker Performance & Query Lifecycle (`skills/looker_performance`)
* **`P1-01`**: **Query Lifecycle Latency Breakdown** (JVM overhead <20%, database runtime <2s).
* **`P1-02`**: **Connection Pool & Gateway Throttling** (Queue wait time <100ms).
* **`P1-03`**: **Dashboard Query Density** (<= 25 tiles per dashboard).
* **`P1-04`**: **Auto-Refresh Rate Limits** (Auto-refresh intervals >= 30 minutes).
* **`P1-05`**: **Schedule Time Staggering** (Cron schedules distributed off-peak e.g. `:07`, `:22`).
* **`P1-06`**: **Concurrency Peaks & Queue Depths** (Zero connection pool exhaustion).
* **`P1-07`**: **Stale / Unused Dashboard Inventory** (Identify content unviewed in >90 days).
* **`P1-08`**: **Unfiltered Dashboard Queries** (Enforce required dashboard filters).
* **`P1-09`**: **In-Memory Merged Query Risks** (Eliminate JVM memory merges >10k rows).
* **`P1-10`**: **Datagroup ETL Synchronization** (Replace volatile triggers with ETL watermarks).

### Pillar 2: LookML Modeling & Code Quality (`skills/lookml_quality`)
* **`P2-11`**: **Primary Key Integrity** (`primary_key: yes` declared on 100% of joined views).
* **`P2-12`**: **Explicit Join Cardinality** (`relationship: many_to_one` declared explicitly).
* **`P2-13`**: **Identifier Naming Conventions** (Strict `snake_case` on views, dimensions, measures).
* **`P2-14`**: **Masked Technical Foreign Keys** (Raw IDs & hash keys set to `hidden: yes`).
* **`P2-15`**: **Field Description Coverage** (100% of business dimensions & measures documented).
* **`P2-16`**: **Symmetric Aggregate Fanout Safety** (Zero unkeyed one-to-many join fanouts).
* **`P2-17`**: **Model & View File Line Limits** (Modular files <= 500 lines).
* **`P2-18`**: **Incremental PDT Design** (`increment_key` and `increment_offset` configured).
* **`P2-19`**: **Explore Field Picker Capping** (Explores limited to <= 50 business fields).
* **`P2-20`**: **Table Calculation Pushdown** (Calculations migrated to native SQL measures).

### Pillar 3: BigQuery Engine & Compute Optimization (`skills/bigquery_compute`)
* **`P3-21`**: **Table Partitioning & Clustering** (Fact tables partitioned by date and clustered).
* **`P3-22`**: **BI Engine In-Memory Acceleration** (BI Engine reservations targeting active tables).
* **`P3-23`**: **PDT Build Failure Event Log** (Zero PDT create-fail actions in past 7 days).
* **`P3-24`**: **Warehouse Slot Contention** (Slot utilization within reservation limits <500 slots).
* **`P3-25`**: **Query Memory & Shuffle Spills** (Zero stage memory shuffle spills to disk).
* **`P3-26`**: **Query Cost & Bytes Billed** (Scans constrained to <100 MB per query).
* **`P3-27`**: **Aggregate Awareness Acceleration** (Rollup tables serving summary queries).
* **`P3-28`**: **BigQuery Text Search Indexes** (`SEARCH()` indexes on text search columns).
* **`P3-29`**: **Long Running Query Thread Health** (Zero stuck queries stalling slots >60s).
* **`P3-30`**: **Unpartitioned Full Table Scans** (Semantic layer enforces partition filters).

---

## 🏆 4. Executive Health Grade Thresholds

| Overall Score | Grade | Executive Meaning | Next Step |
| :---: | :---: | :--- | :--- |
| **`90 – 100`** | **A (Exemplary)** | Production-hardened enterprise architecture. | Regular monthly drift monitoring. |
| **`75 – 89`** | **B+ (Good)** | Minor optimization potential; low risk. | Implement minor field cleanups. |
| **`60 – 74`** | **B- (Fair)** | **Optimization Recommended**; moderate compute cost. | Deploy partitioning & primary key fixes. |
| **`< 60`** | **F (Critical)** | **Critical Action Required**; slot starvation risk. | Execute TDD remediation immediately. |
