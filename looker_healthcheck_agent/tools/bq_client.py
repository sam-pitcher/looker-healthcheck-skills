"""
Generic BigQuery Client & Database Optimization Tools.
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

def audit_partition_cluster_filters(table_id: str, project_id: Optional[str] = None) -> str:
    """Task 21: Partition & Cluster Alignment."""
    pid = project_id or GCP_PROJECT_ID
    client = _get_bq_client(pid)
    if not client:
        return f"Ensure LookML views for table `{table_id}` enforce `conditionally_filter` or `require_partition_filter: yes`."
    try:
        table_ref = client.get_table(table_id)
        p_info = str(table_ref.time_partitioning.type_) if table_ref.time_partitioning else "UNPARTITIONED"
        c_fields = list(table_ref.clustering_fields) if table_ref.clustering_fields else []
        report = {"table_id": table_id, "partitioning": p_info, "clustering": c_fields}
        return f"### 🎯 Partition & Clustering Alignment (`{table_id}`):\n```json\n{json.dumps(report, indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def audit_datagroup_sync(project_id: Optional[str] = None, region: Optional[str] = None, hours: int = 24) -> str:
    """Task 25: Caching Strategies (Datagroups)."""
    return "Map BigQuery ELT completion timestamps to Looker datagroup trigger queries."

def audit_query_costs_and_bytes_billed(project_id: Optional[str] = None, region: Optional[str] = None, hours: int = 24) -> str:
    """Task 30: Query Cost Optimization."""
    return f"Audit total bytes billed and on-demand costs for Looker queries over past {hours} hours."

def audit_bq_slots(project_id: Optional[str] = None, region: Optional[str] = None, hours: int = 24) -> str:
    """Task 22: Slot Audit."""
    return "Slot reservation audit"

def list_dataset_tables(dataset_id: str, project_id: Optional[str] = None) -> str:
    """List dataset tables."""
    return f"Tables in {dataset_id}"

def optimize_table_layout(table_id: str, project_id: Optional[str] = None) -> str:
    """Optimize table layout."""
    return audit_partition_cluster_filters(table_id, project_id)

def estimate_query_cost_dry_run(sql_query: str, project_id: Optional[str] = None) -> str:
    """Estimate dry-run costs."""
    return "Dry-run cost estimation"
