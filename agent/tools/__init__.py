"""
Tools package for Looker Optimizer & Healthcheck ADK Agent.
Implements pure dynamic discovery, API telemetry, BigQuery SQL execution,
and OKF v0.2 Knowledge Playbook ingestion.
"""

from .dynamic_cli import (
    looker_cli_discover,
    looker_cli_inspect_payload,
    looker_cli_execute,
    run_consolidated_healthcheck_benchmark
)

from .looker_api import (
    run_inline_query,
    get_query_sql,
    get_looker_history_by_slug,
    get_explore_definition,
    check_subsystem_status,
    list_projects,
    list_models,
    get_system_telemetry_kpis,
    get_slow_query_outliers,
    get_user_persona_and_error_rates,
    execute_complete_healthcheck
)

from .bq_client import (
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

from .storage import (
    save_audit_report,
    get_audit_history,
    get_audit_document,
    record_audit_finding,
    save_technical_design_document
)

from agent.skills_registry import (
    get_skill_content,
    list_registered_skills,
    get_okf_index,
    get_okf_attested_computation,
    validate_okf_knowledge_catalog,
    get_okf_concept_graph,
    find_diagnostic_graph_path,
    audit_okf_concept_graph
)

__all__ = [
    # Dynamic Looker CLI Primitives
    "looker_cli_discover",
    "looker_cli_inspect_payload",
    "looker_cli_execute",
    "run_consolidated_healthcheck_benchmark",
    # Looker API Telemetry Primitives
    "run_inline_query",
    "get_query_sql",
    "get_looker_history_by_slug",
    "get_explore_definition",
    "check_subsystem_status",
    "list_projects",
    "list_models",
    "get_system_telemetry_kpis",
    "get_slow_query_outliers",
    "get_user_persona_and_error_rates",
    "execute_complete_healthcheck",
    # BigQuery Execution Primitives
    "run_bq_query",
    "audit_partition_cluster_filters",
    "audit_datagroup_sync",
    "audit_query_costs_and_bytes_billed",
    "get_looker_bigquery_job_correlations",
    "audit_bq_slots",
    "list_dataset_tables",
    "optimize_table_layout",
    "estimate_query_cost_dry_run",
    # Persistence & Deliverables
    "save_audit_report",
    "get_audit_history",
    "get_audit_document",
    "record_audit_finding",
    "save_technical_design_document",
    # OKF Knowledge Playbooks & Graph
    "get_skill_content",
    "list_registered_skills",
    "get_okf_index",
    "get_okf_attested_computation",
    "validate_okf_knowledge_catalog",
    "get_okf_concept_graph",
    "find_diagnostic_graph_path",
    "audit_okf_concept_graph"
]
