# Looker & BigQuery Healthcheck Skills Suite

> **A suite of platform-agnostic Agent Skills that empowers AI coding agents (Gemini, Antigravity, Claude Code, Cursor, Codex) to audit Looker instance performance, enforce LookML modeling quality, optimize BigQuery warehouse compute, and compile executive Technical Design Documents (TDD).**

Structured strictly following the [Looker Skills Standard](https://github.com/looker-open-source/looker-skills) and `agentskills.io` specification. Grounded in **Google Cloud Professional Services (PSO) performance benchmarks**.

---

## 1. The 3-Pillar Healthcheck Architecture

This suite correlates telemetry across **Looker System Activity**, **LookML code semantics**, and **BigQuery INFORMATION_SCHEMA**:

```text
                           THE 3-PILLAR TRIANGULATION
 ┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
 │ PILLAR 1: LOOKER PERF   │ PILLAR 2: LOOKML QUALITY│ PILLAR 3: BIGQUERY      │
 ├─────────────────────────┼─────────────────────────┼─────────────────────────┤
 │ • Latency Phase Split   │ • Primary Key Integrity │ • Partition & Cluster   │
 │ • Looker JVM vs DB %    │ • Explicit Joins        │ • Slot Contention Curve │
 │ • Dashboard Tile Bloat  │ • Masked Foreign Keys   │ • Memory & Disk Spills  │
 │ • Datagroup ETL Caching │ • Dead Field Pruning    │ • Aggregate Awareness   │
 └─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

| Skill | Domain | Role & Capabilities |
| :--- | :--- | :--- |
| **[`looker-bq-healthcheck`](skills/looker-bq-healthcheck/SKILL.md)** | `looker-operations` | **Master 3-Pillar Orchestrator**: Correlates Looker System Activity, LookML modeling (with `lookml-reviewer`), and BigQuery `INFORMATION_SCHEMA` to produce a 0–100% health score and a 7-section `TECHNICAL_DESIGN_DOCUMENT.md`. |
| **[`looker-performance-auditor`](skills/looker-performance-auditor/SKILL.md)** | `looker-operations` | **Pillar 1 — Looker Performance & Content Governance**: 3-Way Query Latency Triage (Looker JVM overhead % vs. DB runtime vs. Connection queue wait), dashboard tile density (over 25 tiles), auto-refresh, dynamic fields, and schedule staggering. |
| **[`bq-jobs-diagnostics`](skills/bq-jobs-diagnostics/SKILL.md)** | `looker-operations` | **Pillar 3 — BigQuery Warehouse Diagnostics**: `JOBS_TIMELINE` slot saturation & queued units, shuffle RAM spills to disk, `TABLE_STORAGE` partitioning & clustering DDL, and Aggregate Awareness rollups. |

*(Note: Pillar 2 LookML code review and the **0–4 Transcriber Scoring Rubric** are integrated directly into `looker-bq-healthcheck/references/` and upstream `lookml-reviewer`.)*

---

## 2. Customer Permissions Required (Read-Only Least-Privilege)

To run a healthcheck with a customer using `looker-cli` and `bq`:

* **Looker**:
  * `Admin` role, **OR** a custom role on `system__activity` and target models with `see_system_activity`, `develop` (or `see_lookml`), `use_sql_runner`, `see_lookml_dashboards`, `see_user_dashboards`, and `see_schedules`.
  * Looker CLI OAuth enabled (**Admin > Platform > BI Connectors > Looker CLI = ON**) or API3 credentials.
* **BigQuery (Project-level IAM)**:
  * `roles/bigquery.resourceViewer` *(Required for `bigquery.jobs.listAll` to query `INFORMATION_SCHEMA.JOBS_BY_PROJECT` and `JOBS_TIMELINE_BY_PROJECT` — `bigquery.dataEditor` alone only sees your own jobs)*
  * `roles/bigquery.jobUser` *(Required to execute `bq query` diagnostic queries)*
  * `roles/bigquery.metadataViewer` *(Required to inspect `INFORMATION_SCHEMA.TABLE_STORAGE` and `COLUMNS` for partition/cluster checks)*

---

## 3. Repository Structure

```text
looker-healthcheck/
├── README.md
└── skills/
    ├── looker-bq-healthcheck/
    │   ├── SKILL.md
    │   └── references/
    ├── looker-performance-auditor/
    │   ├── SKILL.md
    │   └── references/
    └── bq-jobs-diagnostics/
        ├── SKILL.md
        └── references/
```

---

## 4. Example Prompts

* **Full 3-Pillar Healthcheck**:
  > *"Run a full 3-pillar healthcheck across our Looker instance and BigQuery warehouse. Triangulate slow queries across System Activity, LookML joins, and BigQuery slot usage, calculate the composite health score, and generate a TECHNICAL_DESIGN_DOCUMENT.md."*
* **Looker Performance & Governance (Pillar 1)**:
  > *"Our marketing dashboard (id: 42) is taking 45 seconds to load. Audit its query lifecycle latency to see whether the bottleneck is in the Looker JVM, database execution, or connection queueing."*
* **BigQuery Compute & Storage (Pillar 3)**:
  > *"Inspect `INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT` over the last 24 hours to see if our Looker service account hit slot saturation or had queued queries."*

---

## License
Apache-2.0
