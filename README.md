# 🚀 Looker & BigQuery Healthcheck: Skills & OKF Catalog

> **A repository of platform-agnostic Agent Skills and Open Knowledge Format (OKF v0.2) diagnostic bundles that empowers any AI agent harness to audit Looker instance performance, enforce LookML modeling quality, optimize BigQuery warehouse compute, and compile publication-grade Technical Design Documents (TDD).**

Structured following the [Looker Skills Standard](https://github.com/looker-open-source/looker-skills) for procedural capabilities and the [Dataplex OKF v0.2 Specification](https://www.mindstudio.ai/blog/how-to-build-okf-knowledge-bundle-share-ai-agents) for normative knowledge. Grounded in **Google Cloud Professional Services (PSO) performance benchmarks**.

---

## 📑 Table of Contents
1. [What It Does & The 3 Healthcheck Pillars](#1-what-it-does--the-3-healthcheck-pillars)
2. [Architecture & Standards: How the Repository Is Structured](#2-architecture--standards-how-the-repository-is-structured)
3. [The Catalog: Skills & Bundles](#3-the-catalog-skills--bundles)
4. [Tooling & Access Primitives](#4-tooling--access-primitives)
5. [How an AI Agent Harness Executes a Healthcheck](#5-how-an-ai-agent-harness-executes-a-healthcheck)
6. [OKF Bundle Packaging & Export](#6-okf-bundle-packaging--export)
7. [Conformance Testing & Evaluation](#7-conformance-testing--evaluation)

---

## 1. What It Does & The 3 Healthcheck Pillars

This repository replaces opaque manual audits and fragmented scripts with an autonomous, cross-layer diagnostic engine. It enables any AI harness (Gemini Jetski, Claude Code, Cursor, Codex, LangGraph) to correlate telemetry across **Looker System Activity**, **LookML AST code semantics**, and **BigQuery INFORMATION_SCHEMA**:

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

| Pillar | Scope & Focus Area | Key Healthcheck Dimensions Audited |
| :--- | :--- | :--- |
| **Pillar 1: Looker Performance** | Instance & Content Governance *(System Activity)* | • **3-Way Latency Triage**: Looker JVM Init/Compile % vs. DB execution average vs. Connection queue wait.<br>• **Dashboard Content Hygiene**: Tile density (>25 tiles), auto-refresh loops, merged query misuse.<br>• **Caching & Delivery**: Datagroup ETL alignment, PDT build triggers, schedule staggering. |
| **Pillar 2: LookML Quality** | Semantic Modeling & AST Hygiene *(looker-skills Reviewer)* | • **Primary Key Integrity**: Mandatory `primary_key: yes` on joined views to eliminate `SUM(DISTINCT ...)` symmetric aggregate hashing.<br>• **Explicit Joins**: Unambiguous `relationship: many_to_one/one_to_many`, clean column-to-column equality joins in `sql_on`.<br>• **Field Privacy & Governance**: Mask technical keys (`hidden: yes`), prune dead fields with Henry vacuum, conversational descriptions for Gemini. |
| **Pillar 3: BigQuery Engine** | Warehouse Compute & Storage *(INFORMATION_SCHEMA)* | • **Slot Contention Curves**: Peak slot saturation (>200 slots), queued query units in `JOBS_TIMELINE`.<br>• **Table Physical Layout**: Partitioning (`PARTITION BY DATE(...)`) and clustering (`CLUSTER BY ...`) DDL to minimize scanned bytes.<br>• **Execution Diagnostics**: Memory shuffle spills and disk spill forensics on slow queries.<br>• **Acceleration**: Aggregate Awareness LookML rollups and BI Engine readiness. |

### Key Deliverable
The healthcheck compiles findings into an authoritative, publication-grade **Technical Design Document (TDD)** adhering to OKF v0.2 (specification detailed in [`bundle/shared/playbooks/playbook_technical_design_document.md`](bundle/shared/playbooks/playbook_technical_design_document.md)):
1. Executive Summary & Problem Statement
2. Baseline Architecture & Forensic Telemetry
3. Pillar 1: Looker Performance & Query Lifecycle Diagnostics
4. Pillar 2: LookML Semantic Modeling & AST Diagnostics
5. Pillar 3: BigQuery Engine & Compute Diagnostics
6. Prioritized Remediation Roadmap (P0 / P1 / P2)
7. Production Code Verification & Validation Plan

---

## 2. Architecture & Standards: How the Repository Is Structured

This repository is built upon two complementary, open industry standards:
1. **Agent Skills Standard** (from [`looker-open-source/looker-skills`](https://github.com/looker-open-source/looker-skills) and Google/Anthropic ecosystems): Standardizes procedural capabilities into portable, self-documenting directory packages (`SKILL.md` + helper scripts).
2. **Open Knowledge Format (OKF v0.2)** (from Google Cloud Dataplex / Knowledge Catalog): Standardizes normative domain knowledge into structured, trust-verified, versioned markdown bundles.

```
                       ┌────────────────────────────┐
                       │     AI AGENT HARNESS       │
                       │ (Jetski, Claude, Cursor)   │
                       └─────────────┬──────────────┘
                                     │
          ┌──────────────────────────┴──────────────────────────┐
          ▼                                                     ▼
   PROCEDURAL SKILLS                                     OKF v0.2 KNOWLEDGE
   Directory: `skills/`                                  Directory: `bundle/`
   "HOW to do the work"                                  "WHAT facts govern the work"
   • Execution workflows & triggers                      • Domain facts, boundaries & logs
   • Safe CLI wrappers & scripts                         • 30-Check Master Rubric & SLAs
   • Live LookML streaming API                           • Attested SQL computations & DDL
```

---

### The 5 Core Artifact Types: Why They Are Separated

To prevent hallucinations, context window bloat, and monolithic script sprawl, knowledge and execution are strictly partitioned into five distinct artifact types:

| Artifact Type | Location | What It Is | Role for the AI Harness | Real Example in this Repo |
| :--- | :--- | :--- | :--- | :--- |
| **`SKILL`** | `skills/<name>/SKILL.md` | **Executable Procedure ("The Runbook")** | Guides the agent on **HOW** to interact with tools, execute scripts, and sequence its investigation. Contains triggers, step-by-step vectors, and CLI commands. | [`skills/looker-bq-healthcheck/SKILL.md`](skills/looker-bq-healthcheck/SKILL.md) |
| **`OKF BUNDLE`** | `bundle/<domain>/` | **Domain Container ("The Knowledge Base")** | High-level subject domain grouping rules, logs, and computations under a unified trust boundary. Declares ownership, versioning, and update logs (`log.md`). | [`bundle/looker_performance/`](bundle/looker_performance/) |
| **`PLAYBOOK`** | `bundle/**/playbooks/` | **Standard & Rubric ("The Grading Spec")** | Authoritative guidelines, scoring rubrics, and deliverable blueprints. Tells the agent **WHAT GOOD VS. BAD LOOKS LIKE** without hardcoding procedural commands. | [`bundle/shared/playbooks/playbook_technical_design_document.md`](bundle/shared/playbooks/playbook_technical_design_document.md) |
| **`COMPUTATION`** | `bundle/**/computations/` | **Attested Formula ("The Certified Query")** | Pre-tested, reproducible analytical equations and parameterized SQL queries. Annotated with OKF frontmatter (`type: Attested Computation`, `runtime: sql-bigquery`). Guarantees the agent executes mathematically sound formulas instead of guessing SQL. | [`bundle/bigquery_compute/computations/slot_consumption_timeline.md`](bundle/bigquery_compute/computations/slot_consumption_timeline.md) |
| **`REFERENCE`** | `bundle/**/references/` | **Benchmark & SLA ("The Manual")** | Static architectural reference guides, Google Cloud PSO latency SLAs (<3s interactive), CI/CD workflows, and access control policies. | [`bundle/looker_performance/references/benchmarks.md`](bundle/looker_performance/references/benchmarks.md) |

#### Why this separation is critical for AI Agent Harnesses:
* **Token Efficiency (Progressive Disclosure)**: An agent never ingests the whole repo into context. It loads only the `SKILL.md` orchestrator, which tells it to read specific `playbooks/` or `computations/` only when it reaches that specific phase.
* **Deterministic Accuracy**: Complex BigQuery telemetry queries (`INFORMATION_SCHEMA.JOBS_TIMELINE`) are pre-validated in `computations/`, eliminating syntax hallucination.
* **Maintainability**: When Google Cloud updates performance benchmarks or LookML best practices, only the markdown `references/` or `playbooks/` change—zero changes are needed to the procedural skills or python harnesses.

---

### Annotated Repository File Tree

```
looker-healthcheck/
├── manifest.yaml                    # Master Catalog Manifest (OKF v0.2 + upstream dependencies)
├── README.md                        # Master architectural & user guide
├── requirements.txt                 # Lightweight packaging dependencies (pyyaml)
│
├── skills/                          # PROCEDURAL AGENT SKILLS (Agent Skills Standard)
│   ├── looker-bq-healthcheck/       # Master 3-pillar healthcheck orchestrator & TDD compiler
│   │   ├── SKILL.md                 # 5-vector execution workflow & upstream delegation rules
│   │   └── scripts/                 # Safe CLI execution tools
│   │       ├── safe_looker.sh       # Read-only guardrail (blocks rm, delete, drop, truncate)
│   │       ├── stream_lookml.sh     # Live LookML streaming API without git cloning
│   │       └── validate_lookml.sh   # Direct project compilation validator
│   └── bq-jobs-diagnostics/         # Pillar 3: BigQuery compute diagnostics skill
│       ├── SKILL.md                 # Slot curves, memory/disk spills, partition/cluster auditing
│       └── scripts/
│           └── run_bq_query.sh      # PrettyJSON bq query runner
│
├── bundle/                          # NORMATIVE KNOWLEDGE CATALOG (OKF v0.2 Specification)
│   ├── index.md                     # Root catalog index declaring okf_version: "0.2"
│   ├── log.md                       # Master chronological audit log
│   │
│   ├── looker_performance/          # PILLAR 1: Looker query lifecycle & instance performance
│   │   ├── index.md, log.md         # Domain index & change audit log
│   │   ├── playbooks/               # Performance playbooks & content governance SOPs
│   │   ├── computations/            # Attested query latency breakdown formulas
│   │   └── references/              # Google Cloud PSO benchmarks (<3s SLAs) & query outliers
│   │
│   ├── lookml_quality/              # PILLAR 2: LookML semantic modeling & AST quality
│   │   ├── index.md, log.md         # Domain index & change audit log
│   │   ├── playbooks/               # 30-Check Master LookML Audit Rubric & Transcriber 0-4 scoring
│   │   ├── computations/            # PDT failure event logs & AST risk calculators
│   │   └── references/              # Henry vacuum guides, Spectacles CI, legacy runtime recipes
│   │
│   ├── bigquery_compute/            # PILLAR 3: BigQuery engine & warehouse optimization
│   │   ├── index.md, log.md         # Domain index & change audit log
│   │   ├── playbooks/               # Partitioning/clustering guides, BI Engine acceleration
│   │   ├── computations/            # Attested SQL queries (slot contention, bytes billed)
│   │   └── references/              # Pipeline architecture, warehouse optimization
│   │
│   └── shared/                      # Cross-cutting deliverables & enterprise standards
│       ├── index.md, log.md         # Shared index & change audit log
│       ├── playbooks/               # 7-Section Technical Design Document (TDD) playbook
│       └── references/              # Security roles, development workflows, and CI/CD
│
├── scripts/                         # STANDALONE UTILITIES
│   ├── export_okf_bundle.py         # Packages bundles into checksummed .tar.gz archives
│   └── sync_skills.py               # Sparse-checkout sync for upstream looker-skills
│
└── evals/                           # ZERO-DEPENDENCY 3-LAYER TEST SUITE (15/15 PASSING)
    ├── run_evals.py                 # Unified test runner (<50ms execution)
    ├── test_transcriber_scoring.py  # Layer 1: Transcriber 0-4 rubric benchmarks
    ├── test_okf_conformance.py      # Layer 2: OKF v0.2 spec verification
    └── test_skills_conformance.py   # Layer 3: Agent Skills standard & manifest verification
```

---

## 3. The Catalog: Skills & Bundles

All skills and knowledge bundles are declared in [`manifest.yaml`](manifest.yaml):

| Bundle ID | Domain | Primary Skill | Path in `bundle/` | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`looker-healthcheck`** | Master Suite | [`skills/looker-bq-healthcheck/SKILL.md`](skills/looker-bq-healthcheck/SKILL.md) | `bundle/` | Master orchestrator triangulating query latency, LookML AST flaws, and BigQuery slot contention. Compiles `TECHNICAL_DESIGN_DOCUMENT.md`. |
| **`looker-performance`** | Pillar 1 | [`skills/looker-bq-healthcheck/SKILL.md`](skills/looker-bq-healthcheck/SKILL.md) | `bundle/looker_performance/` | Query lifecycle latency phase breakdown (Looker JVM overhead % vs DB execution vs queue wait), dashboard tile bloat, and schedule concurrency. Delegates to upstream `looker-performance-optimizer`. |
| **`lookml-quality`** | Pillar 2 | [`skills/looker-bq-healthcheck/SKILL.md`](skills/looker-bq-healthcheck/SKILL.md) | `bundle/lookml_quality/` | Semantic modeling audit: `primary_key: yes` integrity (eliminating `SUM(DISTINCT ...)` symmetric aggregate hashing), explicit joins, unmasked keys, and dead fields. Delegates to upstream `lookml-reviewer`. |
| **`bigquery-compute`** | Pillar 3 | [`skills/bq-jobs-diagnostics/SKILL.md`](skills/bq-jobs-diagnostics/SKILL.md) | `bundle/bigquery_compute/` | Slot contention timelines (`INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT`), table partitioning & clustering DDL, memory/disk spills, and Aggregate Awareness. |

> **Upstream Vendor Dependency**: For generic Looker CLI operations, authentication, LookML code review, and standard LookML guidelines, this repository integrates with the official [**`looker-open-source/looker-skills`**](https://github.com/looker-open-source/looker-skills) catalog (`using-looker-cli`, `authenticating-looker-cli`, `looker-performance-optimizer`, `lookml-reviewer`, `lookml-modeling-guidelines`).

---

## 4. Tooling & Access Primitives

Any agent harness interacts with the external systems using two standard, ubiquitous command-line tools:

### 1. Looker CLI (`looker-cli`)
* **Zero-Secret PKCE OAuth**: No long-lived API secrets in environment variables.
* **Authenticate**:
  ```bash
  looker-cli session login --oauth --client-id com.looker.cli
  ```
* **Discovery & Schema**:
  ```bash
  looker-cli meta search <keyword>
  ```
  ```bash
  looker-cli <command> --template
  ```
* **Read-Only Safety Guardrail**:
  All read actions can be routed through the safety wrapper to block destructive verbs (`rm`, `delete`, `drop`, `truncate`):
  ```bash
  bash skills/looker-bq-healthcheck/scripts/safe_looker.sh <command>
  ```
* **Parallel LookML Streamer**:
  Fetch and cache model and view files live without cloning git repos:
  ```bash
  bash skills/looker-bq-healthcheck/scripts/stream_lookml.sh <project_id> /tmp/lookml
  ```
* **LookML Validator**:
  Validate project compilation and syntax directly:
  ```bash
  bash skills/looker-bq-healthcheck/scripts/validate_lookml.sh <project_id>
  ```

### 2. BigQuery CLI (`bq`)
* **Identity**: Uses standard Google Cloud credentials (`gcloud auth login` or ADC).
* **Forensic Queries**:
  ```bash
  bq query --use_legacy_sql=false --format=prettyjson "<SQL>"
  ```
* **Helper Wrapper**:
  ```bash
  bash skills/bq-jobs-diagnostics/scripts/run_bq_query.sh "<SQL>"
  ```

---

## 5. How an AI Agent Harness Executes a Healthcheck

Whether running inside a coding agent (Gemini Jetski, Claude Code, Cursor), a multi-agent framework (LangGraph, AutoGen, CrewAI), or an autonomous loop, the harness interfaces with this repository through a **5-step execution lifecycle**:

```
                       ┌────────────────────────────┐
                       │        USER PROMPT         │
                       │ "Run healthcheck on model" │
                       └─────────────┬──────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                           AGENT HARNESS                                │
 │                                                                        │
 │  1. DISCOVERY & ACTIVATION                                             │
 │     Scans skills/ -> selects skills/looker-bq-healthcheck/SKILL.md     │
 │                                                                        │
 │  2. PROGRESSIVE DISCLOSURE                                             │
 │     Reads SKILL.md -> loads targeted playbooks from bundle/ on demand  │
 │                                                                        │
 │  3. SAFE ENVIRONMENT & TOOL EXECUTION                                  │
 │     Runs looker-cli (via safe_looker.sh) & bq (via run_bq_query.sh)    │
 │                                                                        │
 │  4. CROSS-LAYER TRIANGULATION                                          │
 │     Correlates BQ slot spikes with LookML AST flaws & JVM overhead     │
 │                                                                        │
 │  5. SYNTHESIS & SCORING                                                │
 │     Outputs TECHNICAL_DESIGN_DOCUMENT.md with 0–100% health score      │
 └────────────────────────────────────────────────────────────────────────┘
```

### The 5-Step Execution Lifecycle

#### 1. Discovery & Registration
The harness scans `skills/` (or parses [`manifest.yaml`](manifest.yaml)). It reads each skill's standardized YAML frontmatter (`name` and `description`). When a user asks:
> *"Audit the query performance and LookML quality of the 'ecommerce' model in dataset 'prod_analytics'"*

The harness matches this intent to `skills/looker-bq-healthcheck/SKILL.md` and loads it into working memory.

#### 2. Progressive Knowledge Ingestion (`bundle/`)
To prevent context window bloat and hallucination, the harness **does not load the entire repository at once**. Instead, [`SKILL.md`](skills/looker-bq-healthcheck/SKILL.md) instructs the harness to fetch specific, authoritative OKF documents on-demand using its native file-reading tools:
* **Benchmarking & SLAs**: Reads [`bundle/looker_performance/references/benchmarks.md`](bundle/looker_performance/references/benchmarks.md) to evaluate query latency phases against Google Cloud PSO standards (<3s interactive SLA).
* **Attested SQL Queries**: Reads [`bundle/bigquery_compute/computations/slot_consumption_timeline.md`](bundle/bigquery_compute/computations/slot_consumption_timeline.md) to retrieve pre-validated BigQuery `INFORMATION_SCHEMA` queries.
* **Semantic Modeling Rules**: Reads [`bundle/lookml_quality/playbooks/playbook_lookml_quality.md`](bundle/lookml_quality/playbooks/playbook_lookml_quality.md) to execute the 30-check LookML audit rubric.

#### 3. Tool & CLI Execution
The harness uses its shell or terminal execution tool to run diagnostic commands via zero-secret, read-only wrappers:
* **Looker Telemetry**: Dissects latency phases via `looker-cli` routed through the safety guardrail:
  ```bash
  bash skills/looker-bq-healthcheck/scripts/safe_looker.sh query_metrics run ...
  ```
* **LookML Code Streaming**: Streams live model/view files directly to local disk without cloning Git repos:
  ```bash
  bash skills/looker-bq-healthcheck/scripts/stream_lookml.sh <project_id> /tmp/lookml
  ```
* **BigQuery Warehouse Telemetry**: Extracts job timelines, slot curves, and memory spills in JSON:
  ```bash
  bash skills/bq-jobs-diagnostics/scripts/run_bq_query.sh "<SQL>"
  ```

#### 4. Cross-Layer Triangulation
The harness synthesizes telemetry across layers to uncover root causes:
* **Looker Symptom**: Looker JVM spend is only 8%, but queries take 22s in database execution.
* **LookML Cause**: Explore joins lack `primary_key: yes`, forcing Looker to inject CPU-intensive symmetric aggregate hashing (`SUM(DISTINCT ...)`).
* **BigQuery Impact**: `INFORMATION_SCHEMA.JOBS_TIMELINE` reveals 300+ peak slot spikes and memory spills to disk on those exact query hashes.

#### 5. Deliverable Synthesis & Scoring
The harness references [`bundle/shared/playbooks/playbook_technical_design_document.md`](bundle/shared/playbooks/playbook_technical_design_document.md) and [`bundle/shared/playbooks/scoring_master_rubric.md`](bundle/shared/playbooks/scoring_master_rubric.md) to compile:
1. An executive 0–100% healthcheck score across all 3 pillars.
2. An authoritative, publication-grade `TECHNICAL_DESIGN_DOCUMENT.md` in the workspace detailing current state telemetry, target state architecture, concrete LookML/DDL remediation code, and a prioritized P0/P1/P2 roadmap.

---

### Supported Harness Archetypes

| Harness Archetype | Examples | How It Operates |
| :--- | :--- | :--- |
| **CLI / Coding Assistants** | Claude Code, Gemini Jetski, Cursor, Codex | Loads `skills/looker-bq-healthcheck/SKILL.md` directly, executes scripts in terminal, inspects `bundle/` markdown on-demand, writes TDD to workspace. |
| **Multi-Agent Orchestrators** | LangGraph, AutoGen, CrewAI | Orchestrator agent runs `looker-bq-healthcheck`, delegating tasks to sub-agents for `bq-jobs-diagnostics` and upstream `lookml-reviewer` concurrently. |
| **Knowledge / RAG Platforms** | Dataplex, MindStudio, NotebookLM | Ingests the standalone `.tar.gz` archives built with `python3 scripts/export_okf_bundle.py --bundle all`. |

---

## 6. OKF Bundle Packaging & Export

Export all or individual knowledge bundles into portable, checksum-verified `.tar.gz` distribution archives:

```bash
# Export all 4 bundles to dist/
python3 scripts/export_okf_bundle.py --bundle all

# Export an individual bundle
python3 scripts/export_okf_bundle.py --bundle lookml-quality
```

Each exported archive includes full content, bundle metadata, and SHA256 checksums in `bundle.json`.

---

## 7. Conformance Testing & Evaluation

The repository includes a comprehensive 3-layer test suite with zero external framework dependencies:

```bash
python3 evals/run_evals.py
```

### Evaluation Matrix (15 Tests, 100% Passing in <50ms)
* **Layer 1: Transcriber 0–4 Scoring Rubric Benchmarks** (`evals/test_transcriber_scoring.py`)
  * Validates anti-pattern fixtures score $\le 1.5$ (Unsatisfactory).
  * Validates exceptional enterprise fixtures score $\ge 3.5$ (Exceptional).
* **Layer 2: OKF v0.2 Knowledge Catalog Conformance** (`evals/test_okf_conformance.py`)
  * Validates normative bundle tree structure and core domains.
  * Enforces root index `okf_version: "0.2"` and non-root indexes without frontmatter.
  * Validates chronological logs (`log.md`), trust tier classification, and staleness engine.
  * Validates attested computation schemas and concept metadata.
* **Layer 3: Agent Skills Standard & Manifest Conformance** (`evals/test_skills_conformance.py`)
  * Validates `manifest.yaml` bundle definitions and dependencies.
  * Validates YAML frontmatter (`name`, `description`), sections, and markdown headers in all `SKILL.md` files.
  * Validates bash scripts and shebangs.
  * Validates bundle packaging and checksum integrity.

---

## 📄 License
Apache-2.0

