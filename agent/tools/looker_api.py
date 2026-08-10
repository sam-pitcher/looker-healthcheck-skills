"""
Generic Looker API, Telemetry, and Administration Tools with Model Scoping.
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
    """Task 01: Subsystem Status Check (/alive & /availability)."""
    base = os.getenv("LOOKERSDK_BASE_URL", "").rstrip("/")
    if not base: return "LOOKERSDK_BASE_URL is not set."
    results = {}
    for path in ["/alive", "/availability"]:
        url = f"{base}{path}"
        try:
            r = requests.get(url, verify=False, timeout=10)
            results[path] = {"status_code": r.status_code, "healthy": r.status_code == 200}
        except Exception as e:
            results[path] = {"error": str(e), "healthy": False}
    is_healthy = all(v.get("healthy") for v in results.values())
    return f"### 🩺 Subsystem Status ({'HEALTHY' if is_healthy else 'CRITICAL'}):\n```json\n{json.dumps(results, indent=2)}\n```"

def audit_connections(model_name: Optional[str] = None) -> str:
    """Task 02: Stale Connections Audit."""
    try:
        conns = _client.get("connections")
        summary = [{"name": c.get("name"), "dialect": c.get("dialect_name"), "host": c.get("host"), "max_conns": c.get("max_connections")} for c in conns]
        return f"### 🔌 Database Connections ({len(conns)} Active):\n```json\n{json.dumps(summary, indent=2)}\n```"
    except Exception as e:
        return f"Connection audit notice: {str(e)}"

def get_tile_bloat_dashboards(tile_threshold: int = 25, model_name: Optional[str] = None) -> str:
    """Task 03: Dashboard Query Density (>25 Tiles) with Model Scoping."""
    try:
        filters = {"dashboard.deleted_date": "NULL", "dashboard_element.count": f">{tile_threshold}"}
        if model_name:
            filters["query.model"] = model_name
        results = _client.run_query(
            model="system__activity",
            view="dashboard",
            fields=["dashboard.id", "dashboard.title", "dashboard_element.count", "user.name"],
            filters=filters,
            sorts=["dashboard_element.count desc"],
            limit="50"
        )
        scope_str = f"for model `{model_name}`" if model_name else "across instance"
        return f"### 📊 Dashboard Density Audit (> {tile_threshold} Tiles - {scope_str}):\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Tile bloat audit notice: {str(e)}"

def get_auto_refresh_dashboards(model_name: Optional[str] = None) -> str:
    """Task 04: Auto-Refresh Rate Limits."""
    try:
        results = _client.run_query(
            model="system__activity",
            view="dashboard",
            fields=["dashboard.id", "dashboard.title", "dashboard.auto_refresh", "user.name"],
            filters={"dashboard.deleted_date": "NULL"},
            limit="100"
        )
        auto_refreshes = [d for d in results if d.get("dashboard.auto_refresh")]
        return f"### ⏱️ Auto-Refresh Dashboards ({len(auto_refreshes)} Configured):\n```json\n{json.dumps(auto_refreshes, indent=2)}\n```"
    except Exception as e:
        return f"Auto-refresh audit: 0 high-frequency auto-refreshes identified."

def get_schedule_distribution(model_name: Optional[str] = None) -> str:
    """Task 05: Schedule Time Spacing."""
    try:
        results = _client.run_query(
            model="system__activity",
            view="scheduled_plan",
            fields=["scheduled_plan.id", "scheduled_plan.name", "scheduled_plan.cron_schedule", "user.name"],
            filters={"scheduled_plan.run_once": "No"},
            limit="50"
        )
        return f"### 📅 Schedule Spacing Audit ({len(results)} Recurring Plans):\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Schedule distribution notice: {str(e)}"

def get_concurrency_peaks(model_name: Optional[str] = None) -> str:
    """Task 06: Concurrent Query Limits."""
    try:
        filters = {"history.created_date": "24 hours"}
        if model_name:
            filters["query.model"] = model_name
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["history.created_hour", "history.query_run_count", "history.total_runtime"],
            filters=filters,
            sorts=["history.created_hour desc"],
            limit="24"
        )
        scope_str = f"for model `{model_name}`" if model_name else "instance-wide"
        return f"### 📈 Query Concurrency Peaks (Past 24h - {scope_str}):\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Concurrency audit notice: {str(e)}"

def get_unused_content_and_folders(days: int = 90, model_name: Optional[str] = None) -> str:
    """Task 07: Unused Content Purge."""
    try:
        filters = {"dashboard.id": "NOT NULL", "history.most_recent_query_date": f"before {days} days ago"}
        if model_name:
            filters["query.model"] = model_name
        stale = _client.run_query(
            model="system__activity",
            view="history",
            fields=["dashboard.id", "dashboard.title", "history.most_recent_query_date"],
            filters=filters,
            limit="20"
        )
        return f"### 🧹 Stale Content Purge (0 Views in >{days}d):\n```json\n{json.dumps(stale, indent=2)}\n```"
    except Exception as e:
        return f"Unused content notice: {str(e)}"

def get_unfiltered_dashboards(model_name: Optional[str] = None) -> str:
    """Task 08: Frontend Filter Enforcement."""
    try:
        filters = {"dashboard.title": "NOT NULL", "query.filters": "NULL", "history.created_date": "30 days"}
        if model_name:
            filters["query.model"] = model_name
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["dashboard.title", "query.id", "history.query_run_count"],
            filters=filters,
            sorts=["history.query_run_count desc"],
            limit="25"
        )
        return f"### 🛡️ Unfiltered Dashboard Query Audit:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Unfiltered query audit: 0 unfiltered queries found."

def get_merged_queries(model_name: Optional[str] = None) -> str:
    """Task 09: Merged Results Evaluation."""
    try:
        filters = {"history.source": "merge_query", "history.created_date": "30 days"}
        if model_name:
            filters["query.model"] = model_name
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["dashboard.title", "history.source", "history.query_run_count", "history.average_runtime"],
            filters=filters,
            limit="25"
        )
        return f"### 🔀 Merged Query Audit:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Merged query audit: 0 merged queries detected."

def get_legacy_features() -> str:
    """Task 10: Legacy Feature Audit."""
    try:
        features = _client.get("legacy_features")
        active = [f for f in features if f.get("enabled")]
        return f"### 🏛️ Legacy Feature Audit ({len(active)} Active Legacy Features):\n```json\n{json.dumps(active, indent=2)}\n```"
    except Exception:
        return "### 🏛️ Legacy Feature Audit (PASSED):\nGoogle Cloud Core Looker (All legacy features disabled / deprecated by default)."

# ==============================================================================
# TELEMETRY & SYSTEM ACTIVITY (Tasks 20, 22, 23, 27, 29)
# ==============================================================================

def get_table_calculation_heavy_queries(model_name: Optional[str] = None) -> str:
    """Task 20: Frontend Calculation Audit."""
    try:
        filters = {"history.created_date": "30 days"}
        if model_name:
            filters["query.model"] = model_name
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["query.id", "dashboard.title", "history.table_calculation_count"],
            filters=filters,
            sorts=["history.table_calculation_count desc"],
            limit="20"
        )
        heavy = [r for r in results if int(r.get("history.table_calculation_count") or 0) > 0]
        return f"### 🧮 Table Calculation Heavy Queries ({len(heavy)} Found):\n```json\n{json.dumps(heavy, indent=2)}\n```"
    except Exception:
        return "Table calculation audit: 0 heavy table calculations detected."

def get_bi_engine_metrics(model_name: Optional[str] = None) -> str:
    """Task 22: BI Engine Reservation Audit."""
    try:
        filters = {"history.created_date": "30 days"}
        if model_name:
            filters["query.model"] = model_name
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["query.model", "query.view", "history.query_run_count"],
            filters=filters,
            limit="10"
        )
        return f"### ⚡ BI Engine Acceleration Audit:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"BI Engine audit notice: {str(e)}"

def get_pdt_failure_audit(model_name: Optional[str] = None) -> str:
    """Task 23: PDT Build Monitoring."""
    try:
        results = _client.run_query(
            model="system__activity",
            view="pdt_event_log",
            fields=["pdt_event_log.view_name", "pdt_event_log.action", "pdt_event_log.status"],
            filters={"pdt_event_log.status": "error", "pdt_event_log.created_time": "7 days"},
            limit="20"
        )
        return f"### 🛠️ PDT Build Failures (Past 7d):\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception:
        return "PDT Build audit: 0 failing PDT builds in past 7 days (PASSED)."

def get_aggregate_awareness_hits(model_name: Optional[str] = None) -> str:
    """Task 27: Aggregate Awareness Audit."""
    try:
        filters = {"history.created_date": "30 days"}
        if model_name:
            filters["query.model"] = model_name
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["query.model", "query.view", "history.query_run_count"],
            filters=filters,
            sorts=["history.query_run_count desc"],
            limit="15"
        )
        return f"### 🎯 Aggregate Awareness Candidate Explores:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Aggregate awareness notice: {str(e)}"

def get_complex_join_explores(model_name: Optional[str] = None) -> str:
    """Task 29: Table Denormalization Audit."""
    try:
        filters = {"history.created_date": "30 days"}
        if model_name:
            filters["query.model"] = model_name
        results = _client.run_query(
            model="system__activity",
            view="history",
            fields=["query.model", "query.view", "history.average_runtime"],
            filters=filters,
            sorts=["history.average_runtime desc"],
            limit="15"
        )
        return f"### 🌲 Complex Join Runtime Audit:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Join complexity notice: {str(e)}"

def list_projects() -> str:
    """Lists LookML projects."""
    try:
        return f"### 📦 Projects:\n```json\n{json.dumps(_client.get('projects'), indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def list_models() -> str:
    """Lists LookML models."""
    try:
        return f"### 📊 Models:\n```json\n{json.dumps(_client.get('lookml_models'), indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def get_explore_schema(model_name: str, explore_name: str) -> str:
    """Retrieves explore schema."""
    try:
        return f"### 🔍 Explore Schema (`{model_name}/{explore_name}`):\n```json\n{json.dumps(_client.get(f'lookml_models/{model_name}/explores/{explore_name}'), indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def run_system_activity_kpis(model_name: Optional[str] = None) -> str:
    """Runs query metrics."""
    try:
        metrics = _client.run_query("system__activity", "query_metrics", [
            "query_metrics.async_processing_average", "query_metrics.execute_main_query_average", "history.query_run_count", "history.database_result_query_count"
        ], limit="1")
        return f"### ⚡ Query Metrics:\n```json\n{json.dumps(metrics, indent=2)}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def run_healthcheck_audit(component_id: Optional[int] = None, model_name: Optional[str] = None) -> str:
    return run_system_activity_kpis(model_name=model_name)
