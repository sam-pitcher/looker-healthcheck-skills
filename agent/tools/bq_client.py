"""
Generic BigQuery Client & Database Optimization Tools with Model Scoping.
Implements Pillar 3 & BigQuery Performance Checks (Tasks 21, 25, 30).
"""

import os
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

def _get_bq_client(project_id: Optional[str] = None):
    try:
        from google.cloud import bigquery
        proj = project_id or GCP_PROJECT_ID or None
        return bigquery.Client(project=proj, location=GCP_LOCATION)
    except Exception:
        return None

# ==============================================================================
# PILLAR 3: BIGQUERY INTEGRATION & DATABASE OPTIMIZATION (Tasks 21 to 30)
# ==============================================================================

def audit_partition_cluster_filters(table_id: str, project_id: Optional[str] = None, model_name: Optional[str] = None) -> str:
    """
    Task 21: Partition & Cluster Alignment.
    Audits table partitioning and clustering layout to ensure LookML views enforce `conditionally_filter` or `require_partition_filter: yes`.
    """
    pid = project_id or GCP_PROJECT_ID
    client = _get_bq_client(pid)
    if not client:
        return f"Ensure LookML views for table `{table_id}` enforce `conditionally_filter` or `require_partition_filter: yes`."
    
    try:
        table_ref = client.get_table(table_id)
        p_info = None
        if table_ref.time_partitioning:
            p_info = {
                "type": str(table_ref.time_partitioning.type_),
                "field": table_ref.time_partitioning.field,
                "require_partition_filter": table_ref.require_partition_filter
            }
        
        c_fields = list(table_ref.clustering_fields) if table_ref.clustering_fields else []
        
        report = {
            "table_id": table_id,
            "partitioning": p_info or "UNPARTITIONED",
            "clustering": c_fields or "NONE",
            "action_required": "Enforce partition filter in LookML view" if not (p_info and p_info.get("require_partition_filter")) else "HEALTHY"
        }
        return f"### 🎯 Partition & Clustering Alignment (`{table_id}`):\n```json\n{json.dumps(report, indent=2)}\n```"
    except Exception as e:
        return f"Partition audit error: {str(e)}"

def audit_datagroup_sync(project_id: Optional[str] = None, region: Optional[str] = None, hours: int = 24, model_name: Optional[str] = None) -> str:
    """
    Task 25: Caching Strategies (Datagroups).
    Queries BigQuery INFORMATION_SCHEMA to map warehouse ELT completion timestamps to Looker datagroup triggers.
    """
    pid = project_id or GCP_PROJECT_ID
    reg = region or GCP_LOCATION.split("-")[0] if GCP_LOCATION else "us"
    client = _get_bq_client(pid)
    
    query = f"""
    SELECT
      project_id,
      job_id,
      creation_time,
      end_time,
      TIMESTAMP_DIFF(end_time, creation_time, SECOND) as duration_seconds,
      statement_type
    FROM
      `region-{reg}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
      AND statement_type IN ('INSERT', 'MERGE', 'CREATE_TABLE_AS_SELECT')
    ORDER BY end_time DESC
    LIMIT 20;
    """
    
    if not client:
        return f"### 🔄 Datagroup & ELT Completion Mapping SQL:\n```sql\n{query}\n```"

    try:
        query_job = client.query(query)
        results = [dict(row) for row in query_job.result()]
        return f"### 🔄 BigQuery ELT Job Completion Timestamps ({len(results)} Found):\n```json\n{json.dumps(results, indent=2, default=str)}\n```"
    except Exception as e:
        return f"Datagroup ELT audit query:\n```sql\n{query}\n```\n*(Execution note: {str(e)})*"

def audit_query_costs_and_bytes_billed(project_id: Optional[str] = None, region: Optional[str] = None, hours: int = 24, model_name: Optional[str] = None) -> str:
    """
    Task 30: Query Cost Optimization with Model Scoping.
    Audits bytes scanned, GB billed, and on-demand costs for all queries executed by Looker using BigQuery INFORMATION_SCHEMA.
    """
    pid = project_id or GCP_PROJECT_ID
    reg = region or GCP_LOCATION.split("-")[0] if GCP_LOCATION else "us"
    client = _get_bq_client(pid)
    
    filter_clause = "(query LIKE '%Looker%' OR query LIKE '%-- Looker%')"
    if model_name:
        filter_clause += f" AND (query LIKE '%{model_name}%' OR query LIKE '%lookml_model: {model_name}%')"

    query = f"""
    SELECT
      TIMESTAMP_TRUNC(creation_time, HOUR) as hour_window,
      COUNT(DISTINCT job_id) as looker_queries_count,
      ROUND(SUM(total_bytes_billed) / (1024 * 1024 * 1024), 2) as total_gb_billed,
      ROUND(SUM(total_bytes_billed) / (1024 * 1024 * 1024) * 0.00625, 2) as estimated_cost_usd
    FROM
      `region-{reg}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
      AND {filter_clause}
    GROUP BY 1
    ORDER BY hour_window DESC
    LIMIT 24;
    """
    
    if not client:
        return f"### 💰 BigQuery Looker Cost & Data Scanned SQL:\n```sql\n{query}\n```"

    try:
        query_job = client.query(query)
        results = [dict(row) for row in query_job.result()]
        scope_str = f"for model `{model_name}`" if model_name else "across instance"
        return f"### 💰 Looker BigQuery Cost & Bytes Billed (Past {hours}h - {scope_str}):\n```json\n{json.dumps(results, indent=2, default=str)}\n```"
    except Exception as e:
        return f"Cost audit query:\n```sql\n{query}\n```\n*(Execution note: {str(e)})*"

def audit_bq_slots(project_id: Optional[str] = None, region: Optional[str] = None, hours: int = 24, model_name: Optional[str] = None) -> str:
    """Audits slot consumption and reservation ceilings."""
    pid = project_id or GCP_PROJECT_ID
    reg = region or GCP_LOCATION.split("-")[0] if GCP_LOCATION else "us"
    client = _get_bq_client(pid)
    
    query = f"""
    SELECT
      TIMESTAMP_TRUNC(period_start, HOUR) as hour_window,
      ROUND(AVG(period_slot_ms) / 1000, 2) as avg_slots,
      ROUND(MAX(period_slot_ms) / 1000, 2) as peak_slots
    FROM
      `region-{reg}`.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT
    WHERE
      period_start >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
    GROUP BY 1
    ORDER BY hour_window DESC
    LIMIT 24;
    """
    if not client:
        return f"### ⚡ BigQuery Slot Audit SQL:\n```sql\n{query}\n```"
    try:
        results = [dict(r) for r in client.query(query).result()]
        return f"### ⚡ Slot Audit Results:\n```json\n{json.dumps(results, indent=2, default=str)}\n```"
    except Exception as e:
        return f"Slot audit notice: {str(e)}"

def list_dataset_tables(dataset_id: str, project_id: Optional[str] = None) -> str:
    """Lists tables in a dataset."""
    pid = project_id or GCP_PROJECT_ID
    client = _get_bq_client(pid)
    if not client: return f"Dataset: {dataset_id}"
    try:
        tables = [t.table_id for t in client.list_tables(dataset_id)]
        return f"### Tables in `{dataset_id}`:\n```json\n{json.dumps(tables, indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def optimize_table_layout(table_id: str, project_id: Optional[str] = None) -> str:
    """Analyzes table partitioning and clustering."""
    return audit_partition_cluster_filters(table_id, project_id)

def estimate_query_cost_dry_run(sql_query: str, project_id: Optional[str] = None) -> str:
    """Dry-runs a SQL query."""
    pid = project_id or GCP_PROJECT_ID
    client = _get_bq_client(pid)
    if not client: return "Client offline."
    try:
        from google.cloud import bigquery
        job = client.query(sql_query, job_config=bigquery.QueryJobConfig(dry_run=True))
        gb = job.total_bytes_processed / (1024 * 1024 * 1024)
        return f"Dry-run: {gb:.4f} GB scanned (${gb * 0.00625:.5f} USD)"
    except Exception as e:
        return f"Dry-run error: {str(e)}"
