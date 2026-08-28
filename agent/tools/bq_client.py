"""
Generic BigQuery Client & Database Optimization Tools with Model Scoping.
Implements Pillar 3 & BigQuery Performance Checks (Tasks 21, 25, 30).
"""

import os
import re
import json
import subprocess
import time
from functools import lru_cache
from typing import Dict, Any, Optional, List
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

RUNNER_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "sampitcher-playground")
TARGET_BQ_PROJECT_ID = os.getenv("TARGET_BIGQUERY_PROJECT") or os.getenv("BIGQUERY_PROJECT_ID") or RUNNER_PROJECT_ID
TARGET_BQ_LOCATION = os.getenv("TARGET_BIGQUERY_LOCATION") or os.getenv("BIGQUERY_LOCATION", "US")
TARGET_BQ_ACCOUNT = os.getenv("TARGET_BIGQUERY_ACCOUNT", "")
GCP_PROJECT_ID = TARGET_BQ_PROJECT_ID
GCP_LOCATION = TARGET_BQ_LOCATION

_CACHED_BQ_CREDS: Dict[str, Any] = {}

def _get_credentials_for_account(account_email: str):
    """Dynamically obtains OAuth credentials for a specific gcloud account email."""
    if not account_email:
        return None
    now = time.time()
    if account_email in _CACHED_BQ_CREDS:
        creds, acquired_at = _CACHED_BQ_CREDS[account_email]
        if now - acquired_at < 3000:  # Valid for 50 minutes
            return creds
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-access-token", f"--account={account_email}"],
            stderr=subprocess.DEVNULL,
            timeout=10
        ).decode("utf-8").strip()
        if token:
            from google.oauth2.credentials import Credentials
            creds = Credentials(token)
            _CACHED_BQ_CREDS[account_email] = (creds, now)
            return creds
    except Exception:
        pass
    return None

@lru_cache(maxsize=16)
def _get_bq_client(project_id: Optional[str] = None, location: Optional[str] = None):
    try:
        from google.cloud import bigquery
        proj = project_id or TARGET_BQ_PROJECT_ID or None
        loc = location or TARGET_BQ_LOCATION or None
        creds = _get_credentials_for_account(TARGET_BQ_ACCOUNT) if TARGET_BQ_ACCOUNT else None
        if creds:
            return bigquery.Client(project=proj, credentials=creds, location=loc)
        return bigquery.Client(project=proj, location=loc)
    except Exception:
        return None

def _sanitize_identifier(name: str) -> str:
    """Strips any non-alphanumeric characters except underscores and hyphens."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "", name)

# ==============================================================================
# GENERIC BIGQUERY EXECUTION PRIMITIVES
# ==============================================================================

def run_bq_query(sql_query: str, project_id: Optional[str] = None, location: Optional[str] = None, max_results: int = 50) -> str:
    """
    Dynamic BigQuery SQL Execution Primitive.
    Executes any SQL query against BigQuery (including dataset and regional INFORMATION_SCHEMA views).
    
    Args:
        sql_query: Valid BigQuery standard SQL query string.
        project_id: Optional GCP project ID override.
        location: Optional BigQuery location/region (e.g. 'US', 'EU', 'us-central1').
        max_results: Maximum rows to return (default: 50).
    """
    pid = project_id or GCP_PROJECT_ID
    target_loc = location
    if not target_loc:
        if "`region-us`" in sql_query.lower():
            target_loc = "US"
        elif "`region-eu`" in sql_query.lower():
            target_loc = "EU"
        elif "`region-" in sql_query.lower():
            match = re.search(r"`region-([a-zA-Z0-9_-]+)`", sql_query, re.IGNORECASE)
            target_loc = match.group(1) if match else GCP_LOCATION
        else:
            target_loc = GCP_LOCATION

    client = _get_bq_client(pid, target_loc)
    if not client:
        return f"### ⚡ BigQuery SQL Query (Client Offline / Unconfigured):\n```sql\n{sql_query.strip()}\n```"
    
    try:
        query_job = client.query(sql_query)
        results = [dict(row) for row in query_job.result(max_results=max_results)]
        if not results:
            return f"### ⚡ BigQuery Query Result: 0 rows returned."
        return f"### ⚡ BigQuery Query Result ({len(results)} rows):\n```json\n{json.dumps(results, indent=2, default=str)}\n```"
    except Exception as e:
        return f"### ⚠️ BigQuery Query Error:\n```sql\n{sql_query.strip()}\n```\nError: {type(e).__name__}: {str(e)}"


# ==============================================================================
# PILLAR 3: BIGQUERY INTEGRATION & DATABASE OPTIMIZATION (Tasks 21 to 30)
# ==============================================================================

DEFAULT_DATASET = os.getenv("TARGET_BIGQUERY_DATASET") or os.getenv("BIGQUERY_DATASET", "the_look_ca")

def _resolve_table_id(table_id: str, project_id: Optional[str] = None) -> str:
    cleaned = table_id.strip("`'\" \t\n")
    parts = cleaned.split(".")
    pid = project_id or GCP_PROJECT_ID
    if len(parts) == 1:
        return f"{pid}.{DEFAULT_DATASET}.{parts[0]}" if pid else f"{DEFAULT_DATASET}.{parts[0]}"
    elif len(parts) == 2:
        return f"{pid}.{cleaned}" if pid else cleaned
    return cleaned

def audit_partition_cluster_filters(table_id: str, project_id: Optional[str] = None, model_name: Optional[str] = None) -> str:
    """
    Task 21: Partition & Cluster Alignment.
    Audits table partitioning and clustering layout to ensure LookML views enforce `conditionally_filter` or `require_partition_filter: yes`.
    """
    pid = project_id or GCP_PROJECT_ID
    client = _get_bq_client(pid, GCP_LOCATION)
    resolved_id = _resolve_table_id(table_id, pid)
    if not client:
        return f"Ensure LookML views for table `{resolved_id}` enforce `conditionally_filter` or `require_partition_filter: yes`."
    
    try:
        table_ref = client.get_table(resolved_id)
        p_info = None
        if table_ref.time_partitioning:
            p_info = {
                "type": str(table_ref.time_partitioning.type_),
                "field": table_ref.time_partitioning.field,
                "require_partition_filter": table_ref.require_partition_filter
            }
        
        c_fields = list(table_ref.clustering_fields) if table_ref.clustering_fields else []
        
        report = {
            "table_id": resolved_id,
            "partitioning": p_info or "UNPARTITIONED",
            "clustering": c_fields or "NONE",
            "action_required": "Enforce partition filter in LookML view" if not (p_info and p_info.get("require_partition_filter")) else "HEALTHY"
        }
        return f"### 🎯 Partition & Clustering Alignment (`{resolved_id}`):\n```json\n{json.dumps(report, indent=2)}\n```"
    except Exception as e:
        return f"### ⚠️ BigQuery Table Partition & Layout Inspection Failed (`{resolved_id}`):\n{type(e).__name__}: {str(e)}"



def audit_datagroup_sync(project_id: Optional[str] = None, region: Optional[str] = None, hours: int = 24, model_name: Optional[str] = None) -> str:
    """
    Task 25: Caching Strategies (Datagroups).
    Queries BigQuery INFORMATION_SCHEMA to map warehouse ELT completion timestamps to Looker datagroup triggers.
    """
    pid = project_id or GCP_PROJECT_ID
    raw_reg = region or (GCP_LOCATION.split("-")[0] if GCP_LOCATION else "us")
    reg = _sanitize_identifier(raw_reg) or "us"
    target_loc = "US" if reg.lower() == "us" else ("EU" if reg.lower() == "eu" else reg)
    safe_hours = max(1, min(int(hours), 168))
    client = _get_bq_client(pid, target_loc)
    
    schema_table = f"`{pid}.region-{reg}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`" if pid else f"`region-{reg}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`"
    query = f"""
    SELECT
      project_id,
      job_id,
      creation_time,
      end_time,
      TIMESTAMP_DIFF(end_time, creation_time, SECOND) as duration_seconds,
      statement_type
    FROM
      {schema_table}
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {safe_hours} HOUR)
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
    Audits bytes scanned, GB billed, and on-demand costs for all queries executed by Looker using BigQuery INFORMATION_SCHEMA and BigQuery Job Labels.
    """
    pid = project_id or GCP_PROJECT_ID
    raw_reg = region or (GCP_LOCATION.split("-")[0] if GCP_LOCATION else "us")
    reg = _sanitize_identifier(raw_reg) or "us"
    target_loc = "US" if reg.lower() == "us" else ("EU" if reg.lower() == "eu" else reg)
    safe_hours = max(1, min(int(hours), 168))
    client = _get_bq_client(pid, target_loc)
    
    filter_clause = "(EXISTS (SELECT 1 FROM UNNEST(labels) WHERE key LIKE 'looker-context%') OR query LIKE '%Looker%' OR query LIKE '%-- Looker%')"
    if model_name:
        clean_model = _sanitize_identifier(model_name)
        if clean_model:
            filter_clause += f" AND (query LIKE '%{clean_model}%' OR query LIKE '%lookml_model: {clean_model}%')"

    schema_table = f"`{pid}.region-{reg}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`" if pid else f"`region-{reg}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`"
    query = f"""
    SELECT
      TIMESTAMP_TRUNC(creation_time, HOUR) as hour_window,
      COUNT(DISTINCT job_id) as looker_queries_count,
      ROUND(SUM(total_bytes_billed) / (1024 * 1024 * 1024), 2) as total_gb_billed,
      ROUND((SUM(total_bytes_billed) / POW(10, 12)) * 6.25, 4) as estimated_cost_usd,
      ROUND(SUM(total_slot_ms) / 1000, 2) as total_slot_seconds
    FROM
      {schema_table}
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {safe_hours} HOUR)
      AND job_type = 'QUERY'
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
        return f"### 💰 Looker BigQuery Cost & Bytes Billed (Past {safe_hours}h - {scope_str}):\n```json\n{json.dumps(results, indent=2, default=str)}\n```"
    except Exception as e:
        return f"Cost audit query:\n```sql\n{query}\n```\n*(Execution note: {str(e)})*"


def get_looker_bigquery_job_correlations(
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    hours: int = 24,
    min_gb_billed: float = 0.0,
    model_name: Optional[str] = None,
    limit: int = 25
) -> str:
    """
    Correlates BigQuery query execution telemetry with Looker System Activity using BigQuery Job Labels.
    Extracts looker-context-user_id, looker-context-history_slug, and looker-context-instance_slug
    from INFORMATION_SCHEMA.JOBS_BY_PROJECT structured metadata without regex parsing overhead.
    """
    pid = project_id or GCP_PROJECT_ID
    raw_reg = region or (GCP_LOCATION.split("-")[0] if GCP_LOCATION else "us")
    reg = _sanitize_identifier(raw_reg) or "us"
    target_loc = "US" if reg.lower() == "us" else ("EU" if reg.lower() == "eu" else reg)
    safe_hours = max(1, min(int(hours), 168))
    client = _get_bq_client(pid, target_loc)

    filter_clause = "job_type = 'QUERY' AND EXISTS (SELECT 1 FROM UNNEST(labels) WHERE key LIKE 'looker-context%')"
    if min_gb_billed > 0:
        filter_clause += f" AND total_bytes_billed >= {int(min_gb_billed * (1024**3))}"
    if model_name:
        clean_model = _sanitize_identifier(model_name)
        if clean_model:
            filter_clause += f" AND (query LIKE '%{clean_model}%' OR query LIKE '%lookml_model: {clean_model}%')"

    schema_table = f"`{pid}.region-{reg}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`" if pid else f"`region-{reg}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`"
    query = f"""
    SELECT
      project_id,
      job_id,
      creation_time,
      user_email,
      -- Structured Looker Job Labels
      (SELECT value FROM UNNEST(labels) WHERE key = 'looker-context-user_id') AS looker_user_id,
      (SELECT value FROM UNNEST(labels) WHERE key = 'looker-context-history_slug') AS looker_history_slug,
      (SELECT value FROM UNNEST(labels) WHERE key = 'looker-context-instance_slug') AS looker_instance_slug,
      -- Performance & Cost metrics
      total_bytes_billed,
      ROUND(total_bytes_billed / (1024 * 1024 * 1024), 2) AS gb_billed,
      ROUND((total_bytes_billed / POW(10, 12)) * 6.25, 4) AS estimated_cost_usd,
      total_slot_ms,
      ROUND(total_slot_ms / 1000, 2) AS total_slot_seconds,
      query
    FROM
      {schema_table}
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {safe_hours} HOUR)
      AND {filter_clause}
    ORDER BY
      total_bytes_billed DESC
    LIMIT {limit};
    """

    if not client:
        return f"### ⚡ BigQuery Looker Job Label Correlation SQL:\n```sql\n{query}\n```"

    try:
        query_job = client.query(query)
        results = [dict(row) for row in query_job.result()]
        return f"### ⚡ Looker-BigQuery Job Label Correlations ({len(results)} Found - Past {safe_hours}h):\n```json\n{json.dumps(results, indent=2, default=str)}\n```"
    except Exception as e:
        return f"Correlation query error:\n```sql\n{query}\n```\n*(Execution note: {str(e)})*"

def audit_bq_slots(project_id: Optional[str] = None, region: Optional[str] = None, hours: int = 24, model_name: Optional[str] = None) -> str:
    """Audits slot consumption and reservation ceilings."""
    pid = project_id or GCP_PROJECT_ID
    raw_reg = region or (GCP_LOCATION.split("-")[0] if GCP_LOCATION else "us")
    reg = _sanitize_identifier(raw_reg) or "us"
    target_loc = "US" if reg.lower() == "us" else ("EU" if reg.lower() == "eu" else reg)
    client = _get_bq_client(pid, target_loc)
    
    schema_table = f"`{pid}.region-{reg}.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT`" if pid else f"`region-{reg}.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT`"
    query = f"""
    SELECT
      TIMESTAMP_TRUNC(period_start, HOUR) as hour_window,
      ROUND(AVG(period_slot_ms) / 1000, 2) as avg_slots,
      ROUND(MAX(period_slot_ms) / 1000, 2) as peak_slots
    FROM
      {schema_table}
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
        target_dataset = f"{pid}.{dataset_id}" if pid and "." not in dataset_id else dataset_id
        tables = [t.table_id for t in client.list_tables(target_dataset)]
        return f"### Tables in `{target_dataset}`:\n```json\n{json.dumps(tables, indent=2)}\n```"
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
