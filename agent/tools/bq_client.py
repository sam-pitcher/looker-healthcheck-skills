"""
BigQuery Client & Compute Optimization Tools.
Audits slot reservations, INFORMATION_SCHEMA queries, table partitioning/clustering, and dry-run query costs.
"""

import os
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "sampitcher-playground")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

def _get_bq_client(project_id: Optional[str] = None):
    try:
        from google.cloud import bigquery
        proj = project_id or GCP_PROJECT_ID
        return bigquery.Client(project=proj, location=GCP_LOCATION)
    except Exception as e:
        return None

def audit_bq_slots(project_id: Optional[str] = None, hours: int = 24) -> str:
    """
    Audits BigQuery slot consumption and reservation ceilings using INFORMATION_SCHEMA.
    Detects if queries suffered slot starvation during peak dashboard refresh hours.
    
    Args:
        project_id (str, optional): GCP project ID to audit.
        hours (int): Number of past hours to analyze (default: 24).
    """
    pid = project_id or GCP_PROJECT_ID
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
      `region-{GCP_LOCATION.split('-')[0]}`.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT
    WHERE
      period_start >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
    GROUP BY 1, 2
    ORDER BY hour_window DESC
    LIMIT 25;
    """
    
    if not client:
        return (
            f"### ⚡ BigQuery Slot Audit Recipe (Project: `{pid}`):\n"
            f"*BigQuery Client offline or credentials missing. Run the following diagnostic query in BigQuery Studio:*\n\n"
            f"```sql\n{query}\n```\n\n"
            f"**Remediation Guidance:**\n"
            f"- If `peak_slots_consumed` hits the reservation ceiling (e.g. 500 or 1000 slots), queries will queue.\n"
            f"- Establish a dedicated **Looker BI Reservation** separate from heavy ETL/PDT builds.\n"
            f"- Configure **PDT Billing Project Override** in Looker Connection settings."
        )

    try:
        query_job = client.query(query)
        results = [dict(row) for row in query_job.result()]
        output = {
            "status": "success",
            "project_id": pid,
            "hours_analyzed": hours,
            "metrics": results
        }
        return f"### ⚡ BigQuery Slot Ceiling & Starvation Audit ({pid}):\n```json\n{json.dumps(output, indent=2, default=str)}\n```"
    except Exception as e:
        return (
            f"### ⚡ BigQuery Slot Audit SQL (Project: `{pid}`):\n"
            f"*Query failed via API ({str(e)}). Run directly in BigQuery Studio:*\n\n"
            f"```sql\n{query}\n```"
        )

def optimize_table_layout(table_id: str, project_id: Optional[str] = None) -> str:
    """
    Analyzes a BigQuery table's partitioning and clustering layout and returns optimization recommendations.
    
    Args:
        table_id (str): Full table identifier (e.g. 'my_project.dataset.events' or 'dataset.orders').
        project_id (str, optional): Target GCP project ID.
    """
    pid = project_id or GCP_PROJECT_ID
    client = _get_bq_client(pid)
    
    if not client:
        return (
            f"### 🎯 BigQuery Table Layout Optimizer for `{table_id}`:\n"
            f"**Recommended PSO Schema Strategy:**\n"
            f"1. **Partitioning**: Ensure table is partitioned **Daily** on event/creation date (e.g. `created_date`) rather than Monthly.\n"
            f"2. **Clustering**: Add clustering keys ordered by filter frequency: `[high_cardinality_filter_col, join_foreign_key]` (e.g. `cluster_by = ['status', 'user_id']`).\n"
            f"3. **LookML Alignment**: Ensure the LookML view declares `partition_keys: [\"created_date\"]` with `require_partition_filter: yes`."
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
            assessment.append("🔴 Table is UNPARTITIONED. Full table scans will occur on every query.")
        elif partitioning_info.get("type") == "MONTH":
            assessment.append("🟡 Table uses MONTHLY partitioning. Switch to DAILY partitioning for granular pruning.")
        else:
            assessment.append("🟢 Table uses DAILY partitioning.")

        if not clustering_fields:
            assessment.append("🔴 Table has NO CLUSTERING. Queries filtering on user_id, status, or category cannot prune data blocks.")
        else:
            assessment.append(f"🟢 Table is clustered on: {clustering_fields}")

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
                "Enforce `require_partition_filter: yes` in LookML view to prevent inadvertent full table scans.",
                "For high-volume dashboard tiles, implement Aggregate Awareness (aggregate_table) in the LookML model."
            ]
        }
        return f"### 🎯 BigQuery Table Structure Analysis (`{table_id}`):\n```json\n{json.dumps(analysis, indent=2)}\n```"
    except Exception as e:
        return f"Error analyzing table `{table_id}`: {str(e)}"

def estimate_query_cost_dry_run(sql_query: str, project_id: Optional[str] = None) -> str:
    """
    Executes a BigQuery dry-run to estimate the scanned data volume (MB/GB) and on-demand query cost.
    
    Args:
        sql_query (str): The raw SQL query to test.
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
        # Assuming standard on-demand pricing: $6.25 per TB ($0.00625 per GB)
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
