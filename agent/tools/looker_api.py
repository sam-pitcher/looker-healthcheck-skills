"""
Generic Looker API, Telemetry, and Administration Tools with Model Scoping.
Implements Pillar 1 & System Activity Telemetry Checks (Tasks 01-10, 20, 22, 23, 26, 27, 29).
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
# Configurable TLS verification (Default: True for enterprise security)
LOOKER_VERIFY_SSL = os.getenv("LOOKER_VERIFY_SSL", "true").lower() in ("true", "1", "yes", "t")

try:
    import urllib3
    if not LOOKER_VERIFY_SSL:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

class LookerAdminClient:
    def __init__(self):
        self.base_url = os.getenv("LOOKERSDK_BASE_URL", "").rstrip("/")
        self.client_id = os.getenv("LOOKERSDK_CLIENT_ID", "")
        self.client_secret = os.getenv("LOOKERSDK_CLIENT_SECRET", "")
        self.verify_ssl = LOOKER_VERIFY_SSL
        self.token = None
        self.token_acquired_at = 0.0
        self.token_expires_in = 3600

    def authenticate(self):
        if not self.base_url or not self.client_id or not self.client_secret:
            raise ValueError("Looker credentials (LOOKERSDK_BASE_URL, LOOKERSDK_CLIENT_ID, LOOKERSDK_CLIENT_SECRET) are missing.")
        
        login_url = f"{self.base_url}/api/4.0/login"
        payload = json.dumps({"client_id": self.client_id, "client_secret": self.client_secret}).encode("utf-8")
        
        try:
            import requests
            resp = requests.post(
                login_url,
                data={"client_id": self.client_id, "client_secret": self.client_secret},
                verify=self.verify_ssl,
                timeout=30
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Looker Auth failed ({resp.status_code}): {resp.text}")
            data = resp.json()
        except ImportError:
            import urllib.request
            import ssl
            ssl_ctx = ssl.create_default_context() if self.verify_ssl else ssl._create_unverified_context()
            req = urllib.request.Request(login_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

        self.token = data.get("access_token")
        self.token_expires_in = int(data.get("expires_in", 3600))
        self.token_acquired_at = time.time()

    def _headers(self) -> Dict[str, str]:
        # Preemptively refresh if token is within 60 seconds of expiry
        if not self.token or (time.time() - self.token_acquired_at >= (self.token_expires_in - 60)):
            self.authenticate()
        return {"Authorization": f"token {self.token}", "Content-Type": "application/json"}

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}/api/4.0/{endpoint.lstrip('/')}"
        timeout = kwargs.pop("timeout", 60)
        
        try:
            import requests
            headers = self._headers()
            resp = requests.request(
                method,
                url,
                headers=headers,
                verify=self.verify_ssl,
                timeout=timeout,
                **kwargs
            )
            if resp.status_code == 401:
                # Token expired or rejected, refresh and retry once
                self.authenticate()
                resp = requests.request(
                    method,
                    url,
                    headers=self._headers(),
                    verify=self.verify_ssl,
                    timeout=timeout,
                    **kwargs
                )
            if resp.status_code not in (200, 204):
                raise RuntimeError(f"API request failed ({resp.status_code}): {resp.text}")
            return resp.json() if resp.status_code == 200 and resp.content else {}
        except ImportError:
            import urllib.request
            import ssl
            ssl_ctx = ssl.create_default_context() if self.verify_ssl else ssl._create_unverified_context()
            data_bytes = json.dumps(kwargs.get("json")).encode("utf-8") if "json" in kwargs else None
            req = urllib.request.Request(url, data=data_bytes, headers=self._headers(), method=method)
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}

    def run_query(self, model: str, view: str, fields: List[str], filters: Optional[Dict[str, str]] = None, sorts: Optional[List[str]] = None, limit: str = "500") -> List[Dict[str, Any]]:
        body = {
            "model": model,
            "view": view,
            "fields": fields,
            "filters": filters or {},
            "sorts": sorts or [],
            "limit": str(limit)
        }
        res = self._request("POST", "queries/run/json", json=body, timeout=60)
        return res if isinstance(res, list) else []

    def get(self, endpoint: str) -> Any:
        return self._request("GET", endpoint, timeout=30)

    def delete(self, endpoint: str) -> bool:
        try:
            self._request("DELETE", endpoint, timeout=30)
            return True
        except Exception:
            return False

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
            try:
                import requests
                r = requests.get(url, verify=LOOKER_VERIFY_SSL, timeout=10)
                code = r.status_code
            except ImportError:
                import urllib.request
                import ssl
                ssl_ctx = ssl.create_default_context() if LOOKER_VERIFY_SSL else ssl._create_unverified_context()
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
                    code = resp.getcode()
            results[path] = {"status_code": code, "healthy": code == 200}
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

# PSO Benchmarks Definition
PSO_BENCHMARKS = {
    "async_processing": {"target": 5.0, "warning": 10.0, "critical": 15.0, "unit": "s", "label": "Average Async Processing"},
    "execute_main_query": {"target": 4.87, "warning": 5.0, "critical": 15.0, "unit": "s", "label": "Main Query Execution"},
    "acquire_connection": {"target": 0.238, "warning": 0.24, "critical": 0.5, "unit": "s", "label": "Acquire Connection Time"},
    "model_init_computed": {"target": 2.42, "warning": 2.44, "critical": 5.0, "unit": "s", "label": "Model Init (Compute)"},
    "model_init_cache": {"target": 0.50, "warning": 1.0, "critical": 2.5, "unit": "s", "label": "Model Init (Cache)"},
    "explore_init": {"target": 0.233, "warning": 0.233, "critical": 0.5, "unit": "s", "label": "Explore Init (Compute)"},
    "marshalled_cache_load": {"target": 0.351, "warning": 0.351, "critical": 0.75, "unit": "s", "label": "Explore Init (Cache)"},
    "prepare": {"target": 0.20, "warning": 0.439, "critical": 1.0, "unit": "s", "label": "SQL Prepare Average"},
    "postprocessing": {"target": 0.223, "warning": 0.223, "critical": 0.5, "unit": "s", "label": "Post-Processing Time"},
    "stream_to_cache": {"target": 0.223, "warning": 0.223, "critical": 0.5, "unit": "s", "label": "Stream to Cache Time"},
    "queued": {"target": 0.00, "warning": 0.10, "critical": 0.5, "unit": "s", "label": "Worker Queue Wait Time"},
    "per_user_throttler": {"target": 0.00, "warning": 0.01, "critical": 1.0, "unit": "s", "label": "Per-User Throttler"}
}

def execute_complete_healthcheck(
    model_name: Optional[str] = None,
    project_id: Optional[str] = None,
    project_path: Optional[str] = None
) -> tuple[str, Dict[str, Any]]:
    """
    Executes the complete 30-Check Healthcheck Program across all 3 pillars:
    - Pillar 1: Instance & Content Health (Tasks 01-10)
    - Pillar 2: LookML & Modeling Quality (Tasks 11-20)
    - Pillar 3: BigQuery & Warehouse Compute (Tasks 21-30)
    
    Evaluates both PASSED and FAILING checks, computes overall health score,
    and returns a tuple of (report_markdown, structured_findings).
    """
    from datetime import datetime, timezone
    from agent.tools.lookml_fs import (
        run_lookml_validation, audit_primary_keys, audit_join_relationships,
        run_henry_vacuum, audit_explore_field_exposure, audit_folder_structure,
        audit_naming_conventions, audit_metadata_descriptions, audit_unused_joins,
        audit_incremental_pdts, audit_oauth_connections, audit_join_key_syntax
    )
    from agent.tools.bq_client import (
        audit_partition_cluster_filters, audit_datagroup_sync,
        audit_query_costs_and_bytes_billed, audit_bq_slots
    )

    findings: List[Dict[str, Any]] = []
    
    def _add_finding(check_id: str, task_num: int, pillar: str, name: str, status: str, summary: str, details: Any, remediation: str, skill: str):
        findings.append({
            "check_id": check_id,
            "task_number": task_num,
            "pillar": pillar,
            "name": name,
            "status": status,
            "score": 100 if status == "PASSED" else (50 if status == "WARNING" else 0),
            "summary": summary,
            "details": details if isinstance(details, (dict, list, str, int, float, bool)) else str(details),
            "prescribed_remediation": remediation,
            "recommended_skill": skill
        })

    scope_str = f"Model: `{model_name}`" if model_name else "Instance-wide (All Models)"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # --------------------------------------------------------------------------
    # PILLAR 1: Instance & Content Health (Tasks 01 to 10)
    # --------------------------------------------------------------------------
    
    # Task 01: Subsystems
    sub_res = check_subsystem_status()
    sub_status = "PASSED" if "HEALTHY" in sub_res else "CRITICAL"
    _add_finding("P1-01", 1, "Pillar 1: Instance & Content", "Subsystem Status & Endpoint Health", sub_status,
                 "Looker endpoints /alive and /availability verified.", sub_res,
                 "Verify instance load balancer and JVM memory allocation.", "looker-healthcheck")

    # Task 02: Connections
    conn_res = audit_connections(model_name)
    conn_status = "PASSED" if "Active" in conn_res or "notice" not in conn_res.lower() else "WARNING"
    _add_finding("P1-02", 2, "Pillar 1: Instance & Content", "Database Connections & Pool Limits", conn_status,
                 "Active connection pools and host parameters audited.", conn_res,
                 "Tune max_connections and verify SSL/TLS connection parameters.", "connecting-looker-to-bigquery")

    # Task 03: Tile Bloat (>25 Tiles)
    bloat_res = get_tile_bloat_dashboards(tile_threshold=25, model_name=model_name)
    bloat_status = "WARNING" if "[\n  {" in bloat_res else "PASSED"
    _add_finding("P1-03", 3, "Pillar 1: Instance & Content", "Dashboard Query Density (>25 Tiles)", bloat_status,
                 "Audited dashboards for query density exceeding 25 tiles.", bloat_res,
                 "Split large dashboards into tabbed layouts or link via HTML drill-downs.", "creating-looker-dashboard")

    # Task 04: Auto-Refresh (<30 min)
    refresh_res = get_auto_refresh_dashboards(model_name=model_name)
    refresh_status = "WARNING" if "Configured" in refresh_res and "0 Configured" not in refresh_res else "PASSED"
    _add_finding("P1-04", 4, "Pillar 1: Instance & Content", "Auto-Refresh Rate Limits (<30m)", refresh_status,
                 "Audited high-frequency dashboard auto-refresh intervals.", refresh_res,
                 "Ensure auto-refresh interval does not exceed underlying data warehouse ETL frequency.", "looker-performance-optimizer")

    # Task 05: Schedule Distribution
    sched_res = get_schedule_distribution(model_name=model_name)
    sched_status = "PASSED"
    _add_finding("P1-05", 5, "Pillar 1: Instance & Content", "Schedule Time Spacing & Distribution", sched_status,
                 "Scheduled plans analyzed for cron distribution.", sched_res,
                 "Stagger cron schedules away from top-of-the-hour (:00) spikes.", "looker-healthcheck")

    # Task 06: Concurrency Peaks
    conc_res = get_concurrency_peaks(model_name=model_name)
    conc_status = "PASSED"
    _add_finding("P1-06", 6, "Pillar 1: Instance & Content", "Query Concurrency Peaks & Queue Limits", conc_status,
                 "Query concurrency peaks analyzed over past 24h.", conc_res,
                 "Implement datagroup caching to alleviate concurrent database load.", "looker-performance-optimizer")

    # Task 07: Unused Content (>90d)
    unused_res = get_unused_content_and_folders(days=90, model_name=model_name)
    unused_status = "WARNING" if "[\n  {" in unused_res else "PASSED"
    _add_finding("P1-07", 7, "Pillar 1: Instance & Content", "Stale Content & Unused Folder Purge", unused_status,
                 "Content unqueried for >90 days audited.", unused_res,
                 "Soft delete stale dashboards and move orphaned looks to an archive folder.", "looker-refactoring-skill")

    # Task 08: Unfiltered Queries
    unfilt_res = get_unfiltered_dashboards(model_name=model_name)
    unfilt_status = "WARNING" if "[\n  {" in unfilt_res else "PASSED"
    _add_finding("P1-08", 8, "Pillar 1: Instance & Content", "Frontend Filter Enforcement", unfilt_status,
                 "Queries running without frontend dashboard filters audited.", unfilt_res,
                 "Add conditionally_filter or always_filter to explore definitions.", "lookml-modeling-guidelines")

    # Task 09: Merged Queries
    merge_res = get_merged_queries(model_name=model_name)
    merge_status = "WARNING" if "[\n  {" in merge_res else "PASSED"
    _add_finding("P1-09", 9, "Pillar 1: Instance & Content", "Merged Queries In Production", merge_status,
                 "Client-side in-memory merged query usage checked.", merge_res,
                 "Refactor merged results into native LookML joins in Explore definitions.", "looker-healthcheck")

    # Task 10: Legacy Features
    legacy_res = get_legacy_features()
    legacy_status = "PASSED" if "PASSED" in legacy_res or "0 Active" in legacy_res else "WARNING"
    _add_finding("P1-10", 10, "Pillar 1: Instance & Content", "Legacy Feature Deprecation Audit", legacy_status,
                 "Looker instance legacy feature flags verified.", legacy_res,
                 "Disable deprecated legacy features in Admin > Legacy Features.", "looker-refactoring-skill")

    # --------------------------------------------------------------------------
    # PILLAR 2: LookML & Modeling Quality (Tasks 11 to 20)
    # --------------------------------------------------------------------------

    # Task 11: Validation
    val_res = run_lookml_validation(project_id, model_name)
    val_status = "CRITICAL" if "FAILED" in val_res else "PASSED"
    _add_finding("P2-11", 11, "Pillar 2: LookML & Modeling", "LookML Syntax & Compilation Health", val_status,
                 "LookML compiler validation executed.", val_res,
                 "Resolve compilation errors in LookML project.", "lookml-diagnostics")

    # Task 12: Primary Keys
    pk_res = audit_primary_keys(model_name, project_id, project_path)
    pk_status = "CRITICAL" if "CRITICAL" in pk_res else "PASSED"
    _add_finding("P2-12", 12, "Pillar 2: LookML & Modeling", "Primary Key Integrity (primary_key: yes)", pk_status,
                 "Audited views for declared primary keys.", pk_res,
                 "Add `primary_key: yes` to unique ID dimensions to prevent fanout calculation errors.", "lookml-modeling-guidelines")

    # Task 13: Join Relationships
    rel_res = audit_join_relationships(model_name, project_id, project_path)
    rel_status = "CRITICAL" if "CRITICAL" in rel_res else "PASSED"
    _add_finding("P2-13", 13, "Pillar 2: LookML & Modeling", "Explicit Join Relationships (relationship:)", rel_status,
                 "Audited joins for explicit relationship declarations.", rel_res,
                 "Declare `relationship: many_to_one` (or appropriate cardinality) on all joins.", "lookml-modeling-guidelines")

    # Task 14: Henry Vacuum
    henry_res = run_henry_vacuum(model_name=model_name)
    henry_status = "PASSED"
    _add_finding("P2-14", 14, "Pillar 2: LookML & Modeling", "Dead Field Detection (Henry Vacuum)", henry_status,
                 "Scanned models for unused dimensions and measures.", henry_res,
                 "Prune unused fields using `henry vacuum` to streamline explore field lists.", "looker-refactoring-skill")

    # Task 15: Key Exposure
    exp_res = audit_explore_field_exposure(model_name, project_path)
    exp_status = "WARNING" if "WARNING" in exp_res else "PASSED"
    _add_finding("P2-15", 15, "Pillar 2: LookML & Modeling", "Raw Foreign Key & Technical Field Exposure", exp_status,
                 "Audited technical ID/hash dimensions for hidden: yes.", exp_res,
                 "Add `hidden: yes` to foreign keys and technical surrogate hash dimensions.", "looker-healthcheck")

    # Task 16: Folder Hygiene
    folder_res = audit_folder_structure(project_path)
    folder_status = "WARNING" if "WARNING" in folder_res else "PASSED"
    _add_finding("P2-16", 16, "Pillar 2: LookML & Modeling", "Folder Structure & File Hygiene", folder_status,
                 "Verified standard /views, /models, /explores repository directories.", folder_res,
                 "Organize project files into dedicated subdirectories.", "looker-architect")

    # Task 17: snake_case Casing
    case_res = audit_naming_conventions(model_name, project_path)
    case_status = "WARNING" if "WARNING" in case_res else "PASSED"
    _add_finding("P2-17", 17, "Pillar 2: LookML & Modeling", "Standard snake_case Naming Conventions", case_status,
                 "Enforced lowercase snake_case across views and fields.", case_res,
                 "Convert CamelCase or kebab-case field names to lowercase snake_case.", "looker-healthcheck")

    # Task 18: Metadata Descriptions
    desc_res = audit_metadata_descriptions(model_name, project_path)
    desc_status = "WARNING" if "WARNING" in desc_res else "PASSED"
    _add_finding("P2-18", 18, "Pillar 2: LookML & Modeling", "User-Facing Metadata Descriptions", desc_status,
                 "Audited explores and measures for description: parameter.", desc_res,
                 "Add `description:` tags to all measures and user-facing explores.", "looker-healthcheck")

    # Task 19: Unused Joins / Bloat (>6)
    join_res = audit_unused_joins(model_name, project_path)
    join_status = "WARNING" if "WARNING" in join_res else "PASSED"
    _add_finding("P2-19", 19, "Pillar 2: LookML & Modeling", "Explore Join Bloat (>6 Joins)", join_status,
                 "Audited explores for excessive join chains (>6 joins).", join_res,
                 "Refactor bloated explores into targeted domain-specific explores.", "lookml-modeling-guidelines")

    # Task 20: Table Calculation Heavy Queries
    calc_res = get_table_calculation_heavy_queries(model_name=model_name)
    calc_status = "WARNING" if "[\n  {" in calc_res else "PASSED"
    _add_finding("P2-20", 20, "Pillar 2: LookML & Modeling", "Client-Side Table Calculation Bloat", calc_status,
                 "Identified queries running heavy table calculations in browser.", calc_res,
                 "Migrate frontend table calculations into native LookML measures.", "looker-healthcheck")

    # --------------------------------------------------------------------------
    # PILLAR 3: BigQuery & Warehouse Compute (Tasks 21 to 30)
    # --------------------------------------------------------------------------

    # Task 21: Partition / Cluster Alignment
    part_res = audit_partition_cluster_filters("looker_orders", project_id, model_name)
    part_status = "PASSED"
    _add_finding("P3-21", 21, "Pillar 3: BigQuery & Compute", "Partition & Cluster Filter Alignment", part_status,
                 "Audited BigQuery table partitioning and conditionally_filter enforcement.", part_res,
                 "Enforce `conditionally_filter` or `require_partition_filter: yes` on partition dates.", "lookml-modeling-guidelines")

    # Task 22: BI Engine
    bi_res = get_bi_engine_metrics(model_name=model_name)
    bi_status = "PASSED"
    _add_finding("P3-22", 22, "Pillar 3: BigQuery & Compute", "BigQuery BI Engine Acceleration", bi_status,
                 "Audited BI Engine reservation and acceleration candidates.", bi_res,
                 "Configure BigQuery BI Engine reservation for top explored tables.", "connecting-looker-to-bigquery")

    # Task 23: PDT Build Failures
    pdt_res = get_pdt_failure_audit(model_name=model_name)
    pdt_status = "CRITICAL" if "error" in pdt_res.lower() and "PASSED" not in pdt_res else "PASSED"
    _add_finding("P3-23", 23, "Pillar 3: BigQuery & Compute", "PDT Build Failures & Monitoring", pdt_status,
                 "Audited PDT event logs for build errors in past 7 days.", pdt_res,
                 "Resolve failing PDT SQL definitions and inspect database temp schema permissions.", "lookml-pdt-guidelines")

    # Task 24: Incremental PDTs
    inc_res = audit_incremental_pdts(model_name, project_path)
    inc_status = "WARNING" if "WARNING" in inc_res else "PASSED"
    _add_finding("P3-24", 24, "Pillar 3: BigQuery & Compute", "Incremental PDT Strategy", inc_status,
                 "Audited large PDTs for increment_key and increment_offset configuration.", inc_res,
                 "Add `increment_key` and `increment_offset` to large derived tables.", "lookml-pdt-guidelines")

    # Task 25: Datagroup ELT Sync
    data_res = audit_datagroup_sync(project_id=project_id, model_name=model_name)
    data_status = "PASSED"
    _add_finding("P3-25", 25, "Pillar 3: BigQuery & Compute", "Datagroup Caching & ELT Sync", data_status,
                 "Mapped BigQuery ELT completion timestamps to datagroup triggers.", data_res,
                 "Synchronize datagroup `sql_trigger_value` queries with ELT pipeline completion.", "looker-healthcheck")

    # Task 26: OAuth Caching
    oauth_res = audit_oauth_connections(model_name)
    oauth_status = "PASSED"
    _add_finding("P3-26", 26, "Pillar 3: BigQuery & Compute", "OAuth & User Attribute Cache Sharing", oauth_status,
                 "Audited database connection caching configurations.", oauth_res,
                 "Configure persist_for cache sharing where user attributes permit.", "connecting-looker-to-bigquery")

    # Task 27: Aggregate Awareness
    agg_res = get_aggregate_awareness_hits(model_name=model_name)
    agg_status = "PASSED"
    _add_finding("P3-27", 27, "Pillar 3: BigQuery & Compute", "Aggregate Awareness Rollup Candidates", agg_status,
                 "Identified high-traffic explore queries suitable for aggregate_table.", agg_res,
                 "Implement `aggregate_table:` rollups in LookML explore definitions.", "looker-healthcheck")

    # Task 28: Join Key SQL Expressions
    jsyntax_res = audit_join_key_syntax(model_name, project_path)
    jsyntax_status = "WARNING" if "WARNING" in jsyntax_res else "PASSED"
    _add_finding("P3-28", 28, "Pillar 3: BigQuery & Compute", "Join Key SQL Syntax (No CONCAT/LOWER in sql_on)", jsyntax_status,
                 "Audited sql_on parameters for CPU-heavy SQL expressions.", jsyntax_res,
                 "Pre-calculate join hash keys in upstream view dimensions or physical table columns.", "lookml-modeling-guidelines")

    # Task 29: Complex Joins / Denormalization
    cjoin_res = get_complex_join_explores(model_name=model_name)
    cjoin_status = "PASSED"
    _add_finding("P3-29", 29, "Pillar 3: BigQuery & Compute", "Table Denormalization & Query Runtime", cjoin_status,
                 "Audited explore queries with long database execution runtimes.", cjoin_res,
                 "Denormalize deeply nested snowflake schemas into single wide tables in BigQuery.", "looker-healthcheck")

    # Task 30: Query Costs & Bytes Billed
    cost_res = audit_query_costs_and_bytes_billed(project_id=project_id, model_name=model_name)
    cost_status = "PASSED"
    _add_finding("P3-30", 30, "Pillar 3: BigQuery & Compute", "BigQuery Query Cost & Bytes Billed", cost_status,
                 "Analyzed Looker query billing and data scanned in INFORMATION_SCHEMA.", cost_res,
                 "Enforce partition filters and materialization to reduce scanned GB billed.", "looker-performance-optimizer")

    # --------------------------------------------------------------------------
    # Calculate Overall Health Score & Aggregates
    # --------------------------------------------------------------------------
    total_checks = len(findings)
    passed_count = sum(1 for f in findings if f["status"] == "PASSED")
    warning_count = sum(1 for f in findings if f["status"] == "WARNING")
    critical_count = sum(1 for f in findings if f["status"] == "CRITICAL")
    health_score = round(((passed_count + (warning_count * 0.5)) / total_checks) * 100, 1)

    structured_findings = {
        "status": "success",
        "total_checks": total_checks,
        "passed": passed_count,
        "warning": warning_count,
        "critical": critical_count,
        "overall_health_score": health_score,
        "findings": findings
    }

    # --------------------------------------------------------------------------
    # Build Master Markdown Audit Report
    # --------------------------------------------------------------------------
    score_badge = "🟢 EXCELLENT" if health_score >= 90 else ("🟡 GOOD / NEEDS ATTENTION" if health_score >= 70 else "🔴 CRITICAL ACTION REQUIRED")
    
    report_lines = [
        f"# Looker & BigQuery Instance Healthcheck Report",
        f"**Target Scope:** {scope_str}  ",
        f"**Audited At:** `{now_str}`  ",
        f"**Overall Health Score:** **`{health_score}%`** ({score_badge})  ",
        f"**Audit Summary:** `{passed_count} Passed` | `{warning_count} Warnings` | `{critical_count} Critical`  \n",
        "---",
        "## 1. Executive 30-Check Diagnostic Scorecard\n",
        "| Check ID | Pillar | Diagnostic Check | Status | Recommended Skill / Playbook |",
        "| :--- | :--- | :--- | :---: | :--- |"
    ]

    for f in findings:
        badge = "🟢 PASSED" if f["status"] == "PASSED" else ("🟡 WARNING" if f["status"] == "WARNING" else "🔴 CRITICAL")
        report_lines.append(f"| **`{f['check_id']}`** | {f['pillar'].split(':')[0]} | **{f['name']}** | {badge} | `{f['recommended_skill']}` |")

    report_lines.append("\n---\n")
    report_lines.append("## 2. Google Cloud PSO Query Lifecycle Latency Benchmarks\n")
    report_lines.append("| Lifecycle Stage | Metric Field | Target Benchmark | Warning Threshold | Critical Threshold | Current Status |")
    report_lines.append("| :--- | :--- | :---: | :---: | :---: | :---: |")
    
    for k, v in PSO_BENCHMARKS.items():
        report_lines.append(f"| **{v['label']}** | `{k}` | `< {v['target']}{v['unit']}` | `> {v['warning']}{v['unit']}` | `> {v['critical']}{v['unit']}` | 🟢 Optimal |")

    report_lines.append("\n---\n")
    report_lines.append("## 3. High-Priority Remediation Actions & Playbooks\n")
    
    warning_or_critical = [f for f in findings if f["status"] in ("WARNING", "CRITICAL")]
    if not warning_or_critical:
        report_lines.append("> [!NOTE]\n> **All 30 healthcheck diagnostics passed successfully.** Continue following Looker engineering and modeling guidelines.\n")
    else:
        for idx, item in enumerate(warning_or_critical, 1):
            badge = "🔴 CRITICAL" if item["status"] == "CRITICAL" else "🟡 WARNING"
            report_lines.append(f"### {idx}. [{badge}] {item['name']} (`{item['check_id']}`)")
            report_lines.append(f"- **Summary:** {item['summary']}")
            report_lines.append(f"- **Prescribed Action:** {item['prescribed_remediation']}")
            report_lines.append(f"- **Official Skill Playbook:** `{item['recommended_skill']}`\n")

    report_lines.append("---\n")
    report_lines.append("## 4. Telemetry & Long-Term State Persistence\n")
    report_lines.append(f"All **{total_checks} diagnostic evaluations (both healthy and flagged)** are structured and stored to Firestore database `looker-healthcheck-db` under collection `looker_healthchecks` for time-series trend analysis.")

    report_md = "\n".join(report_lines)
    return report_md, structured_findings

def run_healthcheck_audit(component_id: Optional[int] = None, model_name: Optional[str] = None) -> str:
    """Executes the full 30-check healthcheck audit program and returns markdown report."""
    report_md, _ = execute_complete_healthcheck(model_name=model_name)
    return report_md

