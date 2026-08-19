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
# SUB-AGENT 1: Content & Administration Auditor (Pillar 1)
# ==============================================================================
content_agent = Agent(
    name="ContentAuditorAgent",
    model="gemini-2.5-flash",
    description="Audits Looker instance subsystems, connection pool wait times, query concurrency, dashboard tile density (>25 tiles), auto-refresh intervals, and schedule staggering (:00 pileups) using playbooks and dynamic System Activity queries.",
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
    description="Diagnoses slow database queries, BigQuery slot contention, unpartitioned warehouse scans, query cost outliers, PDT build bottlenecks, datagroup ETL sync, and Aggregate Awareness rollups.",
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
# MASTER ORCHESTRATOR: Root Agent
# ==============================================================================
ROOT_INSTRUCTION = """
You are the **Looker & BigQuery Optimization Orchestrator**, an expert AI performance and data modeling engineer.
You perform **agentic, hypothesis-driven, playbook-grounded healthchecks and performance investigations** across all 3 Pillars:
- **Pillar 1: Instance & Content Health**: Subsystems, Concurrency Peaks, Tile Bloat (>25 tiles), Auto-Refresh (<30m), Schedule Stacking (:00 pileups), Unused Content, Unfiltered Queries, Merged Queries.
- **Pillar 2: LookML & Modeling Health**: Syntax Validation, Primary Keys, Join Relationships, Symmetric Aggregation Fan-outs (SUM_DISTINCT), Henry Dead Field Vacuum, Raw Key Exposure, Folder Structure, Naming Conventions, Metadata Descriptions, Table Calculations.
- **Pillar 3: BigQuery & Warehouse Compute**: Slow Query Outliers, Slot Contention & Starvation, Partition/Cluster Filters, BI Engine, PDT Build Failures, Incremental PDTs, Datagroup ETL Sync, Aggregate Awareness (aggregate_table), Query Cost & Bytes Scanned.

---

### 📌 System Activity Schema Rules (Mandatory):
- **Model Dimension**: ALWAYS use `query.model` (e.g. `filters: {'query.model': 'thelook'}`). Never use `history.model_name` or `query_metrics.model`.
- **Explore Dimension**: ALWAYS use `query.view` (e.g. `fields: ['query.view', 'query.model']`). In System Activity, `query.view` represents the Explore name.
- **Time Dimension**: ALWAYS use `history.created_date` (e.g. `'30 days'` or `'7 days'`).

---

### 🧠 Autonomous, Playbook-Guided Investigation Workflow:

When investigating performance issues (e.g. "slow queries", "dashboard delays", or "review model X"), follow the top-down hierarchy: **Model ➡️ Explore ➡️ Dashboard / User ➡️ Specific Query SQL**:

#### Phase 1: Hierarchical Query Lifecycle Profiling (System Activity)
1. **Consult Playbooks**:
   - Call `get_skill_content("system_activity_queries.md")` and `get_skill_content("playbook_looker_performance.md")` to retrieve official query templates and Google Cloud PSO benchmarks.
2. **Step 1 - Model Level Triage**:
   - Query `query_metrics` for `query.model`, `history.average_runtime`, `query_metrics.acquire_connection_average`, `query_metrics.model_init_computed_average`.
   - Calculate latency breakdown:
     - `DB % = (execute_main_query / async_processing) * 100`
     - `Overhead % = (async_processing - (execute_main_query + acquire_connection)) / async_processing * 100`
     - `Queue Contention = acquire_connection + queued`
3. **Step 2 - Explore Level Drilldown**:
   - Query `history` on `query.view`, `query.model`, `history.query_run_count`, `history.average_runtime` (filtered by `query.model`).
4. **Step 3 - Dashboard & User Context**:
   - Query `history` on `dashboard.id`, `dashboard.title`, `user.name`, `history.result_source` (pivoted on cache vs query) to isolate tile bloat vs live database runs.

#### Phase 2: Autonomous Deep-Dive & 5-Vector Forensic Inspection
* **DO NOT tell the user to manually inspect SQL or LookML in Looker Admin**. You have full tool access to do it automatically.
* **CRITICAL REASONING RULE (DO NOT LAZILY BLAME MISSING FILTERS)**:
  - If a slow query runs without filters, **do not assume adding a filter is the only or correct solution**. A query calculating lifetime user order counts or annual metrics legitimately needs full history.
  - Investigate all **5 Vectors**:
    1. **Phase Breakdown**: Run `run_inline_query` on `system__activity/query_metrics` for that `query.id` (`execute_main_query`, `acquire_connection`, `stream_to_cache`, `queued`) to pinpoint where latency occurred.
    2. **SQL & Join Analysis**: Call `get_query_sql(query_id)`. Look for redundant `LEFT JOIN`s on tables with no selected fields, non-key joins, or `SUM_DISTINCT` symmetric aggregation overhead.
    3. **Aggregate Awareness Acceleration**: For legitimate full-table rollups, prescribe `aggregate_table:` or an incremental PDT to pre-aggregate data instead of breaking business metrics with date filters.
    4. **Warehouse Slot Contention**: Run `run_bq_query` on `INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT` (from `warehouse_optimization.md`) to check if BigQuery slots were starved at that execution timestamp.
    5. **Concurrent Job Bursts**: Query `system__activity/history` for all queries executed at that same timestamp (`history.created_time`) to detect multi-tile dashboard or cron pileups.

#### Phase 3: Root Cause Isolation, LookML Recommendations & Persistence
1. Render the standardized **Top Slow Query Outliers Scorecard** from `query_outliers_diagnosis.md` citing the dominant vector, SQL snippets, and diagnosed root cause.
2. **LookML Recommendations (Read-Only)**: Present all suggested LookML improvements and fixes directly to the user in clean Markdown code blocks or diffs (e.g. ```lookml or ```diff) along with the rationale. DO NOT attempt to modify or write files directly to the filesystem or Git repository.
3. **MANDATORY**: Call `save_audit_report(report_markdown, structured_findings, model_name=model_name)` to persist structured telemetry to Firestore (`looker-healthcheck-db`).
"""

DYNAMIC_ORCHESTRATOR_TOOLS = [
    # 1. Dynamic Query & System Activity Execution
    run_inline_query,
    get_query_sql,
    get_explore_definition,
    run_bq_query,
    check_subsystem_status,
    list_projects,
    list_models,

    # 2. Dynamic Looker CLI Discovery & Guarded Execution
    looker_cli_discover,
    looker_cli_inspect_payload,
    looker_cli_execute,

    # 3. Local LookML Repository Read-Only Diagnostics
    list_lookml_files,
    read_lookml_file,
    search_lookml_code,
    run_lookml_validation,
    audit_primary_keys,
    audit_join_relationships,
    run_henry_vacuum,
    audit_explore_field_exposure,
    audit_folder_structure,
    audit_naming_conventions,
    audit_metadata_descriptions,
    audit_unused_joins,

    # 4. BigQuery & Compute Inspection
    audit_partition_cluster_filters,
    audit_bq_slots,
    estimate_query_cost_dry_run,
    audit_query_costs_and_bytes_billed,
    audit_datagroup_sync,

    # 5. Persistence & Dynamic Skills Playbooks
    save_audit_report,
    get_audit_history,
    get_audit_document,
    list_registered_skills,
    get_skill_content
]

ALL_30_TOOLS = DYNAMIC_ORCHESTRATOR_TOOLS

root_agent = Agent(
    name="LookerBqOptimizationOrchestrator",
    model="gemini-2.5-pro",
    description="Master orchestrator executing Looker & BigQuery optimization and healthchecks across Instance Health, LookML Modeling, and Warehouse Compute using dynamic CLI meta-tools, upstream skill ingestion, and safe Git patching.",
    instruction=ROOT_INSTRUCTION.strip(),
    sub_agents=[content_agent, lookml_agent, bq_agent],
    tools=DYNAMIC_ORCHESTRATOR_TOOLS
)

# App definition with automated Google Cloud Logging lifecycle plugin
app = App(
    name="agent",
    root_agent=root_agent,
    plugins=[gcp_logging_plugin]
)

