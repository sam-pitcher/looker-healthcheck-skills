"""
Core Orchestration Layer for Looker & BigQuery Optimizer Agent System.
Built with Google Agent Development Kit (ADK) and Modular Multi-Agent Architecture.
Executes the Complete 30-Check Healthcheck Across 3 Pillars with Dynamic Model Scoping,
Upstream Skill Registry Ingestion, Safe Git Branch Patching, and Dual-Layer Persistence.
"""

import os
from pathlib import Path

try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
    os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", certifi.where())
except ImportError:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google.adk.agents import Agent
    from google.adk.apps import App
except ImportError:
    class Agent:  # Fallback lightweight mock for standalone CLI / Web mode
        def __init__(self, name: str = "", model: str = "", description: str = "", instruction: str = "", tools: list = None, sub_agents: list = None):
            self.name = name
            self.model = model
            self.description = description
            self.instruction = instruction
            self.tools = tools or []
            self.sub_agents = sub_agents or []
    
    class App:
        def __init__(self, name: str = "", root_agent: Any = None, plugins: list = None):
            self.name = name
            self.root_agent = root_agent
            self.plugins = plugins or []

from agent.telemetry import gcp_logging_plugin

# Dynamic Looker CLI Meta-Discovery & Guarded Execution Tools
from agent.tools.dynamic_cli import (
    looker_cli_discover,
    looker_cli_inspect_payload,
    looker_cli_execute,
    run_consolidated_healthcheck_benchmark
)

# Pillar 1 Tools (Instance & Content Telemetry)
from agent.tools.looker_api import (
    run_inline_query,
    get_query_sql,
    get_looker_history_by_slug,
    get_explore_definition,
    check_subsystem_status,
    list_projects,
    list_models,
    get_system_telemetry_kpis,
    get_slow_query_outliers,
    get_user_persona_and_error_rates
)

# Pillar 3 Tools (BigQuery Engine & Compute)
from agent.tools.bq_client import (
    run_bq_query,
    audit_partition_cluster_filters,
    audit_datagroup_sync,
    audit_query_costs_and_bytes_billed,
    get_looker_bigquery_job_correlations,
    audit_bq_slots,
    list_dataset_tables,
    optimize_table_layout,
    estimate_query_cost_dry_run
)

# Dual-Layer Storage Tools (Markdown + Firestore)
from agent.tools.storage import (
    save_audit_report,
    get_audit_history,
    get_audit_document,
    record_audit_finding,
    save_technical_design_document,
    compile_and_save_technical_design_document
)

# Dynamic Looker Skills Registry (Pure Knowledge Playbooks)
from agent.skills_registry import (
    get_skill_content,
    list_registered_skills,
    get_okf_index,
    get_okf_attested_computation,
    validate_okf_knowledge_catalog,
    get_okf_concept_graph,
    find_diagnostic_graph_path,
    audit_okf_concept_graph,
    get_active_graph_traversal_path,
    skill_registry
)

# Model Configuration (Default to gemini-3.7-flash)
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-3.7-flash")
AGENT_FLASH_MODEL = os.getenv("AGENT_FLASH_MODEL", "gemini-3.7-flash")

# Sub-Agent System Instructions Loader (Runtime Prompts & Tool Bindings)
PROMPTS_ROOT = Path(__file__).parent / "prompts"

def _load_agent_instruction(prompt_name: str) -> str:
    prompt_file = PROMPTS_ROOT / f"{prompt_name}.md"
    if prompt_file.exists():
        content = prompt_file.read_text(encoding="utf-8")
        return content.strip()
    return f"Execute diagnostics and remediation for domain: {prompt_name}"

# ==============================================================================
# SUB-AGENT 1: Looker Performance & Query Lifecycle Auditor (Pillar 1)
# ==============================================================================
looker_perf_agent = Agent(
    name="LookerPerformanceAgent",
    model=AGENT_FLASH_MODEL,
    description="Specialist in Looker Query Lifecycle Profiling, System Activity metrics, latency phase breakdown (Looker JVM overhead vs Database execution vs Connection queueing), slow query identification, dashboard tile density (>25 tiles), auto-refresh intervals, and schedule staggering.",
    instruction=_load_agent_instruction("content_auditor"),
    tools=[
        run_inline_query,
        get_query_sql,
        get_looker_history_by_slug,
        get_looker_bigquery_job_correlations,
        get_explore_definition,
        check_subsystem_status,
        list_models,
        list_projects,
        looker_cli_discover,
        looker_cli_inspect_payload,
        looker_cli_execute,
        record_audit_finding,
        save_audit_report,
        save_technical_design_document,
        get_audit_history,
        get_audit_document,
        list_registered_skills,
        get_skill_content,
        get_okf_index,
        get_okf_attested_computation,
        validate_okf_knowledge_catalog,
        get_okf_concept_graph,
        find_diagnostic_graph_path,
        get_active_graph_traversal_path,
        compile_and_save_technical_design_document
    ]
)
# Backward-compatible alias
content_agent = looker_perf_agent

# ==============================================================================
# SUB-AGENT 2: LookML Modeling & Code Quality Specialist (LookML Quality)
# ==============================================================================
lookml_agent = Agent(
    name="LookmlQualityAgent",
    model=AGENT_MODEL,
    description="Playbook-grounded LookML architecture & modeling auditor. Discovers and inspects LookML files live via looker-cli primitives, reasons directly over syntax trees (AST), verifies primary key uniqueness and join cardinalities to eliminate symmetric aggregations, and prescribes exact LookML diffs.",
    instruction=_load_agent_instruction("lookml_quality"),
    tools=[
        # Pure Execution Primitives & Dynamic CLI Discovery
        looker_cli_discover,
        looker_cli_inspect_payload,
        looker_cli_execute,
        # Telemetry & Deliverable Publishing
        record_audit_finding,
        save_technical_design_document,
        compile_and_save_technical_design_document,
        get_audit_history,
        get_audit_document,
        # OKF v0.2 Knowledge Playbooks & Semantic Concept Graph
        list_registered_skills,
        get_skill_content,
        get_okf_index,
        get_okf_attested_computation,
        validate_okf_knowledge_catalog,
        get_okf_concept_graph,
        find_diagnostic_graph_path,
        get_active_graph_traversal_path
    ]
)

# ==============================================================================
# SUB-AGENT 3: BigQuery Engine & Compute Optimizer (Pillar 3)
# ==============================================================================
bq_agent = Agent(
    name="BqOptimizerAgent",
    model=AGENT_MODEL,
    description="Diagnoses slow database queries, BigQuery SQL execution, AST anti-patterns (e.g. functions in JOIN ON clauses), BigQuery slot contention & timelines via INFORMATION_SCHEMA, unpartitioned warehouse scans, query cost outliers, and Aggregate Awareness rollups.",
    instruction=_load_agent_instruction("bq_optimizer"),
    tools=[
        run_bq_query,
        run_inline_query,
        get_query_sql,
        get_looker_history_by_slug,
        get_looker_bigquery_job_correlations,
        get_explore_definition,
        estimate_query_cost_dry_run,
        list_dataset_tables,
        record_audit_finding,
        save_audit_report,
        save_technical_design_document,
        compile_and_save_technical_design_document,
        get_audit_history,
        get_audit_document,
        list_registered_skills,
        get_skill_content,
        get_okf_index,
        get_okf_attested_computation,
        validate_okf_knowledge_catalog,
        get_okf_concept_graph,
        find_diagnostic_graph_path,
        get_active_graph_traversal_path
    ]
)

# In Google ADK, root_agent owns all direct sub-agents in a clean hierarchical topology.
looker_perf_agent.sub_agents = []
bq_agent.sub_agents = []
lookml_agent.sub_agents = []

# ==============================================================================
# MASTER ORCHESTRATOR: Root Supervisor Agent
# ==============================================================================
ROOT_INSTRUCTION = """
You are the **Looker & BigQuery Optimization Orchestrator**, the master supervisor agent responsible for orchestrating comprehensive, playbook-grounded healthchecks and performance investigations.

### 👥 Your Specialized Sub-Agents:
You coordinate 3 specialized sub-agents to perform deep-dive investigations:

1. **`LookerPerformanceAgent`** (Pillar 1 - Query Lifecycle & Looker Performance):
   - **MANDATORY CHECKS**:
     - System Activity latency phase breakdown (`query_metrics`): Looker JVM overhead % vs BigQuery `execute_main_query` vs connection queue wait.
     - Explore governance & partition filter enforcement (`audit_explore_filters`).
     - Caching & datagroup policy inspection (`audit_caching_and_datagroups`).
     - Dashboard tile bloat and schedule concurrency.
2. **`BqOptimizerAgent`** (Pillar 3 - BigQuery Engine & SQL Optimization):
   - **MANDATORY CHECKS**:
     - Physical SQL extraction & join anti-pattern detection (`get_query_sql`).
     - Dataset table & partition/clustering alignment (`list_dataset_tables`, `audit_partition_cluster_filters`).
     - Warehouse slot contention & saturation (`audit_bq_slots`).
     - Query costs & bytes billed (`audit_query_costs_and_bytes_billed`).
3. **`LookmlQualityAgent`** (Pillar 2 - LookML Modeling & Code Quality):
   - **MANDATORY CHECKS**:
     - Primary key integrity (`audit_primary_keys`) to prevent Symmetric Aggregate fan-out multiplier overhead.
     - Join relationships & SQL join conditions (`audit_join_relationships`) to catch `REGEXP_CONTAINS` and mismatched 1:1 fanout relations.
     - LookML naming hygiene (`audit_naming_conventions`) and raw key masking (`audit_explore_field_exposure`).
     - Dashboard quality & calculations (`audit_lookml_dashboards`).
     - Prescriptive, copy-paste LookML remediation code blocks.

### ⚡ Continuous Real-Time Finding Ingestion:
* **STREAM FINDINGS AS YOU WORK**: Sub-agents MUST call `record_audit_finding(...)` immediately upon identifying any issue, warning, or check score.
* Do NOT wait until the end of the entire audit. Continuous streaming ensures Firestore is always up to date even if a session is interrupted.

### 📢 LIVE USER PROGRESS COMMUNICATION (CRITICAL):
* **No Silent Spans**: Sub-agents MUST output short, informative status messages in chat as they transition through phases so the user sees live progress in real time (e.g. `🔍 [Phase 1: Looker Performance] Auditing query latency breakdown and dashboard bloat...`, `⚡ [Phase 2: BigQuery & Compute] Auditing slot utilization and partition layout...`, `🧩 [Phase 3: LookML Quality] Checking primary keys and join conditions...`).

### 🎯 Zero-Configuration & Minimal Prompt Handling:
If the user provides a minimal or open-ended prompt (e.g. *"run a healthcheck"*, *"audit performance"*, *"check my instance"*, *"how are we doing?"*, *"audit thelook"*):
* **DO NOT ASK CLARIFYING QUESTIONS OR REQUEST MISSING ARGS.** Autonomously infer the environment:
  - **Target Project & Model**: Infer from environment (`thelook-antigravity` / `thelook`) or discover via `list_models()`.
  - **Target BigQuery Dataset**: Infer from environment (`sampitcher-playground.the_look_ca`).
* **Autonomously run the complete 3-Pillar pipeline**:
  1. Transfer to `LookerPerformanceAgent` (Explore filters, datagroups, dashboard bloat, System Activity).
  2. Transfer to `BqOptimizerAgent` (Table partition layout, slot timeline, query billing).
  3. Transfer to `LookmlQualityAgent` (Primary keys, join conditions, AST naming rules, and final synthesis).

### 🛑 CRITICAL UI RESPONSE LENGTH & FINAL DELIVERY RULES:
1. **NEVER FLOOD THE CHAT WINDOW (MAX 30–40 LINES TOTAL)**:
   - When presenting the audit findings in chat, output ONLY:
     - 🎯 **Executive Scorecard Table** (Overall Health %, Pillar 1, 2, 3 Ratings).
     - 🚨 **Top 4 Critical Anti-Patterns** (1 bullet point each).
     - 💾 **Persistence Confirmation** (`✅ All findings recorded in Firestore (looker_healthchecks)`).
     - 📑 **Published Document Link**: Clickable link `[TECHNICAL_DESIGN_DOCUMENT.md](TECHNICAL_DESIGN_DOCUMENT.md)`.
2. **ALL DETAILED ARCHITECTURE & REMEDIATIONS BELONG IN TECHNICAL_DESIGN_DOCUMENT.MD**:
   - Telemetry and findings are persisted to Firestore in real time.
   - The authoritative 7-section engineering spec is written to `TECHNICAL_DESIGN_DOCUMENT.md` via `save_technical_design_document()`.
3. **MANDATORY CONCLUDING OUTPUT**: Never end a turn with an empty message or only tool output. The concluding agent MUST write the final executive message.

---

### 📝 Enterprise Technical Design Document (TDD) Authoring Protocol:
When a user asks to write a **Technical Design Document (TDD)**, architecture spec, or modernization proposal:
1. **Retrieve Playbook & Audit State**:
   - Call `get_skill_content("playbook_technical_design_document.md")` for the authoritative TDD specification.
   - Call `get_audit_document(audit_id)` or `get_audit_history()` to extract baseline telemetry, scores, and all structured findings from Firestore.
   - Ground in `looker_bigquery_pipeline_architecture.md`, `warehouse_optimization.md`, and `aggregate_awareness_and_architecture.md`.
2. **Synthesize an In-Depth, Publication-Grade 7-Section Document (NOT a simple pass/fail table)**:
   - **Section 1: Executive Summary & Modernization Objectives**: Scope, target KPIs (latency reductions, slot savings), and baseline ratings.
   - **Section 2: Current State Architecture & Forensic Telemetry**:
     - *2.1 What Is Working Well*: Explicitly commend existing architectural strengths, clean syntax, and valid models.
     - *2.2 Bottleneck Deep-Dive*: Latency phase breakdown (Looker JVM overhead vs DB query time vs Connection queue wait), slot saturation curves (>200 slots), and slow query profiles (>10s–25s) with Job IDs.
   - **Section 3: Target State Architecture & Data Flow**: Complete end-to-end Mermaid diagram from dashboards -> Looker datagroups -> Aggregate Awareness -> BigQuery partitioned/clustered tables.
   - **Section 4: Pillar 1 Technical Design (Looker Performance & Content Governance)**:
     - Decomposing 35-tile monolithic dashboards into modular tabbed navigation.
     - Datagroup overhaul (replacing `GENERATE_UUID()` with ETL watermark triggers).
     - Explore partition filter enforcement and schedule staggering.
   - **Section 5: Pillar 2 Technical Design (LookML Modeling & Hygiene)**:
     - Primary key strategy (eliminating `SUM(DISTINCT ...)` symmetric aggregate hashing overhead).
     - Refactoring cross joins and non-equi joins into equi-joins or pre-aggregated derived tables.
     - Eliminating functions/regex (`LOWER(TRIM())`, `REGEXP_CONTAINS()`) from `sql_on:`.
     - Exact copy-paste Before & After LookML code blocks.
   - **Section 6: Pillar 3 Technical Design (BigQuery Engine & Physical Storage Layout)**:
     - Exact BigQuery DDL for table partitioning (`PARTITION BY DATE(created_at)`) and clustering (`CLUSTER BY ...`).
     - LookML `aggregate_table` specifications for high-frequency queries.
     - BI Engine memory sizing.
   - **Section 7: Phased Migration Roadmap, Risk Matrix & Projected ROI**:
     - 3-Phase rollout plan (Zero-risk hotfixes -> LookML restructuring -> Warehouse partitioning).
     - Rollback procedures and validation gates.
     - Quantified ROI table (Expected % latency reduction, slot capacity freed, dollar cost savings).
3. **SAVE TO FILE - DO NOT FLOOD THE CHAT WINDOW**:
   - **MANDATORY**: Call `save_technical_design_document(tdd_markdown, output_filename="TECHNICAL_DESIGN_DOCUMENT.md")`.
   - In your chat turn, output ONLY a concise 1-page Executive Summary, the Target State Mermaid diagram, and a direct clickable link: `[TECHNICAL_DESIGN_DOCUMENT.md](TECHNICAL_DESIGN_DOCUMENT.md)`.
   - Prompt the user to explore specific sections or approve automated branch remediation.
"""

ORCHESTRATOR_TOOLS = [
    # Coordinator & Persistence Tools
    list_registered_skills,
    get_skill_content,
    save_audit_report,
    record_audit_finding,
    save_technical_design_document,
    compile_and_save_technical_design_document,
    get_audit_history,
    get_audit_document,
    get_looker_history_by_slug,
    get_looker_bigquery_job_correlations,
    get_okf_index,
    get_okf_attested_computation,
    validate_okf_knowledge_catalog,
    get_okf_concept_graph,
    find_diagnostic_graph_path,
    get_active_graph_traversal_path,
    audit_okf_concept_graph
]

ALL_30_TOOLS = ORCHESTRATOR_TOOLS

root_agent = Agent(
    name="LookerBqOptimizationOrchestrator",
    model=AGENT_MODEL,
    description="Master supervisor orchestrating LookerPerformanceAgent, LookmlQualityAgent, and BqOptimizerAgent for enterprise healthchecks, query lifecycle profiling, and LookML code optimization.",
    instruction=ROOT_INSTRUCTION.strip(),
    sub_agents=[looker_perf_agent, lookml_agent, bq_agent],
    tools=ORCHESTRATOR_TOOLS
)

# App definition with automated Google Cloud Logging lifecycle plugin
app = App(
    name="agent",
    root_agent=root_agent,
    plugins=[gcp_logging_plugin]
)


