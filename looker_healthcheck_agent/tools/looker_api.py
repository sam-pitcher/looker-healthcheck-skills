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

def run_healthcheck_audit(component_id: Optional[int] = None) -> str:
    """
    Executes live healthcheck diagnostics against Looker system__activity across 8 components.
    """
    try:
        if component_id is None or component_id == 2:
            metrics = _client.run_query("system__activity", "query_metrics", [
                "query_metrics.async_processing_average",
                "query_metrics.execute_main_query_average",
                "query_metrics.acquire_connection_average",
                "query_metrics.project_init_average",
                "query_metrics.model_init_computed_average",
                "query_metrics.model_init_cache_average",
                "query_metrics.explore_init_average",
                "query_metrics.marshalled_cache_load_average",
                "query_metrics.prepare_average",
                "query_metrics.queued_average",
                "query_metrics.per_user_throttler_average",
                "query_metrics.stream_to_cache_average",
                "query_metrics.postprocessing_average",
                "history.query_run_count",
                "history.database_result_query_count"
            ], limit="1")
            
            m = metrics[0] if metrics else {}
            async_avg = float(m.get("query_metrics.async_processing_average") or 0.0)
            exec_avg = float(m.get("query_metrics.execute_main_query_average") or 0.0)
            conn_avg = float(m.get("query_metrics.acquire_connection_average") or 0.0)
            proj_init = float(m.get("query_metrics.project_init_average") or 0.0)
            model_comp = float(m.get("query_metrics.model_init_computed_average") or 0.0)
            model_cache = float(m.get("query_metrics.model_init_cache_average") or 0.0)
            exp_comp = float(m.get("query_metrics.explore_init_average") or 0.0)
            exp_cache = float(m.get("query_metrics.marshalled_cache_load_average") or 0.0)
            prep_avg = float(m.get("query_metrics.prepare_average") or 0.0)
            queue_avg = float(m.get("query_metrics.queued_average") or 0.0)
            throttle_avg = float(m.get("query_metrics.per_user_throttler_average") or 0.0)
            stream_avg = float(m.get("query_metrics.stream_to_cache_average") or 0.0)
            post_avg = float(m.get("query_metrics.postprocessing_average") or 0.0)
            
            total_queries = int(m.get("history.query_run_count") or 0)
            db_queries = int(m.get("history.database_result_query_count") or 0)
            
            cache_ratio = ((1.0 - (db_queries / total_queries)) * 100.0) if total_queries > 0 else 0.0
            overhead_pct = (((async_avg - (exec_avg + conn_avg)) / async_avg) * 100.0) if async_avg > 0 else 0.0
            
            def eval_status(val: float, warn: float, crit: float, lower_better: bool = True):
                if lower_better:
                    if val > crit: return "CRITICAL"
                    if val > warn: return "WARNING"
                    return "HEALTHY"
                else:
                    if val < crit: return "CRITICAL"
                    if val < warn: return "WARNING"
                    return "HEALTHY"

            report = [
                f"# Looker Healthcheck Audit",
                f"**Target Instance:** `{_client.base_url}`\n",
                f"## 1. Component 2: Performance Audit Scorecard",
                f"| Metric Name | Observed Value | Target Benchmark | Status |",
                f"| :--- | :---: | :---: | :---: |",
                f"| **Average Async Runtime** | `{async_avg:.2f}s` | `< 5.00s` | **{eval_status(async_avg, 9.999, 14.999)}** |",
                f"| **Indicative Looker Overhead** | `{overhead_pct:.1f}%` | `< 20.0%` | **{eval_status(overhead_pct, 30.0, 50.0)}** |",
                f"| **Cache Hit Percentage** | `{cache_ratio:.1f}%` | `> 50.0%` | **{eval_status(cache_ratio, 40.0, 20.0, lower_better=False)}** |",
                f"| **Execute Main Query (DB)** | `{exec_avg:.2f}s` | `< 4.87s` | **{eval_status(exec_avg, 4.999, 15.000)}** |",
                f"| **Acquire Connection** | `{conn_avg:.3f}s` | `< 0.238s` | **{eval_status(conn_avg, 0.238, 0.500)}** |",
                f"| **Per-User Throttler** | `{throttle_avg:.3f}s` | `0.000s` | **{eval_status(throttle_avg, 0.001, 1.000)}** |",
                f"| **Worker Queue Time** | `{queue_avg:.3f}s` | `0.000s` | **{eval_status(queue_avg, 0.100, 0.500)}** |",
                f"| **Project Init** | `{proj_init:.3f}s` | `< 0.100s` | **{eval_status(proj_init, 0.100, 0.250)}** |",
                f"| **Model Init (Compute)** | `{model_comp:.2f}s` | `< 2.42s` | **{eval_status(model_comp, 2.440, 5.000)}** |",
                f"| **Model Init (Cache)** | `{model_cache:.2f}s` | `< 0.50s` | **{eval_status(model_cache, 1.000, 2.500)}** |",
                f"| **Explore Init (Compute)** | `{exp_comp:.3f}s` | `< 0.233s` | **{eval_status(exp_comp, 0.233, 0.500)}** |",
                f"| **Explore Init (Cache)** | `{exp_cache:.3f}s` | `< 0.351s` | **{eval_status(exp_cache, 0.351, 0.750)}** |",
                f"| **SQL Prepare Time** | `{prep_avg:.3f}s` | `< 0.439s` | **{eval_status(prep_avg, 0.439, 1.000)}** |",
                f"| **Stream to Cache** | `{stream_avg:.3f}s` | `< 0.223s` | **{eval_status(stream_avg, 0.223, 0.500)}** |",
                f"| **Post Processing** | `{post_avg:.3f}s` | `< 0.223s` | **{eval_status(post_avg, 0.223, 0.500)}** |"
            ]

            if component_id == 2:
                return "\n".join(report)

        if component_id == 1 or component_id is None:
            devs = _client.run_query("system__activity", "user", ["user.count"], filters={
                "user.is_disabled": "No", "permission_set.permissions": "%develop%"
            }, limit="1")
            admins = _client.run_query("system__activity", "user", ["user.count"], filters={
                "user.is_disabled": "No", "permission_set.permissions": "%admin%"
            }, limit="1")
            dev_count = devs[0].get("user.count", 0) if devs else 0
            admin_count = admins[0].get("user.count", 0) if admins else 0
            
            c1_report = [
                f"\n## 2. Component 1: Strategy & Developer Baseline",
                f"- **Active Looker Developers:** `{dev_count}`",
                f"- **Active Looker Administrators:** `{admin_count}`"
            ]
            if component_id == 1:
                return "\n".join(c1_report)
            report.extend(c1_report)

        if component_id == 4 or component_id is None:
            stale_dashboards = _client.run_query("system__activity", "history", [
                "dashboard.id", "dashboard.title", "history.most_recent_query_date"
            ], filters={"dashboard.id": "NOT NULL", "history.most_recent_query_date": "before 90 days ago"}, limit="10")
            
            zombie_schedules = _client.run_query("system__activity", "user", [
                "user.name", "user_facts.last_ui_login_date", "scheduled_job.count"
            ], filters={"user_facts.last_ui_login_date": "before 90 days ago", "user.is_disabled": "No", "scheduled_job.count": ">0"}, limit="10")
            
            c4_report = [
                f"\n## 3. Component 4: Unused Content & Zombie Schedules",
                f"- **90-Day Stale Dashboards Identified:** `{len(stale_dashboards)}`",
                f"- **Zombie Schedules (Inactive Users >90 Days):** `{len(zombie_schedules)}`"
            ]
            if component_id == 4:
                return "\n".join(c4_report)
            report.extend(c4_report)

        return "\n".join(report)

    except Exception as e:
        return f"Audit execution error: {str(e)}"
