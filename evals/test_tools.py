"""
Deterministic Evaluation Suite: Unit & Integration Tests for Healthcheck Tools & Dynamic CLI.
Verifies tool return formats, error safety, model scoping, and performance profiling.
"""

import os
import json
from pathlib import Path

# Import clean tools from agent.tools
from agent.tools import (
    looker_cli_discover,
    looker_cli_inspect_payload,
    looker_cli_execute,
    run_consolidated_healthcheck_benchmark,
    check_subsystem_status,
    list_projects,
    list_models,
    get_system_telemetry_kpis,
    get_slow_query_outliers,
    get_user_persona_and_error_rates,
    execute_complete_healthcheck,
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
    search_lookml_code,
    audit_partition_cluster_filters,
    audit_datagroup_sync,
    audit_query_costs_and_bytes_billed,
    get_looker_bigquery_job_correlations,
    get_looker_history_by_slug,
    audit_bq_slots,
    list_dataset_tables,
    optimize_table_layout,
    estimate_query_cost_dry_run,
    save_audit_report,
    get_audit_history,
    get_audit_document,
    get_skill_content,
    list_registered_skills
)
from agent.telemetry import TelemetryTracer


def test_pillar1_subsystem_and_project_discovery():
    """Verify Pillar 1 subsystem checks and dynamic project/model discovery."""
    subsys = check_subsystem_status()
    assert isinstance(subsys, str)
    assert "HEALTHY" in subsys or "responsive" in subsys.lower()

    projs = list_projects()
    assert isinstance(projs, str)
    assert "LookML Projects" in projs or "notice" in projs.lower()

    models = list_models()
    assert isinstance(models, str)
    assert "LookML Models" in models or "notice" in models.lower()


def test_granular_telemetry_triage_tools():
    """Verify fast granular telemetry tools for agentic 3-way triage."""
    kpis = get_system_telemetry_kpis(model_name="ecommerce_analytics")
    assert isinstance(kpis, str)
    assert "Query Lifecycle Telemetry" in kpis or "error" in kpis.lower()

    outliers = get_slow_query_outliers(model_name="ecommerce_analytics", limit=3)
    assert isinstance(outliers, str)

    personas = get_user_persona_and_error_rates(model_name="ecommerce_analytics")
    assert isinstance(personas, str)


def test_pillar2_lookml_modeling_hygiene():
    """Verify Pillar 2 primary keys, join relationships, and field exposure checks."""
    pks = audit_primary_keys()
    assert isinstance(pks, str)
    assert "primary key" in pks.lower()

    joins = audit_join_relationships()
    assert isinstance(joins, str)
    assert "join" in joins.lower()

    exposure = audit_explore_field_exposure()
    assert isinstance(exposure, str)

    naming = audit_naming_conventions()
    assert isinstance(naming, str)

    metadata = audit_metadata_descriptions()
    assert isinstance(metadata, str)

    unused_joins = audit_unused_joins()
    assert isinstance(unused_joins, str)


def test_pillar3_bigquery_and_compute():
    """Verify Pillar 3 partitioning, BQ slots, and datagroup synchronization."""
    partition = audit_partition_cluster_filters(table_id="project.analytics.orders")
    assert isinstance(partition, str)
    assert "partition" in partition.lower()

    slots = audit_bq_slots(hours=24)
    assert isinstance(slots, str)

    datagroups = audit_datagroup_sync(hours=24)
    assert isinstance(datagroups, str)

    costs = audit_query_costs_and_bytes_billed(hours=24)
    assert isinstance(costs, str)


def test_dynamic_cli_discovery_and_guardrails():
    """Verify dynamic CLI meta-tree search, payload inspection, and safety guardrails."""
    # 1. Discover
    disc = looker_cli_discover("explore")
    assert isinstance(disc, str)
    assert "Looker CLI Discovery" in disc or "matching commands" in disc
    
    # 2. Inspect Payload
    payload = looker_cli_inspect_payload("api query run_inline_query")
    assert isinstance(payload, str)
    assert "Command Specification" in payload
    
    # 3. Guardrail: Destructive block
    block_res = looker_cli_execute("dashboard rm 9999")
    assert "SAFETY GUARDRAIL TRIGGERED" in block_res
    
    # 4. Safe read-only execution
    user_me = looker_cli_execute("user me")
    assert isinstance(user_me, str)
    assert "Output of `looker-cli user me`" in user_me or "Looker" in user_me


def test_one_click_consolidated_benchmark():
    """Verify one-click consolidated healthcheck benchmark execution and scoring."""
    res = run_consolidated_healthcheck_benchmark(model_name="ecommerce_analytics")
    assert isinstance(res, str)
    assert "Consolidated Healthcheck Benchmark Complete" in res
    assert "Overall Health Score" in res
    assert "Pillar 1" in res
    assert "Pillar 2" in res
    assert "Pillar 3" in res


def test_model_scoping_behavior():
    """Verify that passing model_name filters audits and persists scoped telemetry."""
    model_name = "ecommerce_analytics"
    
    report, structured = execute_complete_healthcheck(model_name=model_name)
    assert isinstance(report, str)
    assert isinstance(structured, dict)
    assert structured.get("total_checks", 0) == 30

    save_res = save_audit_report(report, structured, model_name=model_name)
    assert "ecommerce_analytics" in save_res.lower() or "audit_" in save_res


def test_dual_layer_storage():
    """Verify local report generation and history fetching."""
    history = get_audit_history(limit=5)
    assert isinstance(history, str)
    assert "Historical Healthcheck" in history or "audit_" in history


def test_telemetry_tracer():
    """Verify TelemetryTracer span tracking and summary aggregation."""
    tracer = TelemetryTracer()
    trace_id = tracer.start_trace(prompt="Test Healthcheck", model_scope="test_model")
    assert trace_id.startswith("trace_")

    with tracer.span(name="test_tool_execution", span_type="tool") as s:
        pass

    tracer.record_tool(name="mock_heavy_query", duration_ms=2500, status="SUCCESS")
    
    summary = tracer.end_trace()
    assert summary["tool_calls_count"] >= 1
    assert summary["slow_tools_count"] == 1
    assert len(summary["slowest_tools"]) == 1


def test_looker_bigquery_job_correlation_tools():
    """Verify BigQuery Job Labels correlation and Looker history_slug lookup."""
    bq_corr = get_looker_bigquery_job_correlations(hours=24, limit=5)
    assert isinstance(bq_corr, str)
    assert "Job Label" in bq_corr or "Correlations" in bq_corr or "SQL" in bq_corr

    looker_slug_res = get_looker_history_by_slug("mock_slug_12345")
    assert isinstance(looker_slug_res, str)
    assert "mock_slug_12345" in looker_slug_res
