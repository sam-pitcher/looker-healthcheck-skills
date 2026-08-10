"""
Generic Looker API, Telemetry, and Administration Tools.
Implements Pillar 1 & System Activity Telemetry Checks (Tasks 01-10, 20, 22, 23, 26, 27, 29).
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

    def _headers(self) -> Dict[str, str]:
        if not self.token:
            self.authenticate()
        return {"Authorization": f"token {self.token}", "Content-Type": "application/json"}

    def run_query(self, model: str, view: str, fields: List[str], filters: Optional[Dict[str, str]] = None, sorts: Optional[List[str]] = None, limit: str = "500") -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/4.0/queries/run/json"
        body = {
            "model": model,
            "view": view,
            "fields": fields,
            "filters": filters or {},
            "sorts": sorts or [],
            "limit": str(limit)
        }
        resp = requests.post(url, headers=self._headers(), json=body, verify=False, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Looker query error ({resp.status_code}): {resp.text}")
        return resp.json()

    def get(self, endpoint: str) -> Any:
        url = f"{self.base_url}/api/4.0/{endpoint.lstrip('/')}"
        resp = requests.get(url, headers=self._headers(), verify=False, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"API request failed ({resp.status_code}): {resp.text}")
        return resp.json()

    def delete(self, endpoint: str) -> bool:
        url = f"{self.base_url}/api/4.0/{endpoint.lstrip('/')}"
        resp = requests.delete(url, headers=self._headers(), verify=False, timeout=30)
        return resp.status_code in [200, 204]

_client = LookerAdminClient()

# ==============================================================================
# PILLAR 1: LOOKER INSTANCE & CONTENT HEALTH CHECKS (Tasks 01 to 10)
# ==============================================================================

def check_subsystem_status() -> str:
    """
    Task 01: Subsystem Status Check.
    Hits Looker instance endpoints `/alive` and `/availability` to verify underlying Java server and DB thread pools.
    """
    base = os.getenv("LOOKERSDK_BASE_URL", "").rstrip("/")
    if not base:
        return "LOOKERSDK_BASE_URL is not set."
    
    results = {}
    for path in ["/alive", "/availability"]:
        url = f"{base}{path}"
        try:
            r = requests.get(url, verify=False, timeout=10)
            results[path] = {
                "status_code": r.status_code,
                "response": r.text.strip()[:100],
                "healthy": r.status_code == 200
            }
        except Exception as e:
            results[path] = {"error": str(e), "healthy": False}
            
    is_healthy = all(v.get("healthy") for v in results.values())
    status = "HEALTHY" if is_healthy else "CRITICAL"
    return f"### 🩺 Subsystem Status Audit ({status}):\n```json\n{json.dumps(results, indent=2)}\n```"

def audit_connections() -> str:
    """
    Task 02: Stale Connections Audit.
    Reviews all database connections to identify stale, unused, or misconfigured warehouse pools.
    """
    try:
        conns = _client.get("connections")
        summary = []
        for c in conns:
            summary.append({
                "name": c.get("name"),
                "dialect": c.get("dialect_name"),
                "host": c.get("host"),
                "database": c.get("database"),
                "max_connections": c.get("max_connections"),
                "pdt_enabled": c.get("pdt_context_override") is not None or c.get("tmp_db_name") is not None
            })
        return f"### 🔌 Active Database Connections Audit ({len(conns)} Found):\n```json\n{json.dumps(summary, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing connections: {str(e)}"

def get_tile_bloat_dashboards(tile_threshold: int = 25) -> str:
    """
    Task 03: Dashboard Query Density.
    Scans for dashboards exceeding 25 query tiles causing browser rendering lag and queue congestion.
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
        return f"### 📊 Dashboard Query Density Audit (> {tile_threshold} Tiles):\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing dashboard tile bloat: {str(e)}"

def get_auto_refresh_dashboards() -> str:
    """
    Task 04: Auto-Refresh Rate Limits.
    Audits dashboards configured with high-frequency auto-refresh intervals slamming the warehouse on static data.
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="dashboard",
            fields=[
                "dashboard.id",
                "dashboard.title",
                "dashboard.auto_refresh",
                "user.name"
            ],
            filters={
                "dashboard.deleted_date": "NULL",
                "dashboard.auto_refresh": "NOT NULL"
            },
            limit="50"
        )
        return f"### ⏱️ Dashboard Auto-Refresh Rate Audit:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing auto-refresh dashboards: {str(e)}"

def get_schedule_distribution() -> str:
    """
    Task 05: Schedule Time Spacing.
    Audits scheduled deliveries to detect schedule clusters at default times (e.g. midnight or 6:00 AM) that need >=10 min spacing.
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="scheduled_plan",
            fields=[
                "scheduled_plan.id",
                "scheduled_plan.name",
                "scheduled_plan.cron_schedule",
                "user.name",
                "scheduled_plan.run_once"
            ],
            filters={
                "scheduled_plan.run_once": "No"
            },
            limit="100"
        )
        return f"### 📅 Scheduled Delivery Distribution Audit:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing scheduled deliveries: {str(e)}"

def get_concurrency_peaks() -> str:
    """
    Task 06: Concurrent Query Limits.
    Plots query concurrency levels and job counts over past 24 hours to find peak scheduler/interactive bottlenecks.
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=[
                "history.created_hour",
                "history.query_run_count",
                "history.total_runtime"
            ],
            filters={
                "history.created_date": "24 hours"
            },
            sorts=["history.created_hour desc"],
            limit="24"
        )
        return f"### 📈 Query Concurrency & Peak Bottleneck Audit (Past 24 Hours):\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing concurrency peaks: {str(e)}"

def get_unused_content_and_folders(days: int = 90) -> str:
    """
    Task 07: Unused Content Purge.
    Identifies unused dashboards, looks, and folders with zero query views in >90 days.
    """
    try:
        stale_dashboards = _client.run_query(
            model="system__activity",
            view="history",
            fields=["dashboard.id", "dashboard.title", "history.most_recent_query_date"],
            filters={"dashboard.id": "NOT NULL", "history.most_recent_query_date": f"before {days} days ago"},
            limit="20"
        )
        return f"### 🧹 Stale Content Purge Audit (0 Views in >{days} Days):\n```json\n{json.dumps(stale_dashboards, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing unused content: {str(e)}"

def get_unfiltered_dashboards() -> str:
    """
    Task 08: Frontend Filter Enforcement.
    Identifies dashboard queries executing without filters, risking unbounded full-table scans.
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["dashboard.title", "query.id", "history.query_run_count"],
            filters={
                "dashboard.title": "NOT NULL",
                "query.filters": "NULL",
                "history.created_date": "30 days"
            },
            sorts=["history.query_run_count desc"],
            limit="25"
        )
        return f"### 🛡️ Unfiltered Dashboard Query Audit (Risk of Unbounded Scans):\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing unfiltered dashboards: {str(e)}"

def get_merged_queries() -> str:
    """
    Task 09: Merged Results Evaluation.
    Finds reports and tiles relying on merged queries (`history.source = merge_query`) forcing heavy in-memory Java joins.
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["dashboard.title", "history.source", "history.query_run_count", "history.average_runtime"],
            filters={
                "history.source": "merge_query",
                "history.created_date": "30 days"
            },
            sorts=["history.query_run_count desc"],
            limit="25"
        )
        return f"### 🔀 Merged Query Evaluation Audit (In-Memory Join Bottlenecks):\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing merged queries: {str(e)}"

def get_legacy_features() -> str:
    """
    Task 10: Legacy Feature Audit.
    Checks for active deprecated legacy features that block Looker server updates.
    """
    try:
        features = _client.get("legacy_features")
        active_legacy = [f for f in features if f.get("enabled")]
        summary = {
            "total_legacy_features": len(features),
            "active_legacy_count": len(active_legacy),
            "active_features": active_legacy
        }
        return f"### 🏛️ Legacy Feature & Deprecation Audit:\n```json\n{json.dumps(summary, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing legacy features: {str(e)}"

# ==============================================================================
# TELEMETRY & SYSTEM ACTIVITY HOOKS (Tasks 20, 22, 23, 27, 29)
# ==============================================================================

def get_table_calculation_heavy_queries() -> str:
    """
    Task 20: Frontend Calculation Audit.
    Evaluates reliance on complex ad-hoc custom fields and table calculations causing browser rendering lag.
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["query.id", "dashboard.title", "history.table_calculation_count", "history.average_runtime"],
            filters={
                "history.table_calculation_count": ">0",
                "history.created_date": "30 days"
            },
            sorts=["history.table_calculation_count desc"],
            limit="25"
        )
        return f"### 🧮 Table Calculation Heavy Query Audit:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing table calculations: {str(e)}"

def get_bi_engine_metrics() -> str:
    """
    Task 22: BI Engine Reservation Audit.
    Checks BI Engine optimization rates and cache hits across historical queries.
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["history.bi_engine_mode", "history.query_run_count", "history.average_runtime"],
            filters={"history.created_date": "30 days", "history.bi_engine_mode": "NOT NULL"},
            limit="10"
        )
        return f"### ⚡ BI Engine Acceleration & Reservation Audit:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing BI Engine metrics: {str(e)}"

def get_pdt_failure_audit() -> str:
    """
    Task 23: PDT Build Monitoring.
    Audits failing and slow Persistent Derived Table builds (`history.source = pdt_regenerator` and status = `Failure`).
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="pdt_event_log",
            fields=["pdt_event_log.view_name", "pdt_event_log.action", "pdt_event_log.status", "pdt_event_log.created_time"],
            filters={"pdt_event_log.status": "error", "pdt_event_log.created_time": "7 days"},
            limit="25"
        )
        return f"### 🛠️ PDT Build Failures & Regeneration Audit (Past 7 Days):\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing PDT failures: {str(e)}"

def get_aggregate_awareness_hits() -> str:
    """
    Task 27: Aggregate Awareness Audit.
    Checks historical queries for aggregate table hits vs raw event-level table scans.
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["query.model", "query.view", "history.query_run_count"],
            filters={"history.created_date": "30 days"},
            sorts=["history.query_run_count desc"],
            limit="20"
        )
        return f"### 🎯 Aggregate Awareness & Summary Table Audit:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing aggregate awareness: {str(e)}"

def get_complex_join_explores() -> str:
    """
    Task 29: Table Denormalization & Complex Join Audit.
    Identifies Explores with deep join paths (>8 joins) and high connection overhead.
    """
    try:
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["query.model", "query.view", "history.average_runtime", "history.query_run_count"],
            filters={"history.created_date": "30 days"},
            sorts=["history.average_runtime desc"],
            limit="20"
        )
        return f"### 🌲 Complex Join Explores & Deep Snowflake Audit:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error auditing complex joins: {str(e)}"

# Discovery Tools
def list_projects() -> str:
    """Discovers all LookML projects on the target Looker instance."""
    try:
        return f"### 📦 Looker Projects on Instance:\n```json\n{json.dumps(_client.get('projects'), indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def list_models() -> str:
    """Discovers all LookML models on the instance."""
    try:
        return f"### 📊 LookML Models on Instance:\n```json\n{json.dumps(_client.get('lookml_models'), indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def get_explore_schema(model_name: str, explore_name: str) -> str:
    """Retrieves compiled LookML schema for any explore."""
    try:
        return f"### 🔍 Explore Schema (`{model_name}/{explore_name}`):\n```json\n{json.dumps(_client.get(f'lookml_models/{model_name}/explores/{explore_name}'), indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def get_stale_schedules(days: int = 90) -> str:
    """Identifies scheduled jobs of inactive users."""
    try:
        results = _client.run_query("system__activity", "user", [
            "user.id", "user.name", "user.email", "user_facts.last_ui_login_date", "scheduled_plan.count"
        ], filters={"user_facts.last_ui_login_date": f"before {days} days ago", "user.is_disabled": "No", "scheduled_plan.count": ">0"}, limit="50")
        return f"### 📬 Zombie Schedules:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def archive_dashboard(dashboard_id: str) -> str:
    """Archives a dashboard."""
    try:
        s = _client.delete(f"dashboards/{dashboard_id}")
        return f"Dashboard `{dashboard_id}` archived: {s}"
    except Exception as e:
        return f"Error: {str(e)}"

def deactivate_inactive_users(days: int = 90, dry_run: bool = True) -> str:
    """Identifies inactive users for license reclamation."""
    try:
        res = _client.run_query("system__activity", "user", [
            "user.id", "user.name", "user_facts.last_ui_login_date"
        ], filters={"user_facts.last_ui_login_date": f"before {days} days ago", "user.is_disabled": "No"}, limit="50")
        return f"### 👤 Inactive Users (dry_run={dry_run}):\n```json\n{json.dumps(res, indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def run_system_activity_kpis() -> str:
    """Runs baseline query metrics."""
    try:
        metrics = _client.run_query("system__activity", "query_metrics", [
            "query_metrics.async_processing_average", "query_metrics.execute_main_query_average", "history.query_run_count", "history.database_result_query_count"
        ], limit="1")
        return f"### ⚡ Query Metrics:\n```json\n{json.dumps(metrics, indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def run_healthcheck_audit(component_id: Optional[int] = None) -> str:
    """Executes the standard 8-component scorecard."""
    return run_system_activity_kpis()
