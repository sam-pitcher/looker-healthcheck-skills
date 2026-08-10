"""
Core Orchestration Layer for Looker & BigQuery Optimizer Agent System.
Built with Google Agent Development Kit (ADK) and Modular Multi-Agent Architecture.
Executes the Complete 30-Check Healthcheck Across 3 Pillars with Dynamic Model Scoping,
Upstream Skill Registry Ingestion, Safe Git Branch Patching, and Dual-Layer Persistence.
"""

import os
import certifi
from pathlib import Path
from dotenv import load_dotenv

# Auto-configure SSL certificate bundle for macOS / aiohttp / Vertex AI
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", certifi.where())

load_dotenv()

from google.adk.agents import Agent

# Pillar 1 Tools (Instance & Content)
from agent.tools.looker_api import (
    check_subsystem_status,
    audit_connections,
    get_tile_bloat_dashboards,
    get_auto_refresh_dashboards,
    get_schedule_distribution,
    get_concurrency_peaks,
    get_unused_content_and_folders,
    get_unfiltered_dashboards,
    get_merged_queries,
    get_legacy_features,
    get_table_calculation_heavy_queries,
    get_bi_engine_metrics,
    get_pdt_failure_audit,
    get_aggregate_awareness_hits,
    get_complex_join_explores,
    list_projects,
    list_models,
    get_explore_schema,
    run_system_activity_kpis,
    run_healthcheck_audit
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
    audit_incremental_pdts,
    audit_oauth_connections,
    audit_join_key_syntax,
    list_lookml_files,
    read_lookml_file,
    search_lookml_code,
    apply_lookml_patch,
    apply_safe_lookml_patch
)

# Pillar 3 Tools (BigQuery Engine & Compute)
from agent.tools.bq_client import (
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

# Dynamic Looker Skills Registry
from agent.skills_registry import (
    get_skill_content,
    list_registered_skills,
    skill_registry
)

# Progressive Skill Loader
SKILLS_ROOT = Path(__file__).resolve().parent.parent / "agent" / "skills"

def _load_skill_instruction(skill_name: str) -> str:
    skill_file = SKILLS_ROOT / skill_name / "skill.md"
    if skill_file.exists():
        content = skill_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content.strip()
    return f"Execute diagnostics and remediation for domain: {skill_name}"

# ==============================================================================
# SUB-AGENT 1: Content & Administration Auditor (Pillar 1: Tasks 01 to 10)
# ==============================================================================
content_agent = Agent(
    name="ContentAuditorAgent",
    model="gemini-2.5-flash",
    description="Audits Looker instance subsystems, connections, tile bloat, auto-refresh rates, schedule spacing, concurrency bottlenecks, unused content, unfiltered queries, merged results, and legacy features (Tasks 01-10) with optional model scoping.",
    instruction=_load_skill_instruction("content_audit"),
    tools=[
        check_subsystem_status,
        audit_connections,
        get_tile_bloat_dashboards,
        get_auto_refresh_dashboards,
        get_schedule_distribution,
        get_concurrency_peaks,
        get_unused_content_and_folders,
        get_unfiltered_dashboards,
        get_merged_queries,
        get_legacy_features,
        run_system_activity_kpis,
        save_audit_report,
        get_audit_history,
        get_audit_document,
        list_registered_skills,
        get_skill_content
    ]
)

# ==============================================================================
# SUB-AGENT 2: LookML Modeling & Code Quality Specialist (Pillar 2: Tasks 11 to 20)
# ==============================================================================
lookml_agent = Agent(
    name="LookmlQualityAgent",
    model="gemini-2.5-pro",
    description="Validates LookML syntax, enforces primary keys, verifies join relationships, cleans unused fields with Henry (henry vacuum), hides raw keys, enforces folder/naming hygiene, audits metadata descriptions, prunes unused joins, and checks frontend calculations (Tasks 11-20) with interactive safe git patching.",
    instruction=_load_skill_instruction("lookml_quality"),
    tools=[
        run_lookml_validation,
        audit_primary_keys,
        audit_join_relationships,
        run_henry_vacuum,
        audit_explore_field_exposure,
        audit_folder_structure,
        audit_naming_conventions,
        audit_metadata_descriptions,
        audit_unused_joins,
        get_table_calculation_heavy_queries,
        audit_incremental_pdts,
        audit_oauth_connections,
        audit_join_key_syntax,
        list_projects,
        list_models,
        get_explore_schema,
        list_lookml_files,
        read_lookml_file,
        search_lookml_code,
        apply_lookml_patch,
        apply_safe_lookml_patch,
        save_audit_report,
        get_audit_history,
        get_audit_document,
        list_registered_skills,
        get_skill_content
    ]
)

# ==============================================================================
# SUB-AGENT 3: BigQuery Engine & Compute Optimizer (Pillar 3: Tasks 21 to 30)
# ==============================================================================
bq_agent = Agent(
    name="BqOptimizerAgent",
    model="gemini-2.5-pro",
    description="Audits partition/cluster alignment, BI Engine reservations, PDT build failures, incremental PDT configs, datagroup ETL sync, OAuth caching, Aggregate Awareness hits, join SQL hash keys, snowflake schema denormalization, and BigQuery query billing (Tasks 21-30).",
    instruction=_load_skill_instruction("bq_optimizer"),
    tools=[
        audit_partition_cluster_filters,
        get_bi_engine_metrics,
        get_pdt_failure_audit,
        audit_incremental_pdts,
        audit_datagroup_sync,
        audit_oauth_connections,
        get_aggregate_awareness_hits,
        audit_join_key_syntax,
        get_complex_join_explores,
        audit_query_costs_and_bytes_billed,
        audit_bq_slots,
        list_dataset_tables,
        optimize_table_layout,
        estimate_query_cost_dry_run,
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
You are the **Looker & BigQuery Optimization Orchestrator**.
You execute the complete **30-Task Healthcheck Program** across all 3 Pillars:
- **Pillar 1: Instance & Content Health (Tasks 01 to 10)**: Subsystems, Connections, Tile Bloat, Auto-Refresh, Schedules, Concurrency, Unused Content, Unfiltered Queries, Merged Queries, Legacy Features.
- **Pillar 2: LookML & Modeling Health (Tasks 11 to 20)**: Syntax Validation, Primary Keys, Join Relationships, Henry Unused Field Vacuum, Key Exposure, Folder Structure, Naming Casing, Metadata Descriptions, Unused Joins, Table Calculations.
- **Pillar 3: BigQuery & Warehouse Health (Tasks 21 to 30)**: Partition/Cluster Filters, BI Engine, PDT Build Failures, Incremental PDTs, Datagroup ELT Sync, OAuth Caching, Aggregate Awareness, Join Key Syntax, Snowflake Denormalization, Query Billing & INFORMATION_SCHEMA.

### Dynamic Model Scoping & Session Protocol:
1. When a user asks to audit a specific model or project (e.g. "audit model ecommerce_analytics"), execute all 30 checks scoped specifically to `model_name="ecommerce_analytics"`.
2. If no model is specified, list available models with `list_models()` or run an instance-wide audit across all models.

### Official Looker Skills Ingestion:
3. Before suggesting refactoring or LookML fixes, check `list_registered_skills()` and call `get_skill_content(skill_name)` (e.g. `looker-performance-optimizer`, `lookml-modeling-guidelines`, `lookml-liquid`, `lookml-tests`) to ensure your recommendations strictly follow official Google Cloud Looker engineering playbooks.

### Interactive Remediation (Pair-Programmer Mode):
4. When guiding the user through fixes:
   - Propose the exact LookML code snippet.
   - When confirmed or requested to fix, call `apply_safe_lookml_patch(file_path, patch_content, branch_name)` to create an isolated Git branch, write the fix, and automatically verify compilation.
   - If validation fails, inform the user that changes were safely rolled back with the compiler errors.

### State Persistence & Telemetry:
5. **MANDATORY**: At the end of every healthcheck audit, you MUST call `save_audit_report(report_markdown, structured_findings, model_name, project_id)` to persist structured telemetry to Firestore (`looker-healthcheck-db`) and write `AUDIT_REPORT.md`.
6. Use `get_audit_document()` to display stored Firestore records, and `get_audit_history()` to show historical trend comparisons when requested.
"""

ALL_30_TOOLS = [
    # Storage & History & Skills
    save_audit_report,
    get_audit_history,
    get_audit_document,
    list_registered_skills,
    get_skill_content,
    
    # Pillar 1: Instance & Content
    check_subsystem_status,
    audit_connections,
    get_tile_bloat_dashboards,
    get_auto_refresh_dashboards,
    get_schedule_distribution,
    get_concurrency_peaks,
    get_unused_content_and_folders,
    get_unfiltered_dashboards,
    get_merged_queries,
    get_legacy_features,
    run_system_activity_kpis,
    run_healthcheck_audit,
    
    # Pillar 2: LookML & Modeling
    run_lookml_validation,
    audit_primary_keys,
    audit_join_relationships,
    run_henry_vacuum,
    audit_explore_field_exposure,
    audit_folder_structure,
    audit_naming_conventions,
    audit_metadata_descriptions,
    audit_unused_joins,
    get_table_calculation_heavy_queries,
    list_projects,
    list_models,
    get_explore_schema,
    list_lookml_files,
    read_lookml_file,
    search_lookml_code,
    apply_lookml_patch,
    apply_safe_lookml_patch,
    
    # Pillar 3: BigQuery & Compute
    audit_partition_cluster_filters,
    get_bi_engine_metrics,
    get_pdt_failure_audit,
    audit_incremental_pdts,
    audit_datagroup_sync,
    audit_oauth_connections,
    get_aggregate_awareness_hits,
    audit_join_key_syntax,
    get_complex_join_explores,
    audit_query_costs_and_bytes_billed,
    audit_bq_slots,
    list_dataset_tables,
    optimize_table_layout,
    estimate_query_cost_dry_run
]

root_agent = Agent(
    name="LookerBqOptimizationOrchestrator",
    model="gemini-2.5-pro",
    description="Master orchestrator executing the complete 30-Check Looker & BigQuery Healthcheck across Instance Health, LookML Modeling, and Warehouse Compute with dynamic model scoping, upstream skill ingestion, and safe Git patching.",
    instruction=ROOT_INSTRUCTION.strip(),
    sub_agents=[content_agent, lookml_agent, bq_agent],
    tools=ALL_30_TOOLS
)
