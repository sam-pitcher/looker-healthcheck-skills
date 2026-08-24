"""
Tools package for Looker Optimizer & Healthcheck ADK Agent.
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

from .lookml_fs import (
    run_lookml_validation,
    audit_primary_keys,
    audit_join_relationships,
    audit_caching_and_datagroups,
    audit_explore_filters,
    audit_lookml_dashboards,
    run_henry_vacuum,
    audit_explore_field_exposure,
    audit_folder_structure,
    audit_naming_conventions,
    audit_metadata_descriptions,
    audit_unused_joins,
    discover_model_tables,
    list_lookml_files,
    read_lookml_file,
    search_lookml_code
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
    "run_inline_query",
    "get_query_sql",
    "get_looker_history_by_slug",
    "get_explore_definition",
    "run_bq_query",
    "looker_cli_discover",
    "looker_cli_inspect_payload",
    "looker_cli_execute",
    "run_consolidated_healthcheck_benchmark",
    "check_subsystem_status",
    "list_projects",
    "list_models",
    "get_system_telemetry_kpis",
    "get_slow_query_outliers",
    "get_user_persona_and_error_rates",
    "execute_complete_healthcheck",
    "run_lookml_validation",
    "audit_primary_keys",
    "audit_join_relationships",
    "run_henry_vacuum",
    "audit_explore_field_exposure",
    "audit_folder_structure",
    "audit_naming_conventions",
    "audit_metadata_descriptions",
    "audit_unused_joins",
    "discover_model_tables",
    "list_lookml_files",
    "read_lookml_file",
    "search_lookml_code",
    "audit_partition_cluster_filters",
    "audit_datagroup_sync",
    "audit_query_costs_and_bytes_billed",
    "get_looker_bigquery_job_correlations",
    "audit_bq_slots",
    "list_dataset_tables",
    "optimize_table_layout",
    "estimate_query_cost_dry_run",
    "save_audit_report",
    "get_audit_history",
    "get_audit_document",
    "save_technical_design_document",
    "get_skill_content",
    "list_registered_skills",
    "get_okf_index",
    "get_okf_attested_computation",
    "validate_okf_knowledge_catalog",
    "get_okf_concept_graph",
    "find_diagnostic_graph_path",
    "audit_okf_concept_graph"
]

