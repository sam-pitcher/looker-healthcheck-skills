"""
Generic BigQuery Client & Compute Optimization Tools.
Audits slot reservations, INFORMATION_SCHEMA queries, table partitioning/clustering, and dry-run costs across ANY dataset.
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

def audit_bq_slots(project_id: Optional[str] = None, region: Optional[str] = None, hours: int = 24) -> str:
    """
    Audits BigQuery slot consumption and reservation ceilings using INFORMATION_SCHEMA.
    Detects slot starvation during peak dashboard refresh hours.
    
    Args:
        project_id (str, optional): Target GCP project ID.
        region (str, optional): BigQuery region (e.g. 'us', 'us-central1', 'eu').
        hours (int): Number of past hours to analyze (default: 24).
    """
    pid = project_id or GCP_PROJECT_ID
    reg = region or GCP_LOCATION.split("-")[0] if GCP_LOCATION else "us"
    client = _get_bq_client(pid)
    
    query = f"""
    SELECT
      TIMESTAMP_TRUNC(period_start, HOUR) as hour_window,
      job_type,
      COUNT(DISTINCT job_id) as total_jobs,
      ROUND(AVG(period_slot_ms) / 1000, 2) as avg_slots_consumed,
      ROUND(MAX(period_slot_ms) / 1000, 2) as peak_slots_consumed,
      SUM(IF(error_result.reason = 'rateLimitExceeded', 1, 0)) as slot_limit_errors
    FROM
      `region-{reg}`.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT
    WHERE
      period_start >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
    GROUP BY 1, 2
    ORDER BY hour_window DESC
    LIMIT 25;
    """
    
    if not client:
        return (
            f"### ⚡ BigQuery Slot Audit (Project: `{pid or 'current'}`):\n"
            f"*Run the following diagnostic query in BigQuery Studio:*\n\n"
            f"```sql\n{query}\n```\n\n"
            f"**Remediation Guidance:**\n"
            f"- If `peak_slots_consumed` approaches reservation ceilings, create a dedicated BI reservation.\n"
            f"- Configure **PDT Billing Project Override** in Looker Connection settings."
        )

    try:
        query_job = client.query(query)
        results = [dict(row) for row in query_job.result()]
        output = {
            "status": "success",
            "project_id": pid,
            "region": reg,
            "hours_analyzed": hours,
            "metrics": results
        }
        return f"### ⚡ BigQuery Slot Ceiling & Starvation Audit ({pid}):\n```json\n{json.dumps(output, indent=2, default=str)}\n```"
    except Exception as e:
        return f"### ⚡ BigQuery Slot Audit SQL:\n```sql\n{query}\n```\n*(Execution note: {str(e)})*"

def list_dataset_tables(dataset_id: str, project_id: Optional[str] = None) -> str:
    """
    Discovers and audits all tables within a BigQuery dataset (rows, sizes, partitioning, and clustering).
    
    Args:
        dataset_id (str): Target BigQuery dataset name.
        project_id (str, optional): Target GCP project ID.
    """
    pid = project_id or GCP_PROJECT_ID
    client = _get_bq_client(pid)
    if not client:
        return f"BigQuery Client unavailable to list tables for dataset `{dataset_id}`."
    
    try:
        tables = list(client.list_tables(dataset_id))
        summaries = []
        for t in tables[:50]:
            table_obj = client.get_table(t.reference)
            p_type = table_obj.time_partitioning.type_ if table_obj.time_partitioning else None
            p_field = table_obj.time_partitioning.field if table_obj.time_partitioning else None
            summaries.append({
                "table_id": table_obj.table_id,
                "num_rows": table_obj.num_rows,
                "size_mb": round((table_obj.num_bytes or 0) / (1024 * 1024), 2),
                "partition_type": p_type,
                "partition_field": p_field,
                "clustering_fields": list(table_obj.clustering_fields) if table_obj.clustering_fields else []
            })
        return f"### 📊 Tables in Dataset `{dataset_id}`:\n```json\n{json.dumps(summaries, indent=2)}\n```"
    except Exception as e:
        return f"Error listing tables in dataset `{dataset_id}`: {str(e)}"

def optimize_table_layout(table_id: str, project_id: Optional[str] = None) -> str:
    """
    Analyzes a BigQuery table's partitioning and clustering layout and returns actionable schema recommendations.
    
    Args:
        table_id (str): Full table identifier (e.g. 'dataset.table_name' or 'project.dataset.table_name').
        project_id (str, optional): Target GCP project ID.
    """
    pid = project_id or GCP_PROJECT_ID
    client = _get_bq_client(pid)
    
    if not client:
        return (
            f"### 🎯 BigQuery Table Optimization Strategy for `{table_id}`:\n"
            f"1. **Partitioning**: Ensure table is partitioned **Daily** on creation/event date.\n"
            f"2. **Clustering**: Cluster on high-frequency UI filter columns first, foreign keys second.\n"
            f"3. **LookML Filter Enforcement**: Add `always_filter` or `require_partition_filter: yes` in LookML view."
        )

    try:
        table_ref = client.get_table(table_id)
        partitioning_info = None
        if table_ref.time_partitioning:
            partitioning_info = {
                "type": str(table_ref.time_partitioning.type_),
                "field": table_ref.time_partitioning.field,
                "expiration_ms": table_ref.time_partitioning.expiration_ms,
                "require_partition_filter": table_ref.require_partition_filter
            }

        clustering_fields = list(table_ref.clustering_fields) if table_ref.clustering_fields else []

        assessment = []
        if not partitioning_info:
            assessment.append("🔴 UNPARTITIONED: Full table scan on every query.")
        elif partitioning_info.get("type") == "MONTH":
            assessment.append("🟡 MONTHLY PARTITIONING: Migrate to DAILY partitioning for granular block pruning.")
        else:
            assessment.append("🟢 DAILY PARTITIONING: Healthy layout.")

        if not clustering_fields:
            assessment.append("🔴 NO CLUSTERING: Block pruning disabled for high-cardinality filters.")
        else:
            assessment.append(f"🟢 CLUSTERED: {clustering_fields}")

        analysis = {
            "table_id": table_id,
            "num_rows": table_ref.num_rows,
            "total_bytes": table_ref.num_bytes,
            "total_megabytes": round((table_ref.num_bytes or 0) / (1024 * 1024), 2),
            "partitioning": partitioning_info,
            "clustering": clustering_fields,
            "assessment": assessment,
            "recommendations": [
                "Cluster on high-cardinality UI filter columns first, foreign keys second.",
                "Enforce `require_partition_filter: yes` in LookML view to prevent unpruned scans.",
                "For high-volume dashboard tiles, implement Looker Aggregate Awareness (aggregate_table)."
            ]
        }
        return f"### 🎯 BigQuery Table Structure Analysis (`{table_id}`):\n```json\n{json.dumps(analysis, indent=2)}\n```"
    except Exception as e:
        return f"Error analyzing table `{table_id}`: {str(e)}"

def estimate_query_cost_dry_run(sql_query: str, project_id: Optional[str] = None) -> str:
    """
    Executes a BigQuery dry-run to estimate the scanned data volume (MB/GB) and on-demand query cost.
    
    Args:
        sql_query (str): The raw SQL query string to dry-run.
        project_id (str, optional): Target GCP project ID.
    """
    pid = project_id or GCP_PROJECT_ID
    client = _get_bq_client(pid)
    
    if not client:
        return f"BigQuery Client offline. Query length: {len(sql_query)} characters."

    try:
        from google.cloud import bigquery
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        query_job = client.query(sql_query, job_config=job_config)
        
        bytes_scanned = query_job.total_bytes_processed
        mb_scanned = bytes_scanned / (1024 * 1024)
        gb_scanned = bytes_scanned / (1024 * 1024 * 1024)
        estimated_cost_usd = gb_scanned * 0.00625
        
        report = {
            "bytes_scanned": bytes_scanned,
            "megabytes_scanned": round(mb_scanned, 2),
            "gigabytes_scanned": round(gb_scanned, 4),
            "estimated_cost_usd": f"${estimated_cost_usd:.5f}",
            "verdict": "HEAVY SCAN (>1GB)" if gb_scanned > 1.0 else "EFFICIENT SCAN (<1GB)"
        }
        return f"### 💰 BigQuery Query Dry-Run Cost Estimate:\n```json\n{json.dumps(report, indent=2)}\n```"
    except Exception as e:
        return f"Error executing BigQuery dry-run: {str(e)}"
