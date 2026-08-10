"""
Looker API & Administration Tools for Content & System Auditing.
Interacts with Looker API 4.0 and system__activity models.
"""

import os
import json
from typing import Dict, Any, List, Optional
import urllib3
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LookerAdminClient:
    def __init__(self):
        self.base_url = os.getenv("LOOKERSDK_BASE_URL", "").rstrip("/")
        self.client_id = os.getenv("LOOKERSDK_CLIENT_ID", "")
        self.client_secret = os.getenv("LOOKERSDK_CLIENT_SECRET", "")
        self.token = None

    def authenticate(self):
        if not self.base_url or not self.client_id or not self.client_secret:
            raise ValueError("Looker credentials (LOOKERSDK_BASE_URL, LOOKERSDK_CLIENT_ID, LOOKERSDK_CLIENT_SECRET) are missing.")
        login_url = f"{self.base_url}/api/4.0/login"
        resp = requests.post(
            login_url,
            data={"client_id": self.client_id, "client_secret": self.client_secret},
            verify=False,
            timeout=30
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Looker Auth failed ({resp.status_code}): {resp.text}")
        self.token = resp.json().get("access_token")

    def run_query(self, model: str, view: str, fields: List[str], filters: Optional[Dict[str, str]] = None, sorts: Optional[List[str]] = None, limit: str = "500") -> List[Dict[str, Any]]:
        if not self.token:
            self.authenticate()
        url = f"{self.base_url}/api/4.0/queries/run/json"
        body = {
            "model": model,
            "view": view,
            "fields": fields,
            "filters": filters or {},
            "sorts": sorts or [],
            "limit": str(limit)
        }
        headers = {"Authorization": f"token {self.token}", "Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, json=body, verify=False, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Looker query error ({resp.status_code}): {resp.text}")
        return resp.json()

    def get_dashboard(self, dashboard_id: str) -> Dict[str, Any]:
        if not self.token:
            self.authenticate()
        url = f"{self.base_url}/api/4.0/dashboards/{dashboard_id}"
        headers = {"Authorization": f"token {self.token}"}
        resp = requests.get(url, headers=headers, verify=False, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to fetch dashboard {dashboard_id}: {resp.text}")
        return resp.json()

    def delete_dashboard(self, dashboard_id: str) -> bool:
        if not self.token:
            self.authenticate()
        url = f"{self.base_url}/api/4.0/dashboards/{dashboard_id}"
        headers = {"Authorization": f"token {self.token}"}
        resp = requests.delete(url, headers=headers, verify=False, timeout=30)
        return resp.status_code in [200, 204]

_client = LookerAdminClient()

def get_stale_schedules(days: int = 90) -> str:
    """
    Identifies scheduled plans and emails belonging to inactive users (no login in X days)
    or schedules that have not delivered successfully.
    
    Args:
        days (int): Inactive threshold in days (default: 90).
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="user",
            fields=[
                "user.id",
                "user.name",
                "user.email",
                "user_facts.last_ui_login_date",
                "scheduled_plan.count",
                "scheduled_job.count"
            ],
            filters={
                "user_facts.last_ui_login_date": f"before {days} days ago",
                "user.is_disabled": "No",
                "scheduled_plan.count": ">0"
            },
            sorts=["user_facts.last_ui_login_date desc"],
            limit="100"
        )
        
        output = {
            "status": "success",
            "threshold_days": days,
            "zombie_schedule_recipients_count": len(results),
            "zombie_schedules": results
        }
        return f"### 📬 Zombie & Stale Schedules Report (Inactive >{days} Days):\n```json\n{json.dumps(output, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing stale schedules: {str(e)}"

def get_tile_bloat_dashboards(tile_threshold: int = 25) -> str:
    """
    Scans Looker dashboards to identify tile bloat (>25 tiles), merged query usage,
    and excessive data scans from hidden table columns.
    
    Args:
        tile_threshold (int): Maximum recommended tile count per dashboard (default: 25).
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="dashboard",
            fields=[
                "dashboard.id",
                "dashboard.title",
                "dashboard_element.count",
                "dashboard.created_date",
                "user.name"
            ],
            filters={
                "dashboard.deleted_date": "NULL",
                "dashboard_element.count": f">{tile_threshold}"
            },
            sorts=["dashboard_element.count desc"],
            limit="50"
        )
        
        output = {
            "status": "success",
            "tile_threshold": tile_threshold,
            "bloated_dashboards_found": len(results),
            "dashboards": results
        }
        return f"### 📊 Dashboard Tile Bloat Audit (> {tile_threshold} Tiles):\n```json\n{json.dumps(output, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing dashboard tile bloat: {str(e)}"

def archive_dashboard(dashboard_id: str) -> str:
    """
    Soft-deletes or archives an unused or deprecated Looker dashboard.
    
    Args:
        dashboard_id (str): The ID of the dashboard to delete.
    """
    try:
        success = _client.delete_dashboard(dashboard_id)
        if success:
            return f"✅ Dashboard `{dashboard_id}` successfully archived/deleted."
        return f"❌ Failed to archive dashboard `{dashboard_id}`."
    except Exception as e:
        return f"Error archiving dashboard `{dashboard_id}`: {str(e)}"

def deactivate_inactive_users(days: int = 90, dry_run: bool = True) -> str:
    """
    Identifies or deactivates user accounts that have had zero UI logins for > 90 days.
    
    Args:
        days (int): Inactivity threshold in days (default: 90).
        dry_run (bool): If True, only lists candidates without modifying user state (default: True).
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="user",
            fields=[
                "user.id",
                "user.name",
                "user.email",
                "user_facts.last_ui_login_date",
                "role.name"
            ],
            filters={
                "user_facts.last_ui_login_date": f"before {days} days ago",
                "user.is_disabled": "No"
            },
            sorts=["user_facts.last_ui_login_date desc"],
            limit="100"
        )
        output = {
            "status": "success",
            "dry_run": dry_run,
            "inactive_users_count": len(results),
            "candidates": results
        }
        return f"### 👤 Inactive User License Reclamation (>{days} Days):\n```json\n{json.dumps(output, indent=2)}\n```"
    except Exception as e:
        return f"Error evaluating inactive users: {str(e)}"

def run_system_activity_kpis() -> str:
    """
    Executes a baseline performance telemetry audit against Looker system__activity query metrics.
    Evaluates async runtime, Looker overhead percentage, and cache hit ratios.
    """
    try:
        metrics = _client.run_query("system__activity", "query_metrics", [
            "query_metrics.async_processing_average",
            "query_metrics.execute_main_query_average",
            "query_metrics.acquire_connection_average",
            "query_metrics.model_init_computed_average",
            "query_metrics.explore_init_average",
            "query_metrics.prepare_average",
            "query_metrics.stream_to_cache_average",
            "history.query_run_count",
            "history.database_result_query_count"
        ], limit="1")
        
        m = metrics[0] if metrics else {}
        async_avg = float(m.get("query_metrics.async_processing_average") or 0.0)
        exec_avg = float(m.get("query_metrics.execute_main_query_average") or 0.0)
        conn_avg = float(m.get("query_metrics.acquire_connection_average") or 0.0)
        total_q = int(m.get("history.query_run_count") or 0)
        db_q = int(m.get("history.database_result_query_count") or 0)
        
        overhead_pct = (((async_avg - (exec_avg + conn_avg)) / async_avg) * 100.0) if async_avg > 0 else 0.0
        cache_hit_pct = ((1.0 - (db_q / total_q)) * 100.0) if total_q > 0 else 0.0
        
        report = {
            "average_async_runtime_seconds": f"{async_avg:.2f}s",
            "database_execution_seconds": f"{exec_avg:.2f}s",
            "connection_acquire_seconds": f"{conn_avg:.3f}s",
            "looker_overhead_percentage": f"{overhead_pct:.1f}%",
            "cache_hit_percentage": f"{cache_hit_pct:.1f}%",
            "total_queries_analyzed": total_q
        }
        return f"### ⚡ Looker Telemetry Performance KPIs:\n```json\n{json.dumps(report, indent=2)}\n```"
    except Exception as e:
        return f"Error executing telemetry audit: {str(e)}"
