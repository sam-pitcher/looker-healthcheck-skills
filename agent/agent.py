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
    get_explore_definition,
    check_subsystem_status,
    list_projects,
    list_models,
    get_system_telemetry_kpis,
    get_slow_query_outliers,
    get_user_persona_and_error_rates
)

# Pillar 2 Tools (LookML Modeling & Quality)
from agent.tools.lookml_fs import (
    run_lookml_validation,
    audit_primary_keys,
    audit_join_relationships,
    run_henry_vacuum,
    audit_explore_field_exposure,
    audit_folder_structure,
    audit_naming_conventions,
    audit_metadata_descriptions,
    audit_unused_joins,
    list_lookml_files,
    read_lookml_file,
    search_lookml_code
)

# Pillar 3 Tools (BigQuery Engine & Compute)
from agent.tools.bq_client import (
    run_bq_query,
    audit_partition_cluster_filters,
    audit_datagroup_sync,
    audit_query_costs_and_bytes_billed,
    audit_bq_slots,
    list_dataset_tables,
    optimize_table_layout,
    estimate_query_cost_dry_run
)

# Dual-Layer Storage Tools (Markdown + Firestore)
from agent.tools.storage import (
    save_audit_report,
    get_audit_history,
    get_audit_document
)

# Dynamic Looker Skills Registry (Pure Knowledge Playbooks)
from agent.skills_registry import (
    get_skill_content,
    list_registered_skills,
    skill_registry
)

# Sub-Agent System Instructions Loader (Runtime Prompts & Tool Bindings)
PROMPTS_ROOT = Path(__file__).parent / "prompts"

def _load_agent_instruction(prompt_name: str) -> str:
    prompt_file = PROMPTS_ROOT / f"{prompt_name}.md"
    if prompt_file.exists():
        content = prompt_file.read_text(encoding="utf-8")
        return content.strip()
    return f"Execute diagnostics and remediation for domain: {prompt_name}"

# ==============================================================================
# ==============================================================================
# SUB-AGENT 1: Looker Performance & Query Lifecycle Auditor (Pillar 1)
# ==============================================================================
looker_perf_agent = Agent(
    name="LookerPerformanceAgent",
    model="gemini-2.5-flash",
    description="Specialist in Looker Query Lifecycle Profiling, System Activity metrics, latency phase breakdown (Looker JVM overhead vs Database execution vs Connection queueing), slow query identification, dashboard tile density (>25 tiles), auto-refresh intervals, and schedule staggering.",
    instruction=_load_agent_instruction("content_auditor"),
    tools=[
        run_inline_query,
        get_query_sql,
        get_explore_definition,
        looker_cli_discover,
        looker_cli_inspect_payload,
        looker_cli_execute,
        check_subsystem_status,
        save_audit_report,
        get_audit_history,
        get_audit_document,
        list_registered_skills,
        get_skill_content
    ]
)
# Backward-compatible alias
content_agent = looker_perf_agent

# ==============================================================================
# SUB-AGENT 2: LookML Modeling & Code Quality Specialist (Pillar 2)
# ==============================================================================
lookml_agent = Agent(
    name="LookmlQualityAgent",
    model="gemini-2.5-pro",
    description="Audits LookML code hygiene, syntax validation, primary key integrity (preventing SUM_DISTINCT fanouts), join relationships, dead field pruning with Henry, raw key masking, and prescribes LookML code recommendations.",
    instruction=_load_agent_instruction("lookml_quality"),
    tools=[
        run_inline_query,
        get_query_sql,
        get_explore_definition,
        looker_cli_discover,
        looker_cli_inspect_payload,
        looker_cli_execute,
        run_lookml_validation,
        audit_primary_keys,
        audit_join_relationships,
        run_henry_vacuum,
        audit_explore_field_exposure,
        audit_folder_structure,
        audit_naming_conventions,
        audit_metadata_descriptions,
        audit_unused_joins,
        list_projects,
        list_models,
        list_lookml_files,
        read_lookml_file,
        search_lookml_code,
        save_audit_report,
        get_audit_history,
        get_audit_document,
        list_registered_skills,
        get_skill_content
    ]
)

# ==============================================================================
# SUB-AGENT 3: BigQuery Engine & Compute Optimizer (Pillar 3)
# ==============================================================================
bq_agent = Agent(
    name="BqOptimizerAgent",
    model="gemini-2.5-pro",
    description="Diagnoses slow database queries, BigQuery SQL execution, AST anti-patterns (e.g. functions in JOIN ON clauses), BigQuery slot contention & timelines via INFORMATION_SCHEMA, unpartitioned warehouse scans, query cost outliers, and Aggregate Awareness rollups.",
    instruction=_load_agent_instruction("bq_optimizer"),
    tools=[
        run_bq_query,
        run_inline_query,
        get_query_sql,
        get_explore_definition,
        audit_partition_cluster_filters,
        audit_bq_slots,
        list_dataset_tables,
        optimize_table_layout,
        estimate_query_cost_dry_run,
        audit_query_costs_and_bytes_billed,
        audit_datagroup_sync,
        save_audit_report,
        get_audit_history,
        get_audit_document,
        list_registered_skills,
        get_skill_content
    ]
)

# ==============================================================================
# MASTER ORCHESTRATOR: Root Supervisor Agent
# ==============================================================================
ROOT_INSTRUCTION = """
You are the **Looker & BigQuery Optimization Orchestrator**, the master supervisor agent responsible for orchestrating comprehensive, playbook-grounded healthchecks and performance investigations.

### 👥 Your Specialized Sub-Agents:
You coordinate 3 specialized sub-agents to perform deep-dive investigations:

1. **`LookerPerformanceAgent`** (Pillar 1 - Query Lifecycle & Looker Performance):
   - **DELEGATE TO THIS AGENT FOR**: Looker System Activity query profiling, finding top slow queries across models/explores, breaking down query latency phases (Looker overhead vs Database time), checking connection queueing, dashboard tile bloat (>25 tiles), auto-refresh intervals, and schedule staggering.
2. **`BqOptimizerAgent`** (Pillar 3 - BigQuery Engine & SQL Optimization):
   - **DELEGATE TO THIS AGENT FOR**: Inspecting physical compiled SQL, detecting BigQuery anti-patterns (e.g. functions in JOIN ON, timezone conversion in WHERE), querying BigQuery INFORMATION_SCHEMA for slot contention, validating partition/clustering pruning, and estimating query cost dry-runs.
3. **`LookmlQualityAgent`** (Pillar 2 - LookML Modeling & Code Quality):
   - **DELEGATE TO THIS AGENT FOR**: Auditing LookML syntax, checking primary keys to prevent SUM_DISTINCT fan-outs, verifying join relationships, running Henry dead-field vacuums, and generating prescriptive LookML code fixes.

---

### 🧠 Autonomous Multi-Agent Investigation Workflow:
When a user asks for a performance investigation, slow query triage, or full healthcheck:

1. **Phase 1 (Looker Query Profiling)**:
   - Delegate to `LookerPerformanceAgent` to query `system__activity`, identify the top slow query IDs, and calculate the Looker vs Database latency split.
2. **Phase 2 (Database SQL Forensics)**:
   - Delegate to `BqOptimizerAgent` with the identified slow query ID(s) to extract compiled SQL, check BigQuery anti-patterns, and evaluate warehouse compute / slot contention.
3. **Phase 3 (LookML Code Fixes)**:
   - Delegate to `LookmlQualityAgent` to inspect the explore/view definitions and formulate exact LookML code remediations (e.g. `primary_key: yes`, `convert_tz: no`, `aggregate_table:`).
4. **Phase 4 (Synthesis & Persistence)**:
   - Synthesize all sub-agent findings into the standardized Scorecard report.
   - **MANDATORY**: Call `save_audit_report(report_markdown, structured_findings, model_name=model_name)` to persist the final deliverable to Firestore and AUDIT_REPORT.md.
"""

ORCHESTRATOR_TOOLS = [
    # Coordinator & Persistence Tools
    list_registered_skills,
    get_skill_content,
    save_audit_report,
    get_audit_history,
    get_audit_document,
]

ALL_30_TOOLS = ORCHESTRATOR_TOOLS

root_agent = Agent(
    name="LookerBqOptimizationOrchestrator",
    model="gemini-2.5-pro",
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


