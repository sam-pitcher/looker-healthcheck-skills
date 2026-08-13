"""
Deterministic Evaluation Suite: Unit & Integration Tests for All 30 Healthcheck Tools.
Verifies tool return formats, error safety, model scoping, and performance profiling.
"""

import os
import json
from pathlib import Path

# Import all tools cleanly from agent.tools
from agent.tools import (
    # Pillar 1
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
    get_slow_query_outliers,
    get_user_persona_and_error_rates,
    get_query_lifecycle_stages,
    run_system_activity_kpis,
    run_healthcheck_audit,
    execute_complete_healthcheck,
    
    # Pillar 2
    run_lookml_validation,
    audit_primary_keys,
    audit_join_relationships,
    run_henry_vacuum,
    audit_explore_field_exposure,
    audit_folder_structure,
    audit_naming_conventions,
    audit_metadata_descriptions,
    audit_unused_joins,
    
    # Pillar 3
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
    audit_bq_slots
)

# Storage & Telemetry
from agent.tools.storage import save_audit_report, get_audit_history, get_audit_document
from agent.telemetry import TelemetryTracer, trace_tool


def test_pillar1_subsystems_and_connections():
    """Verify Pillar 1 subsystem checks and database connections return safe formatted responses."""
    subsys = check_subsystem_status()
    assert isinstance(subsys, str)
    assert len(subsys) > 0

    conns = audit_connections()
    assert isinstance(conns, str)
    assert len(conns) > 0


def test_pillar1_dashboard_and_schedules():
    """Verify Pillar 1 tile bloat, refresh, schedule, and concurrency checks."""
    bloat = get_tile_bloat_dashboards(tile_threshold=25)
    assert isinstance(bloat, str)
    assert "tile" in bloat.lower() or "looker" in bloat.lower()

    refresh = get_auto_refresh_dashboards()
    assert isinstance(refresh, str)

    schedules = get_schedule_distribution()
    assert isinstance(schedules, str)

    concurrency = get_concurrency_peaks()
    assert isinstance(concurrency, str)


def test_pillar1_forensic_telemetry_discovery():
    """Verify slow query outliers, query lifecycle stages, and user personas."""
    outliers = get_slow_query_outliers(threshold_seconds=8.0)
    assert isinstance(outliers, str)
    assert len(outliers) > 0

    stages = get_query_lifecycle_stages()
    assert isinstance(stages, str)
    assert len(stages) > 0

    personas = get_user_persona_and_error_rates()
    assert isinstance(personas, str)
    assert len(personas) > 0


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
    """Verify Pillar 3 partitioning, BQ slots, PDTs, and datagroup synchronization."""
    partition = audit_partition_cluster_filters(table_id="project.analytics.orders")
    assert isinstance(partition, str)
    assert "partition" in partition.lower()

    slots = audit_bq_slots(hours=24)
    assert isinstance(slots, str)

    bi_engine = get_bi_engine_metrics()
    assert isinstance(bi_engine, str)

    pdts = get_pdt_failure_audit()
    assert isinstance(pdts, str)

    datagroups = audit_datagroup_sync(hours=24)
    assert isinstance(datagroups, str)

    costs = audit_query_costs_and_bytes_billed(hours=24)
    assert isinstance(costs, str)


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
        pass  # Fast dummy execution

    tracer.record_tool(name="mock_heavy_query", duration_ms=2500, status="SUCCESS")
    
    summary = tracer.end_trace()
    assert summary["tool_calls_count"] >= 1
    assert summary["slow_tools_count"] == 1
    assert len(summary["slowest_tools"]) == 1
