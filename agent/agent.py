"""
Core Orchestration Layer for Looker & BigQuery Optimizer Agent System.
Built with Google Agent Development Kit (ADK) and Modular Multi-Agent Architecture.
Executes the Complete 30-Check Healthcheck Across 3 Pillars with Dynamic Model Scoping,
Upstream Skill Registry Ingestion, Safe Git Branch Patching, and Dual-Layer Persistence.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List

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

# Dynamic Looker CLI Meta-Discovery & Guarded Execution Tools (EXCLUSIVE LOOKER INTERFACE)
from agent.tools.dynamic_cli import (
    looker_cli_discover,
    looker_cli_inspect_payload,
    looker_cli_execute,
    run_consolidated_healthcheck_benchmark
)

# BigQuery Engine & Compute Tools (EXCLUSIVE BIGQUERY INTERFACE)
from agent.tools.bq_client import (
    run_bq_query,
    list_dataset_tables
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
    description="Specialist in Looker Query Lifecycle Profiling, System Activity metrics, latency phase breakdown (Looker JVM overhead vs Database execution vs Connection queueing), slow query identification, dashboard tile density (>25 tiles), auto-refresh intervals, and schedule staggering. Interacts with Looker exclusively via looker-cli primitives.",
    instruction=_load_agent_instruction("content_auditor"),
    tools=[
        # Dynamic Looker CLI Interface
        looker_cli_discover,
        looker_cli_inspect_payload,
        looker_cli_execute,
        # Telemetry & Deliverable Publishing
        record_audit_finding,
        save_audit_report,
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
    description="Diagnoses slow database queries, BigQuery SQL execution, AST anti-patterns, BigQuery slot contention & timelines via INFORMATION_SCHEMA, unpartitioned warehouse scans, query cost outliers, and Aggregate Awareness rollups.",
    instruction=_load_agent_instruction("bq_optimizer"),
    tools=[
        # BigQuery Execution Primitive
        run_bq_query,
        list_dataset_tables,
        # Looker CLI Interface
        looker_cli_discover,
        looker_cli_inspect_payload,
        looker_cli_execute,
        # Telemetry & Deliverable Publishing
        record_audit_finding,
        save_audit_report,
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
     - System Activity latency phase breakdown via `looker-cli query runquery`: Looker JVM overhead % vs BigQuery execution vs connection queue wait.
     - Explore governance & partition filter enforcement.
     - Dashboard tile density (>25 tiles), auto-refresh intervals (<30m), and scheduled plan staggering.
     - Caching policy & ETL datagroup synchronization.

2. **`LookmlQualityAgent`** (Pillar 2 - LookML Modeling & Code Quality):
   - **MANDATORY CHECKS**:
     - Discovers LookML projects and views live via `looker_cli_discover` and `looker_cli_execute`.
     - Primary key integrity: Verifies `primary_key: yes` is declared and unique across all joined views to prevent fanouts and costly `SUM(DISTINCT ...)` symmetric aggregate hashing.
     - Enforces explicit `relationship:` definitions (flags missing or default `many_to_one` mismatches).
     - Identifies unmasked technical foreign keys (`_id`, `_pk`, `_fk`) exposed without `hidden: yes`.
     - Validates field picker hygiene and description coverage for Gemini / Conversational Analytics readiness.
     - Delivers exact, production-ready LookML before/after code remediation diffs.

3. **`BqOptimizerAgent`** (Pillar 3 - BigQuery Engine & Compute Optimization):
   - **MANDATORY CHECKS**:
     - Table partitioning & clustering analysis: Identifies massive unpartitioned table scans (>10M rows) via BigQuery `INFORMATION_SCHEMA`.
     - Slot contention curves & timelines: Identifies peak slot saturation and queue wait spikes.
     - BI Engine acceleration & memory allocation audits.
     - Query cost & bytes billed outlier diagnosis.
     - Aggregate Awareness: Designs and prescribes exact LookML `aggregate_table` definitions for hot explores.
     - Generates production-ready BigQuery SQL DDL (`CREATE OR REPLACE TABLE ... PARTITION BY ... CLUSTER BY ...`).

---

### 📋 Orchestration Protocol:
1. When a user requests a healthcheck or audit:
   - Identify the target model or explore from the user prompt, or run `looker_cli_execute("model list")` to discover available models.
   - Dispatch `LookerPerformanceAgent` to complete Phase 1 (Query Lifecycle & Performance).
   - Hand off to `BqOptimizerAgent` to complete Phase 2 (BigQuery Warehouse & Compute).
   - Hand off to `LookmlQualityAgent` to complete Phase 3 (LookML Code Quality & Semantics).
2. Synthesize all findings into the final **Technical Design Document (TDD)** using `compile_and_save_technical_design_document`.
"""

root_agent = Agent(
    name="LookerBqOptimizationOrchestrator",
    model=AGENT_MODEL,
    description="Autonomous multi-agent orchestrator for Looker & BigQuery performance healthchecks, LookML refactoring, warehouse slot optimization, and publication of OKF v0.2 Technical Design Documents.",
    instruction=ROOT_INSTRUCTION,
    sub_agents=[looker_perf_agent, bq_agent, lookml_agent],
    tools=[
        looker_cli_discover,
        looker_cli_inspect_payload,
        looker_cli_execute,
        run_bq_query,
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
        get_active_graph_traversal_path,
        run_consolidated_healthcheck_benchmark
    ]
)

# App Container for ADK Deployment & Web UI
app = App(
    name="LookerBqOptimizationApp",
    root_agent=root_agent,
    plugins=[gcp_logging_plugin]
)
