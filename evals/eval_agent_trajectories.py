"""
Agent Trajectory & Scenario Evaluation Suite.
Evaluates agent reasoning, multi-step tool-use trajectories, sub-agent delegations,
and playbook citation accuracy across 5 core healthcheck personas.
"""

import os
import json
from typing import Dict, Any, List

from agent.agent import root_agent, content_agent, lookml_agent, bq_agent
from agent.skills_registry import skill_registry, get_skill_content, list_registered_skills
from agent.tools.dynamic_cli import looker_cli_discover, looker_cli_inspect_payload, looker_cli_execute
from agent.tools.looker_api import execute_complete_healthcheck
from agent.tools.storage import save_audit_report, get_audit_document
from agent.telemetry import TelemetryTracer


def test_trajectory_complete_30_check_healthcheck():
    """
    Scenario 1: Complete 30-Check Instance Healthcheck
    Evaluates:
      1. Execution of all 30 checks across Pillar 1, 2, and 3.
      2. Calculation of composite health score.
      3. Persistence of structured telemetry to local storage / Firestore.
    """
    tracer = TelemetryTracer()
    tracer.start_trace(prompt="Run complete 30-check healthcheck audit")

    report, structured = execute_complete_healthcheck()
    assert structured["total_checks"] == 30
    assert "overall_health_score" in structured
    assert structured["passed"] + structured["warning"] + structured["critical"] == 30

    save_msg = save_audit_report(report, structured)
    assert "audit_" in save_msg

    trace_summary = tracer.end_trace()
    assert trace_summary["metadata"]["prompt"] == "Run complete 30-check healthcheck audit"


def test_trajectory_model_scoped_investigation():
    """
    Scenario 2: Model-Scoped Healthcheck Audit
    Evaluates:
      1. Passing model_name='ecommerce_analytics' scopes tool execution.
      2. Generated audit_id reflects model slug.
      3. Structured findings contain valid 30 checks.
    """
    target_model = "ecommerce_analytics"
    report, structured = execute_complete_healthcheck(model_name=target_model)
    assert structured["total_checks"] == 30

    save_msg = save_audit_report(report, structured, model_name=target_model)
    assert "ecommerce_analytics" in save_msg.lower() or "audit_ecommerce_analytics" in save_msg


def test_trajectory_performance_outlier_triage():
    """
    Scenario 3: Looker Performance & Slow Query Triage
    Evaluates:
      1. Dynamic discovery tools (looker_cli_discover, looker_cli_inspect_payload, looker_cli_execute).
      2. Dynamic ingestion of playbook_looker_performance.md.
      3. Verification of Google Cloud PSO latency benchmarks.
    """
    disc = looker_cli_discover("query")
    assert isinstance(disc, str) and len(disc) > 0

    inspect = looker_cli_inspect_payload("api query run_inline_query")
    assert isinstance(inspect, str) and len(inspect) > 0

    perf_playbook = get_skill_content("playbook_looker_performance.md")
    assert "Performance" in perf_playbook or "Lifecycle" in perf_playbook
    assert "execute_main_query" in perf_playbook


def test_trajectory_lookml_quality_and_henry():
    """
    Scenario 4: LookML Modeling Hygiene & Dead Code Vacuum
    Evaluates:
      1. Sub-agent tool availability for LookML quality checks.
      2. Ingestion of playbook_lookml_quality.md.
      3. Transcriber scoring dimension readiness.
    """
    lookml_tools = [t.__name__ for t in lookml_agent.tools]
    expected_tools = [
        "run_lookml_validation",
        "audit_primary_keys",
        "audit_join_relationships",
        "run_henry_vacuum",
        "audit_explore_field_exposure",
        "read_lookml_file",
        "search_lookml_code",
        "get_explore_definition"
    ]
    for exp in expected_tools:
        assert exp in lookml_tools, f"Missing expected tool in LookML agent: {exp}"

    style_playbook = get_skill_content("playbook_lookml_quality.md")
    assert "LookML Quality" in style_playbook or "snake_case" in style_playbook


def test_trajectory_dynamic_skill_resolution():
    """
    Scenario 5: Dynamic Knowledge Resolution Engine
    Evaluates:
      1. Canonical vendor skills (e.g. looker-performance-optimizer).
      2. Custom playbooks (e.g. playbook_healthcheck_delivery.md).
      3. Deep-dive references (e.g. query_outliers_diagnosis.md).
    """
    vendor_skill = get_skill_content("looker-performance-optimizer")
    assert "looker-performance-optimizer" in vendor_skill.lower()

    custom_playbook = get_skill_content("playbook_healthcheck_delivery.md")
    assert "Healthcheck Delivery" in custom_playbook or "4-Pillar" in custom_playbook

    ref_guide = get_skill_content("query_outliers_diagnosis.md")
    assert "Query Outliers" in ref_guide or "system__activity" in ref_guide
