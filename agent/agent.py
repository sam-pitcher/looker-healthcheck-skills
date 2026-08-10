"""
Core Orchestration Layer for Looker & BigQuery Optimizer Agent System.
Built with Google Agent Development Kit (ADK) and Modular Multi-Agent Architecture.
Generic across ANY Looker instance, LookML project, and BigQuery database.
"""

import os
import certifi
from pathlib import Path
from dotenv import load_dotenv

# Auto-configure SSL certificate bundle for macOS / aiohttp / Vertex AI
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", certifi.where())

# Configure environment
load_dotenv()

from google.adk.agents import Agent

from agent.tools.looker_api import (
    list_projects,
    list_models,
    get_explore_schema,
    get_stale_schedules,
    get_tile_bloat_dashboards,
    archive_dashboard,
    deactivate_inactive_users,
    run_system_activity_kpis,
    run_healthcheck_audit
)

from agent.tools.lookml_fs import (
    list_lookml_files,
    read_lookml_file,
    search_lookml_code,
    run_henry_vacuum,
    apply_lookml_patch,
    run_lookml_validation
)

from agent.tools.bq_client import (
    audit_bq_slots,
    list_dataset_tables,
    optimize_table_layout,
    estimate_query_cost_dry_run
)

# Progressive Skill Loader
SKILLS_ROOT = Path(__file__).parent / "skills"

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
# SUB-AGENT 1: Content & Administration Auditor
# ==============================================================================
content_agent = Agent(
    name="ContentAuditorAgent",
    model="gemini-2.5-flash",
    description="Specialist agent that audits Looker content, dashboard tile bloat, zombie scheduled jobs, and user seat licenses.",
    instruction=_load_skill_instruction("content_audit"),
    tools=[
        get_stale_schedules,
        get_tile_bloat_dashboards,
        archive_dashboard,
        deactivate_inactive_users,
        run_system_activity_kpis
    ]
)

# ==============================================================================
# SUB-AGENT 2: LookML Modeling & Code Quality Specialist
# ==============================================================================
lookml_agent = Agent(
    name="LookmlQualityAgent",
    model="gemini-2.5-pro",
    description="Specialist agent that inspects LookML models and views across projects, runs Henry vacuuming, enforces primary keys, and optimizes datagroup caching.",
    instruction=_load_skill_instruction("lookml_quality"),
    tools=[
        list_projects,
        list_models,
        get_explore_schema,
        list_lookml_files,
        read_lookml_file,
        search_lookml_code,
        run_henry_vacuum,
        apply_lookml_patch,
        run_lookml_validation
    ]
)

# ==============================================================================
# SUB-AGENT 3: BigQuery Engine & Compute Optimizer
# ==============================================================================
bq_agent = Agent(
    name="BqOptimizerAgent",
    model="gemini-2.5-pro",
    description="Specialist agent that audits BigQuery slot utilization, discovers dataset tables, optimizes partitioning/clustering layout, and validates Aggregate Awareness.",
    instruction=_load_skill_instruction("bq_optimizer"),
    tools=[
        audit_bq_slots,
        list_dataset_tables,
        optimize_table_layout,
        estimate_query_cost_dry_run
    ]
)

# ==============================================================================
# MASTER ORCHESTRATOR: Root Agent
# ==============================================================================
ROOT_INSTRUCTION = """
You are the **Looker & BigQuery Optimization Orchestrator**.
You lead a team of specialized sub-agents to deliver comprehensive, professional-grade healthchecks and optimization plans for ANY Looker instance and data warehouse.

### Multi-Agent Coordination Protocol:
1. **Understand Request**: Determine the user's objective (e.g. Full Healthcheck, Dashboard Performance, LookML Refactoring, or Warehouse Cost Optimization).
2. **Delegate to Domain Specialists**:
   - For Content Bloat, Stale Schedules, or User Licenses: Delegate to `ContentAuditorAgent`.
   - For LookML files, Explores, Henry Vacuums, Primary Keys, or Datagroups: Delegate to `LookmlQualityAgent`.
   - For BigQuery Slot Starvation, Table Partitioning, Clustering, or Dry-Runs: Delegate to `BqOptimizerAgent`.
3. **Discover Instance & Projects Dynamically**:
   - Use `list_projects()`, `list_models()`, or `list_lookml_files()` to discover models and explores on the target instance dynamically without assuming hardcoded names.
4. **Synthesize Thematic Reports**:
   - Synthesize telemetry findings, benchmark scorecards, and root causes.
   - Present drop-in code fixes (LookML blocks, SQL patches, BigQuery DDL) with exact before/after instructions.
"""

root_agent = Agent(
    name="LookerBqOptimizationOrchestrator",
    model="gemini-2.5-pro",
    description="Master orchestrator coordinating comprehensive Looker and BigQuery performance healthchecks, modeling quality audits, and compute optimizations.",
    instruction=ROOT_INSTRUCTION.strip(),
    sub_agents=[content_agent, lookml_agent, bq_agent],
    tools=[
        run_healthcheck_audit,
        run_system_activity_kpis,
        list_projects,
        list_models,
        list_lookml_files
    ]
)
