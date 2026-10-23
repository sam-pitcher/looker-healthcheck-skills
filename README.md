# 🚀 Looker & BigQuery Healthcheck: Multi-Agent Skills Suite

> **An enterprise suite of platform-agnostic Agent Skills that empowers any AI agent harness (Gemini Jetski, Claude Code, Cursor, Codex, LangGraph) to audit Looker instance performance, enforce LookML modeling quality, optimize BigQuery warehouse compute, and compile publication-grade Technical Design Documents (TDD).**

Structured strictly following the [Looker Skills Standard](https://github.com/looker-open-source/looker-skills) and Google Agent Standards. Grounded in **Google Cloud Professional Services (PSO) performance benchmarks**.

---

## 📑 Table of Contents
1. [What It Does & The 3 Healthcheck Pillars](#1-what-it-does--the-3-healthcheck-pillars)
2. [The 30-Check Master Healthcheck Playbook: No Rock Unturned](#2-the-30-check-master-healthcheck-playbook-no-rock-unturned)
3. [The Skills Architecture](#3-the-skills-architecture)
4. [Example Prompts for AI Agents](#4-example-prompts-for-ai-agents)
5. [Tooling & Safe Primitives](#5-tooling--safe-primitives)
6. [How an AI Agent Harness Executes a Healthcheck](#6-how-an-ai-agent-harness-executes-a-healthcheck)
7. [Conformance Testing & Evaluation](#7-conformance-testing--evaluation)

---

## 1. What It Does & The 3 Healthcheck Pillars

This repository replaces opaque manual audits and fragmented scripts with an autonomous, cross-layer diagnostic engine. It correlates telemetry across **Looker System Activity**, **LookML AST code semantics**, and **BigQuery INFORMATION_SCHEMA**:

```
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

### Comprehensive Healthcheck Coverage

| Pillar | Skill Package | Key Healthcheck Dimensions Audited |
| :--- | :--- | :--- |
| **Pillar 1: Looker Performance** | [`skills/looker-performance-auditor`](skills/looker-performance-auditor/SKILL.md) | • **3-Way Latency Triage**: Looker JVM Init/Compile % vs. DB execution average vs. Connection queue wait.<br>• **Dashboard Content Hygiene**: Tile density (>25 tiles), auto-refresh loops, merged query misuse.<br>• **Caching & Delivery**: Datagroup ETL alignment, PDT build triggers, schedule staggering. |
| **Pillar 2: LookML Quality** | [`skills/lookml-quality-auditor`](skills/lookml-quality-auditor/SKILL.md) | • **Primary Key Integrity**: Mandatory `primary_key: yes` on joined views to eliminate `SUM(DISTINCT ...)` symmetric aggregate hashing.<br>• **Explicit Joins**: Unambiguous `relationship: many_to_one/one_to_many`, clean column-to-column equality joins in `sql_on`.<br>• **Field Privacy & Governance**: Mask technical keys (`hidden: yes`), prune dead fields with Henry vacuum, conversational descriptions for Gemini. |
| **Pillar 3: BigQuery Engine** | [`skills/bq-jobs-diagnostics`](skills/bq-jobs-diagnostics/SKILL.md) | • **Slot Contention Curves**: Peak slot saturation (>200 slots), queued query units in `JOBS_TIMELINE`.<br>• **Table Physical Layout**: Partitioning (`PARTITION BY DATE(...)`) and clustering (`CLUSTER BY ...`) DDL to minimize scanned bytes.<br>• **Execution Diagnostics**: Memory shuffle spills and disk spill forensics on slow queries.<br>• **Acceleration**: Aggregate Awareness LookML rollups and BI Engine readiness. |

---

## 2. The 30-Check Master Healthcheck Playbook: No Rock Unturned

The healthcheck leaves no rock unturned, executing **30 standardized automated checks** (10 per pillar) based on Google Cloud PSO benchmarks:

### 🏛️ Pillar 1: Looker Performance & Content Governance (Checks P1-01 to P1-10)
- **`P1-01` Query Latency Phase Breakdown**: Looker JVM overhead % vs DB runtime vs connection wait.
- **`P1-02` Connection Pool Wait Time**: Queue starvation (>100ms indicates connection pool exhaustion).
- **`P1-03` Dashboard Tile Density**: Flags dashboards with >25 tiles causing concurrent browser/JVM memory stalls.
- **`P1-04` Auto-Refresh Rate Limits**: Catches aggressive auto-refresh (<15–30 min) hammering the warehouse.
- **`P1-05` Schedule Staggering**: Audits top-of-hour (`:00`) cron stampedes across scheduled delivery plans.
- **`P1-06` Concurrency Peaks & Queue Depths**: Server-wide query thread exhaustion.
- **`P1-07` Stale Content Inventory**: Identifies unviewed dashboards (>90 days) cluttering the system.
- **`P1-08` Unfiltered Dashboard Queries**: Enforces required filters (`always_filter`) on fact explores.
- **`P1-09` In-Memory Merged Queries**: Catches multi-explore merged queries forcing heavy client-side joins.
- **`P1-10` Datagroup ETL Synchronization**: Verifies explores use SQL watermarks instead of arbitrary static intervals.

### 🧬 Pillar 2: LookML Modeling Quality & Architecture (Checks P2-11 to P2-20)
- **`P2-11` LookML Compiler & Syntax Health**: 0 compiler warnings or broken explore definitions.
- **`P2-12` Primary Key Integrity**: Verifies 100% of joined views declare `primary_key: yes` to prevent `SUM(DISTINCT ...)` subqueries.
- **`P2-13` Explicit Join Cardinality**: Mandates explicit `relationship: many_to_one/one_to_many/one_to_one`.
- **`P2-14` Dead Field Vacuuming (Henry)**: Audits unused dimensions and measures bloating models.
- **`P2-15` Masked Technical Foreign Keys**: Enforces `hidden: yes` on raw surrogate keys and hashes.
- **`P2-16` Modular Hierarchy**: Verifies separation into dedicated `/explores`, `/views`, and `/models`.
- **`P2-17` Clean snake_case Identifiers**: Enforces consistent lowercase snake_case naming.
- **`P2-18` User-Facing Field Descriptions**: 100% description coverage for business users & Conversational AI.
- **`P2-19` Explore Field Picker Capping**: Caps explore field picker to 40–50 fields via `fields: []`.
- **`P2-20` Table Calculation Pushdown**: Flags heavy client-side calculations that should be LookML measures.

### ⚡ Pillar 3: BigQuery Engine & Compute Optimization (Checks P3-21 to P3-30)
- **`P3-21` Table Partitioning & Clustering**: Enforces date partitioning and clustering on fact tables >10M rows.
- **`P3-22` BI Engine Acceleration**: Checks BI Engine memory reservation and query acceleration rates.
- **`P3-23` PDT Build Failures & Event Log**: Inspects scratch schema for cascading PDT failures.
- **`P3-24` Warehouse Slot Contention**: Analyzes `period_slot_ms` and `period_estimated_runnable_units` (queued queries).
- **`P3-25` Query Memory & Shuffle Spills**: Detects queries spilling memory to disk in BigQuery shuffle stages.
- **`P3-26` Query Cost & Bytes Billed Outliers**: Identifies runaway queries scanning multi-gigabytes per run.
- **`P3-27` Aggregate Awareness Acceleration**: Identifies repetitive summary scans and prescribes `aggregate_table` rollups.
- **`P3-28` Search Indexes**: Replaces expensive regex filters with BigQuery `SEARCH()` indexes.
- **`P3-29` Long Running Query Thread Health**: Detects zombie queries running for >60s.
- **`P3-30` Unpartitioned Full Table Scans**: Guarantees explores enforce partition filters at the semantic layer.

---

## 3. The Skills Architecture

```
looker-healthcheck/
├── manifest.yaml                         # Master Catalog Manifest
├── README.md                             # Architectural & user guide
│
├── skills/
│   ├── looker-bq-healthcheck/            # Master 3-pillar healthcheck orchestrator
│   │   ├── SKILL.md                      # 5-vector execution workflow & subagent orchestration
│   │   ├── scripts/                      # Safe CLI execution tools
│   │   │   └── safe_looker.sh            # Read-only guardrail (blocks rm, delete, drop, truncate)
│   │   └── references/                   # Master scoring rubric, TDD template, delivery guides
│   │
│   ├── lookml-quality-auditor/           # Pillar 2: LookML modeling & Transcriber 0-4 scoring
│   │   ├── SKILL.md                      # 30-check audit playbook & scoring methodology
│   │   ├── scripts/                      # Deterministic AST scanner & streaming tools
│   │   │   ├── audit_lookml_rules.py     # Automated 0-4 score calculator across 4 focus dimensions
│   │   │   ├── stream_lookml.sh          # Live LookML streaming API without git cloning
│   │   │   └── validate_lookml.sh        # Project compilation validator
│   │   └── references/                   # Scoring rubrics, Spectacles CI, conversational AI rules
│   │
│   ├── looker-performance-auditor/       # Pillar 1: Query lifecycle & content governance
│   │   ├── SKILL.md                      # Latency decomposition & dashboard tile hygiene
│   │   └── references/                   # Latency formulas, query outlier guides, schedule staggering
│   │
│   ├── bq-jobs-diagnostics/              # Pillar 3: BigQuery compute diagnostics
│   │   ├── SKILL.md                      # Slot curves, memory/disk spills, partition/cluster auditing
│   │   ├── scripts/                      # BigQuery CLI wrappers
│   │   │   └── run_bq_query.sh           # PrettyJSON bq query runner
│   │   └── references/                   # Slot saturation formulas, partition DDL, BI Engine guides
│   │
│   └── vendor/looker-skills/             # Upstream official Looker developer skills
│
└── evals/                                # Continuous Conformance & Benchmark Suite
    ├── run_evals.py                      # Unified test runner
    ├── test_transcriber_scoring.py       # Layer 1: Transcriber 0-4 rubric benchmarks
    ├── test_skills_conformance.py        # Layer 2: Agent Skills standard & manifest verification
    └── fixtures/                         # Real LookML project fixtures (anti-pattern vs exceptional)
```

---

## 4. Example Prompts for AI Agents

You can trigger the entire suite or scoped sub-audits using natural language prompts in your agent harness:

### 🚀 Full 3-Pillar Healthcheck Prompts
> *"Run a full 3-pillar healthcheck across our Looker instance and BigQuery warehouse. Triangulate slow queries across System Activity, LookML joins, and BigQuery slot usage, calculate the composite health score, and generate a publication-grade TECHNICAL_DESIGN_DOCUMENT.md."*

> *"Perform an end-to-end Looker and BigQuery performance audit on project `thelook_ecommerce`. Check query latency breakdowns, LookML primary keys, and BigQuery slot contention, then produce an executive remediation roadmap."*

### 🔍 Pillar 1 (Looker Performance & Content) Prompts
> *"Our marketing dashboard (id: 42) is taking 45 seconds to load. Audit its query lifecycle latency to see whether the bottleneck is in the Looker JVM, database execution, or connection queueing."*

> *"Audit our Looker instance for top-of-hour schedule stampedes, aggressive dashboard auto-refreshes (<15 min), and dashboards with over 25 tiles."*

### 🧬 Pillar 2 (LookML Modeling & Code Quality) Prompts
> *"Audit this LookML project against the 0–4 Transcriber rubric. Check for missing primary keys on joined views, explicit relationships, unmasked surrogate keys, and field descriptions for Gemini readiness."*

> *"Review our `orders.explore.lkml` and related views. Are any joins causing Looker to generate CPU-intensive symmetric aggregates (`SUM(DISTINCT ...)`), and how do we refactor them?"*

> *"Scan our LookML repo using the audit_lookml_rules.py script and give me a JSON report of all compliance violations across our views and explores."*

### ⚡ Pillar 3 (BigQuery Warehouse & Compute) Prompts
> *"Inspect `INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT` over the last 24 hours to see if our Looker service account hit slot saturation or had queued queries."*

> *"Identify fact tables in our analytics dataset with more than 10 million rows that lack date partitioning or clustering, and generate the DDL remediation scripts to fix them."*

> *"Find our top 10 most expensive queries by bytes billed from Looker and check if any of them experienced RAM shuffle spills to disk."*

---

## 5. Tooling & Safe Primitives

### 1. Looker CLI (`looker-cli`)
* **Authenticate**:
  ```bash
  looker-cli session login --profile=<profile>
  ```
* **Read-Only Guardrail**:
  ```bash
  bash skills/looker-bq-healthcheck/scripts/safe_looker.sh query runquery '<JSON>'
  ```

### 2. BigQuery CLI (`bq`)
* **Safe BQ Query Execution**:
  ```bash
  bash skills/bq-jobs-diagnostics/scripts/run_bq_query.sh "SELECT * FROM \`region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT\` LIMIT 10"
  ```

### 3. LookML Quality Scanner
* **Automated 0–4 Transcriber Score Calculation**:
  ```bash
  python3 skills/lookml-quality-auditor/scripts/audit_lookml_rules.py /path/to/lookml/project
  ```

---

## 6. How an AI Agent Harness Executes a Healthcheck

1. **Activation**: Harness loads `skills/looker-bq-healthcheck/SKILL.md`.
2. **Delegation / Execution**:
   * Evaluates Pillar 1 with `looker-performance-auditor`.
   * Evaluates Pillar 2 with `lookml-quality-auditor` and `audit_lookml_rules.py`.
   * Evaluates Pillar 3 with `bq-jobs-diagnostics` and `run_bq_query.sh`.
3. **Triangulation**: The agent synthesizes cross-layer root causes (e.g. LookML missing primary key $\rightarrow$ BigQuery slot spike $\rightarrow$ dashboard latency).
4. **Deliverable Synthesis**: Emits an executive `TECHNICAL_DESIGN_DOCUMENT.md` and `healthcheck_report.json`.

---

## 7. Conformance Testing & Evaluation

The repository includes a fast test harness validating rubric fidelity and skill standard compliance:

```bash
python3 evals/run_evals.py
```

### Evaluation Matrix (100% Passing in <20ms)
* **Layer 1: Transcriber 0–4 Scoring Rubric Benchmarks** (`evals/test_transcriber_scoring.py`)
  * Validates anti-pattern fixtures score $\le 1.5$ (Unsatisfactory).
  * Validates exceptional enterprise fixtures score $\ge 3.5$ (Exceptional).
* **Layer 2: Agent Skills Standard & Manifest Conformance** (`evals/test_skills_conformance.py`)
  * Validates `manifest.yaml` syntax, skills, and subagent mappings.
  * Enforces YAML frontmatter (`name`, `description`) and markdown structure across all `SKILL.md` files.
  * Validates shell script and python script executable shebangs.
  * Enforces presence of deep-dive playbooks and references in every skill package.

---

## 📄 License
Apache-2.0
