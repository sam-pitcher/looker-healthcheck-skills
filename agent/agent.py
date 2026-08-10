"""
Core Orchestration Layer for Looker & BigQuery Optimizer Agent System.
Built with Google Agent Development Kit (ADK) and Modular Multi-Agent Architecture.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Configure environment
load_dotenv()

from google.adk.agents import Agent

from agent.tools.looker_api import (
    get_stale_schedules,
    get_tile_bloat_dashboards,
    archive_dashboard,
    deactivate_inactive_users,
    run_system_activity_kpis
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
    optimize_table_layout,
    estimate_query_cost_dry_run
)

# Helper function to load skill instructions on demand
def _load_skill_instruction(skill_folder: str) -> str:
    skill_path = Path(__file__).parent / "skills" / skill_folder / "skill.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return ""

CONTENT_SKILL = _load_skill_instruction("content_audit")
LOOKML_SKILL = _load_skill_instruction("lookml_quality")
BQ_SKILL = _load_skill_instruction("bq_optimizer")

# ---------------------------------------------------------------------------
# Sub-Agent 1: Content & Administration Auditor
# ---------------------------------------------------------------------------
content_agent = Agent(
    name="ContentAuditorAgent",
    model="gemini-2.5-flash",
    description="Audits dashboard tile counts (>25 tiles), merged query usage, zombie scheduled plans, and inactive user licenses.",
    tools=[
        get_stale_schedules,
        get_tile_bloat_dashboards,
        archive_dashboard,
        deactivate_inactive_users
    ],
    instruction=f"""
You are the official Looker Content & Administration Auditor.
Analyze Looker instance content clutter, zombie schedules, and dashboard tile anti-patterns.

DETAILED AUDITING RECIPES:
{CONTENT_SKILL}
"""
)

# ---------------------------------------------------------------------------
# Sub-Agent 2: LookML Quality Specialist
# ---------------------------------------------------------------------------
lookml_agent = Agent(
    name="LookmlQualityAgent",
    model="gemini-2.5-pro",
    description="Audits LookML models, views, and explores. Runs Henry CLI vacuuming, enforces primary keys, hides foreign keys, and configures Datagroup caching.",
    tools=[
        run_henry_vacuum,
        apply_lookml_patch,
        list_lookml_files,
        read_lookml_file,
        search_lookml_code,
        run_lookml_validation
    ],
    instruction=f"""
You are the official LookML Quality & Modeling Specialist.
Audit LookML files for readability, metadata hygiene, symmetric aggregate safety (primary keys), and Datagroup caching.

PROACTIVE CODE ACCESS:
- Use `list_lookml_files` to discover models and views (supports both local git repos and remote Looker projects via looker-cli).
- Use `read_lookml_file` to read the exact LookML definitions.
- Use `search_lookml_code` to search for keywords (e.g. `datagroup`, `primary_key`, `sql_trigger`).
- Use `run_henry_vacuum` to find unused fields.
- Use `apply_lookml_patch` to update files.

DETAILED MODELING & REFACTORING RECIPES:
{LOOKML_SKILL}
"""
)

# ---------------------------------------------------------------------------
# Sub-Agent 3: BigQuery Engine & Compute Optimizer
# ---------------------------------------------------------------------------
bq_agent = Agent(
    name="BqOptimizerAgent",
    model="gemini-2.5-pro",
    description="Audits BigQuery slot ceilings, reservation timeouts, table partitioning/clustering layouts, and Looker Aggregate Awareness.",
    tools=[
        audit_bq_slots,
        optimize_table_layout,
        estimate_query_cost_dry_run
    ],
    instruction=f"""
You are the official BigQuery Engine & Compute Optimizer.
Audit BigQuery compute usage, slot starvation during dashboard peak hours, partition/cluster health, and Aggregate Awareness materializations.

DETAILED COMPUTE & LAYOUT RECIPES:
{BQ_SKILL}
"""
)

# ---------------------------------------------------------------------------
# Root Orchestrator Agent
# ---------------------------------------------------------------------------
ROOT_ORCHESTRATOR_INSTRUCTION = """
You are the Lead Looker & BigQuery Optimization Orchestrator.
You orchestrate comprehensive Looker Healthchecks and Refactoring Engagements across three specialized domains:

1. **Content & Administration** (`ContentAuditorAgent`): Dashboard tile counts, zombie schedules, inactive user accounts.
2. **LookML Modeling & Quality** (`LookmlQualityAgent`): Unused fields (Henry vacuum), missing primary keys, datagroups, and compile validation.
3. **BigQuery Engine & Compute** (`BqOptimizerAgent`): Slot ceiling timeouts, daily partitioning, clustering layout, and Aggregate Awareness.

ORCHESTRATION RULES:
- When a user asks for a comprehensive instance healthcheck, coordinate and delegate to each specialist agent in sequence.
- When a user asks a specific question (e.g., "Why is our cache rate 0%?" or "Check our BigQuery slot usage"), delegate directly to the relevant specialist sub-agent.
- Provide executive summaries grouped by **Theme** (Caching, Concurrency, Storage Layout, Governance) with concrete, drop-in code fixes.
"""

root_agent = Agent(
    name="LookerBqOptimizationOrchestrator",
    model="gemini-2.5-pro",
    description="Master Orchestrator for Looker Instance Healthchecks, LookML Refactoring, and BigQuery Compute Optimization.",
    instruction=ROOT_ORCHESTRATOR_INSTRUCTION,
    tools=[run_system_activity_kpis],
    sub_agents=[content_agent, lookml_agent, bq_agent]
)
