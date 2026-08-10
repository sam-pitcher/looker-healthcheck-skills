"""
Tools package for Looker Optimizer & Healthcheck ADK Agent.
"""

from .looker_api import (
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

from .lookml_fs import (
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

from .bq_client import (
    audit_partition_cluster_filters,
    audit_datagroup_sync,
    audit_query_costs_and_bytes_billed,
    audit_bq_slots,
    list_dataset_tables,
    optimize_table_layout,
    estimate_query_cost_dry_run
)

from .storage import (
    save_audit_report,
    get_audit_history,
    get_audit_document
)

from agent.skills_registry import (
    get_skill_content,
    list_registered_skills
)

__all__ = [
    "check_subsystem_status",
    "audit_connections",
    "get_tile_bloat_dashboards",
    "get_auto_refresh_dashboards",
    "get_schedule_distribution",
    "get_concurrency_peaks",
    "get_unused_content_and_folders",
    "get_unfiltered_dashboards",
    "get_merged_queries",
    "get_legacy_features",
    "get_table_calculation_heavy_queries",
    "get_bi_engine_metrics",
    "get_pdt_failure_audit",
    "get_aggregate_awareness_hits",
    "get_complex_join_explores",
    "list_projects",
    "list_models",
    "get_explore_schema",
    "run_system_activity_kpis",
    "run_healthcheck_audit",
    "run_lookml_validation",
    "audit_primary_keys",
    "audit_join_relationships",
    "run_henry_vacuum",
    "audit_explore_field_exposure",
    "audit_folder_structure",
    "audit_naming_conventions",
    "audit_metadata_descriptions",
    "audit_unused_joins",
    "audit_incremental_pdts",
    "audit_oauth_connections",
    "audit_join_key_syntax",
    "list_lookml_files",
    "read_lookml_file",
    "search_lookml_code",
    "apply_lookml_patch",
    "apply_safe_lookml_patch",
    "audit_partition_cluster_filters",
    "audit_datagroup_sync",
    "audit_query_costs_and_bytes_billed",
    "audit_bq_slots",
    "list_dataset_tables",
    "optimize_table_layout",
    "estimate_query_cost_dry_run",
    "save_audit_report",
    "get_audit_history",
    "get_audit_document",
    "get_skill_content",
    "list_registered_skills"
]
