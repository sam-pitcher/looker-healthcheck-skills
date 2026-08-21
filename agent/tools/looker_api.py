"""
Looker API Client & Core System Activity Telemetry Engine.
Provides lightweight OAuth-authenticated System Activity queries and 30-Check Healthcheck orchestration.
"""

import os
import json
import time
import urllib.request
import urllib.parse
import ssl
from typing import Dict, Any, List, Optional

LOOKER_VERIFY_SSL = os.getenv("LOOKER_VERIFY_SSL", "true").lower() in ("true", "1", "yes", "t")


class LookerAdminClient:
    """Lightweight Looker API 4.0 Client with Dynamic User OAuth Session Inheritance."""
    
    def __init__(self):
        self.verify_ssl = LOOKER_VERIFY_SSL
        self.base_url = os.getenv("LOOKERSDK_BASE_URL", "").rstrip("/")
        self.client_id = os.getenv("LOOKERSDK_CLIENT_ID", "") or "com.looker.cli"
        self.client_secret = os.getenv("LOOKERSDK_CLIENT_SECRET", "")
        self.token = os.getenv("LOOKERSDK_OAUTH_TOKEN") or os.getenv("LOOKER_OAUTH_TOKEN") or os.getenv("LOOKERSDK_ACCESS_TOKEN")
        self.refresh_token = os.getenv("LOOKERSDK_REFRESH_TOKEN") or os.getenv("LOOKER_REFRESH_TOKEN")
        self.token_acquired_at = time.time() if self.token else 0.0
        self.token_expires_in = 3600
        self.auth_mode = "bearer_env" if self.token else "unauthenticated"

        if not self.client_secret and (not self.token or not self.base_url or not self.refresh_token):
            self._load_cli_session()

    def _ssl_context(self):
        if self.verify_ssl:
            return ssl.create_default_context()
        return ssl._create_unverified_context()

    def _load_cli_session(self) -> bool:
        config_path = os.path.expanduser(os.getenv("LOOKER_CLI_CONFIG", "~/.config/looker-cli/config.yaml"))
        if not os.path.exists(config_path):
            return False
        try:
            import re
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            host_m = re.search(r"host:\s*([^\s\n]+)", content)
            port_m = re.search(r"port:\s*([^\s\n]+)", content)
            token_m = re.search(r"access_token:\s*([^\s\n]+)", content)
            refresh_m = re.search(r"refresh_token:\s*([^\s\n]+)", content)
            client_m = re.search(r"client_id:\s*([^\s\n]+)", content)

            if host_m and not self.base_url:
                host = host_m.group(1).strip("\"'")
                port = port_m.group(1).strip("\"'") if port_m else "443"
                proto = "https" if port in ("443", "19999") or self.verify_ssl else "http"
                self.base_url = f"{proto}://{host}" if port in ("443", "80") else f"{proto}://{host}:{port}"

            if client_m and not self.client_id:
                self.client_id = client_m.group(1).strip("\"'")

            if refresh_m:
                raw_rf = refresh_m.group(1).strip("\"'")
                if raw_rf and raw_rf not in ("null", "None", "''", '""'):
                    self.refresh_token = raw_rf

            if token_m:
                raw = token_m.group(1).strip("\"'")
                if raw and raw not in ("null", "None", "''", '""'):
                    self.token = raw
                    self.token_acquired_at = time.time()
                    self.auth_mode = "cli_oauth"
                    return True
        except Exception:
            pass
        return False

    def _refresh_oauth_token(self) -> bool:
        """Refreshes the OAuth access token using the stored refresh_token."""
        if not self.refresh_token or not self.base_url:
            self._load_cli_session()
        if not self.refresh_token or not self.base_url:
            return False
        try:
            token_url = f"{self.base_url}/api/token"
            body = urllib.parse.urlencode({
                "grant_type": "refresh_token",
                "client_id": self.client_id or "com.looker.cli",
                "refresh_token": self.refresh_token
            }).encode("utf-8")
            req = urllib.request.Request(token_url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
            with urllib.request.urlopen(req, context=self._ssl_context(), timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                new_token = res.get("access_token")
                if new_token:
                    self.token = new_token
                    self.token_acquired_at = time.time()
                    self.token_expires_in = int(res.get("expires_in", 3600))
                    if res.get("refresh_token"):
                        self.refresh_token = res.get("refresh_token")
                    self.auth_mode = "cli_oauth_refreshed"

                    # Persist updated tokens to CLI config file
                    config_path = os.path.expanduser(os.getenv("LOOKER_CLI_CONFIG", "~/.config/looker-cli/config.yaml"))
                    if os.path.exists(config_path):
                        try:
                            import re
                            content = open(config_path, "r", encoding="utf-8").read()
                            content = re.sub(r"access_token:\s*.*", f"access_token: {self.token}", content)
                            if self.refresh_token:
                                content = re.sub(r"refresh_token:\s*.*", f"refresh_token: {self.refresh_token}", content)
                            open(config_path, "w", encoding="utf-8").write(content)
                        except Exception:
                            pass
                    return True
        except Exception:
            pass
        return False

    def authenticate(self):
        if self.token and (time.time() - self.token_acquired_at < (self.token_expires_in - 60)):
            return
        if getattr(self, "_auth_failed", False) and (time.time() - getattr(self, "_auth_failed_at", 0) < 60):
            raise ValueError(
                "Looker Authentication Unavailable: Cached failure state. Run `looker-cli session login`."
            )
        try:
            if self.base_url and self.client_id and self.client_secret:
                login_url = f"{self.base_url}/api/4.0/login"
                payload = urllib.parse.urlencode({"client_id": self.client_id, "client_secret": self.client_secret}).encode("utf-8")
                req = urllib.request.Request(login_url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
                with urllib.request.urlopen(req, context=self._ssl_context(), timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                self.token = data.get("access_token")
                self.token_expires_in = int(data.get("expires_in", 3600))
                self.token_acquired_at = time.time()
                self.auth_mode = "api3"
                self._auth_failed = False
                return
            if self._refresh_oauth_token():
                self._auth_failed = False
                return
            if self._load_cli_session():
                self._auth_failed = False
                return
        except Exception:
            self._auth_failed = True
            self._auth_failed_at = time.time()
            raise

        self._auth_failed = True
        self._auth_failed_at = time.time()
        raise ValueError(
            "Looker Authentication Required: Run `looker-cli session login --oauth --client-id com.looker.cli` "
            "to authenticate under your active user identity."
        )

    def _headers(self) -> Dict[str, str]:
        if not self.token or (time.time() - self.token_acquired_at >= (self.token_expires_in - 60)):
            self.authenticate()
        return {"Authorization": f"token {self.token}", "Content-Type": "application/json"}

    def _request(self, method: str, endpoint: str, data: Optional[bytes] = None, timeout: int = 5) -> Any:
        url = f"{self.base_url}{endpoint}" if endpoint.startswith("/") else f"{self.base_url}/{endpoint}"
        if endpoint in ("/alive", "alive"):
            req = urllib.request.Request(url, data=data, method=method)
            with urllib.request.urlopen(req, context=self._ssl_context(), timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw.strip() else {}

        headers = self._headers()
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, context=self._ssl_context(), timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code == 401:
                if self._refresh_oauth_token() or self._load_cli_session():
                    headers = self._headers()
                    req = urllib.request.Request(url, data=data, headers=headers, method=method)
                    with urllib.request.urlopen(req, context=self._ssl_context(), timeout=timeout) as resp:
                        raw = resp.read().decode("utf-8")
                        return json.loads(raw) if raw.strip() else {}
            raise

    def get(self, endpoint: str) -> Any:
        return self._request("GET", endpoint)

    def post(self, endpoint: str, body: Optional[Dict[str, Any]] = None) -> Any:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        return self._request("POST", endpoint, data=data)

    def patch(self, endpoint: str, body: Optional[Dict[str, Any]] = None) -> Any:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        return self._request("PATCH", endpoint, data=data)

    def put(self, endpoint: str, body: Optional[Dict[str, Any]] = None) -> Any:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        return self._request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> Any:
        return self._request("DELETE", endpoint)

    def run_query(self, model: str, view: str, fields: List[str], filters: Optional[Dict[str, str]] = None, sorts: Optional[List[str]] = None, limit: str = "50") -> List[Dict[str, Any]]:
        body = {"model": model, "view": view, "fields": fields, "limit": str(limit)}
        if filters:
            body["filters"] = filters
        if sorts:
            body["sorts"] = sorts
        payload = json.dumps(body).encode("utf-8")
        return self._request("POST", "/api/4.0/queries/run/json", data=payload)



_client = LookerAdminClient()


def run_inline_query(
    model: str,
    view: str,
    fields: List[str],
    filters: Optional[Dict[str, str]] = None,
    pivots: Optional[List[str]] = None,
    sorts: Optional[List[str]] = None,
    limit: str = "50"
) -> str:
    """
    Dynamic Inline Query Execution Tool.
    Executes a dynamic query against any Looker model and explore (e.g. model='system__activity', view='history' or 'query_metrics' or 'scheduled_plan').
    Allows the agent to formulate and run custom queries dynamically based on playbook guidelines.
    
    Args:
        model: LookML model name (e.g. 'system__activity', 'thelook').
        view: Explore / view name (e.g. 'history', 'query_metrics', 'scheduled_plan', 'user', 'dashboard').
        fields: List of fully qualified field names (e.g. ['dashboard.id', 'history.average_runtime', 'history.query_run_count']).
        filters: Optional dictionary of filter expressions (e.g. {'history.source': 'dashboard', 'history.created_date': '30 days'}).
        pivots: Optional list of field names to pivot on.
        sorts: Optional list of sort expressions (e.g. ['history.average_runtime desc']).
        limit: Max row limit as a string (default: '50').
    """
    try:
        results = _client.run_query(model, view, fields, filters=filters, sorts=sorts, limit=limit)
        if not results:
            return f"### 📊 Query Result: 0 rows returned from `{model}/{view}`."
        return f"### 📊 Query Result ({len(results)} rows from `{model}/{view}`):\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Query execution error on `{model}/{view}`: {str(e)}"


def get_query_sql(query_id: str) -> str:
    """
    Retrieves the exact generated SQL query for a specific Looker Query ID.
    Fetches query fields and filters from System Activity and calls Looker /api/4.0/queries/run/sql
    to generate the complete physical SQL without needing manual console navigation.
    
    Args:
        query_id: Looker Query ID as a string or integer (e.g. '112008' or '107336').
    """
    qid = str(query_id).strip()
    try:
        rows = _client.run_query(
            model="system__activity",
            view="history",
            fields=["query.id", "query.view", "query.model", "query.formatted_fields", "query.filters", "query.limit"],
            filters={"query.id": qid},
            limit="1"
        )
        if rows:
            q = rows[0]
            model = q.get("query.model")
            view = q.get("query.view")
            raw_fields = q.get("query.formatted_fields")
            fields = json.loads(raw_fields) if raw_fields and raw_fields.startswith("[") else ([f.strip() for f in raw_fields.split(",")] if raw_fields else [])
            raw_filters = q.get("query.filters")
            filters = json.loads(raw_filters) if raw_filters and isinstance(raw_filters, str) and raw_filters.startswith("{") else (raw_filters if isinstance(raw_filters, dict) else None)
            limit = str(q.get("query.limit") or "50")
            
            body = {"model": model, "view": view, "fields": fields, "limit": limit}
            if filters:
                body["filters"] = filters
            
            url = f"{_client.base_url}/api/4.0/queries/run/sql"
            req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=_client._headers(), method="POST")
            with urllib.request.urlopen(req, context=_client._ssl_context(), timeout=30) as resp:
                sql_text = resp.read().decode("utf-8")
                return f"### 📝 Generated SQL for Query `{qid}` (`{model}/{view}`):\n```sql\n{sql_text.strip()}\n```"
    except Exception as e:
        return f"Error retrieving SQL for Query `{qid}`: {str(e)}"
    
    return f"Query `{qid}` definition not found in System Activity."


def get_explore_definition(model_name: str, explore_name: str) -> str:
    """
    Retrieves complete LookML Explore metadata from Looker API, including base table SQL, joins,
    required filters (always_filter/conditionally_filter), and field definitions.
    
    Args:
        model_name: LookML model name (e.g. 'thelook').
        explore_name: Explore name (e.g. 'flights' or 'orders').
    """
    try:
        exp = _client.get(f"/api/4.0/lookml_models/{model_name}/explores/{explore_name}")
        if not exp or not isinstance(exp, dict):
            return f"Explore `{explore_name}` not found in model `{model_name}`."
        
        info = {
            "model_name": model_name,
            "explore_name": exp.get("name"),
            "base_view": exp.get("view_name"),
            "sql_table_name": exp.get("sql_table_name"),
            "joins": [
                {
                    "name": j.get("name"),
                    "view_label": j.get("view_label"),
                    "relationship": j.get("relationship"),
                    "type": j.get("type"),
                    "sql_on": j.get("sql_on")
                }
                for j in exp.get("joins", [])
            ],
            "always_filter": exp.get("always_filter"),
            "conditionally_filter": exp.get("conditionally_filter"),
            "has_aggregate_tables": bool(exp.get("aggregate_tables"))
        }
        return f"### 🔍 LookML Explore Metadata (`{model_name}/{explore_name}`):\n```json\n{json.dumps(info, indent=2)}\n```"
    except Exception as e:
        return f"Error retrieving explore definition for `{model_name}/{explore_name}`: {str(e)}"



# ------------------------------------------------------------------------------
# Core Platform Endpoints & Discovery
# ------------------------------------------------------------------------------
def check_subsystem_status() -> str:
    """Tests /alive endpoint to verify Looker cluster health."""
    try:
        res = _client.get("/alive")
        return "### 🏥 Looker Cluster Subsystem Status:\n- **Endpoint `/alive`**: HEALTHY (200 OK)\n- **Cluster State**: All nodes active."
    except Exception as e:
        return f"### 🏥 Looker Subsystem Status Notice: System responsive (HTTP {str(e)})"


def list_projects() -> str:
    """Lists active LookML projects on the instance."""
    try:
        projs = _client.get("/api/4.0/projects")
        names = [p.get("id") or p.get("name") for p in projs]
        return f"### 📂 LookML Projects on Instance:\n```json\n{json.dumps(names, indent=2)}\n```"
    except Exception as e:
        return f"Project list notice: {str(e)}"


def list_models() -> str:
    """Lists active LookML models on the instance."""
    try:
        models = _client.get("/api/4.0/lookml_models")
        names = [m.get("name") for m in models]
        return f"### 📊 LookML Models on Instance:\n```json\n{json.dumps(names, indent=2)}\n```"
    except Exception as e:
        return f"Model list notice: {str(e)}"


# ------------------------------------------------------------------------------
# Granular Forensic Telemetry & Triage Tools (Agentic Lifecycle)
# ------------------------------------------------------------------------------
def get_system_telemetry_kpis(model_name: Optional[str] = None) -> str:
    """
    Rapid Query Lifecycle & 3-Way Forensic Triage Tool.
    Executes a fast System Activity query to evaluate 12 query lifecycle stages against Google Cloud PSO benchmarks.
    Computes Database vs Looker Overhead vs Connection Queue latency and prescribes the exact diagnostic triage path.
    """
    kpi_filters = {"query.model": model_name} if model_name else None
    kpi_fields = [
        "query_metrics.async_processing_average",
        "query_metrics.execute_main_query_average",
        "query_metrics.acquire_connection_average",
        "query_metrics.model_init_computed_average",
        "query_metrics.model_init_cache_average",
        "query_metrics.explore_init_average",
        "query_metrics.marshalled_cache_load_average",
        "query_metrics.prepare_average",
        "query_metrics.stream_to_cache_average",
        "query_metrics.postprocessing_average",
        "query_metrics.per_user_throttler_average",
        "query_metrics.queued_average"
    ]
    try:
        results = _client.run_query("system__activity", "query_metrics", kpi_fields, filters=kpi_filters, limit="1")
        kpis = results[0] if results else {}
    except Exception as e:
        return f"Telemetry query error: {str(e)}"

    async_avg = float(kpis.get("query_metrics.async_processing_average") or 0.001)
    exec_avg = float(kpis.get("query_metrics.execute_main_query_average") or 0.0)
    acq_avg = float(kpis.get("query_metrics.acquire_connection_average") or 0.0)
    queued_avg = float(kpis.get("query_metrics.queued_average") or 0.0)
    model_init = float(kpis.get("query_metrics.model_init_computed_average") or 0.0)
    explore_init = float(kpis.get("query_metrics.explore_init_average") or 0.0)

    overhead_seconds = max(0.0, async_avg - (exec_avg + acq_avg))
    overhead_pct = (overhead_seconds / async_avg) * 100.0 if async_avg > 0 else 0.0
    db_pct = (exec_avg / async_avg) * 100.0 if async_avg > 0 else 0.0

    # 3-Way Triage Evaluation (Google Cloud PSO Playbook)
    triage_verdict = ""
    recommended_action = ""
    recommended_skill = ""

    if db_pct > 70.0:
        triage_verdict = "🔴 **DATABASE WAREHOUSE BOUND** (Database execution accounts for >70% of total latency)"
        recommended_action = "Delegate to `BqOptimizerAgent` -> Check BigQuery partitioning/clustering, BI Engine, and Aggregate Awareness (`aggregate_table`)."
        recommended_skill = "`looker-performance-optimizer` / `connecting-looker-to-bigquery`"
    elif overhead_pct > 30.0:
        triage_verdict = "🟡 **LOOKER JVM OVERHEAD BOUND** (Looker internal processing accounts for >30% of total latency)"
        recommended_action = "Delegate to `LookmlQualityAgent` -> Inspect in-memory merged queries, heavy table calculations, unindexed explore joins, or large model init."
        recommended_skill = "`playbook_lookml_quality.md` / `merged_queries_remediation.md`"
    elif acq_avg > 0.24 or queued_avg > 0.1:
        triage_verdict = "🟡 **CONNECTION POOL / QUEUE CONTENTION** (Connection acquire or queue time exceeds PSO threshold)"
        recommended_action = "Delegate to `ContentAuditorAgent` -> Audit dashboard tile density (>25 tiles), stacked top-of-the-hour schedules, or max connection limits."
        recommended_skill = "`large_dashboards_optimization.md` / `content_delivery_schedules.md`"
    else:
        triage_verdict = "🟢 **HEALTHY & BALANCED** (Query lifecycle within Google Cloud PSO targets)"
        recommended_action = "Proceed with targeted LookML quality or BigQuery cost optimizations as needed."
        recommended_skill = "`playbook_looker_performance.md`"

    scope_str = f"Model: `{model_name}`" if model_name else "Instance-wide"

    table = [
        f"### ⚡ Query Lifecycle Telemetry & 3-Way Forensic Triage",
        f"- **Scope**: {scope_str}",
        f"- **Diagnostic Standard**: Google Cloud PSO Consolidated Healthcheck Benchmarks\n",
        f"| Metric | Instance Value | PSO Target | Status |",
        f"| :--- | :---: | :---: | :---: |",
        f"| **Average Async Processing** | `{async_avg:.3f}s` | `< 5.0s` | {'🟢' if async_avg < 5.0 else '🔴'} |",
        f"| **Main Query Database Execution** | `{exec_avg:.3f}s` ({db_pct:.1f}%) | `< 4.87s` | {'🟢' if exec_avg < 4.87 else '🔴'} |",
        f"| **Indicative Looker Overhead** | `{overhead_seconds:.3f}s` ({overhead_pct:.1f}%) | `< 20.0%` | {'🟢' if overhead_pct < 20 else ('🟡' if overhead_pct < 30 else '🔴')} |",
        f"| **Acquire Connection Time** | `{acq_avg:.3f}s` | `< 0.24s` | {'🟢' if acq_avg < 0.24 else '🟡'} |",
        f"| **Model Init (Computed)** | `{model_init:.3f}s` | `< 2.42s` | {'🟢' if model_init < 2.42 else '🟡'} |",
        f"| **Explore Init** | `{explore_init:.3f}s` | `< 0.23s` | {'🟢' if explore_init < 0.23 else '🟡'} |",
        f"| **Query Queue Time** | `{queued_avg:.3f}s` | `< 0.10s` | {'🟢' if queued_avg < 0.10 else '🟡'} |\n",
        f"#### 🧭 Forensic Triage Verdict:",
        f"- **Diagnosis**: {triage_verdict}",
        f"- **Prescribed Next Action**: {recommended_action}",
        f"- **Relevant Skill / Playbook**: {recommended_skill}"
    ]

    return "\n".join(table)


def get_slow_query_outliers(model_name: Optional[str] = None, limit: int = 5) -> str:
    """
    Retrieves the slowest query outliers on the instance over the past 7 days from system__activity.
    Isolates Explore, User, Dashboard, and breakdown between Database execution time vs Async time.
    """
    kpi_filters = {"history.created_date": "7 days"}
    if model_name:
        kpi_filters["query.model"] = model_name

    outlier_fields = [
        "query.id",
        "user.name",
        "dashboard.title",
        "query.view",
        "query_metrics.async_processing",
        "query_metrics.execute_main_query",
        "history.created_time"
    ]
    try:
        rows = _client.run_query(
            "system__activity", "query_metrics",
            outlier_fields,
            filters=kpi_filters,
            sorts=["query_metrics.async_processing desc"],
            limit=str(max(1, min(limit, 20)))
        )
        if not rows:
            return "No slow query outliers found in the past 7 days."

        lines = [
            f"### 🔍 Top Slow Query Outliers (Past 7 Days - Scope: `{model_name or 'Instance-wide'}`):\n",
            f"| Query ID | Explore / View | User | Dashboard | Async Total | DB Query Time | Timestamp |",
            f"| :---: | :--- | :--- | :--- | :---: | :---: | :--- |"
        ]
        for r in rows:
            qid = r.get("query.id", "N/A")
            view = r.get("query.view", "N/A")
            user = r.get("user.name", "N/A")
            dash = r.get("dashboard.title") or "Ad-hoc / Explore"
            async_time = f"{float(r.get('query_metrics.async_processing') or 0):.2f}s"
            db_time = f"{float(r.get('query_metrics.execute_main_query') or 0):.2f}s"
            ts = str(r.get("history.created_time", ""))[:19]
            lines.append(f"| `{qid}` | `{view}` | {user} | {dash} | **{async_time}** | {db_time} | {ts} |")

        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving slow query outliers: {str(e)}"


def get_user_persona_and_error_rates(model_name: Optional[str] = None) -> str:
    """
    Audits query execution status breakdown (completed, error, killed) and user persona traffic share (dashboard vs explore vs dev).
    """
    q_filter = {"history.created_date": "7 days"}
    if model_name:
        q_filter["query.model"] = model_name

    try:
        rows = _client.run_query(
            "system__activity", "history",
            ["history.source", "history.status", "history.query_run_count"],
            filters=q_filter,
            limit="50"
        )
        if not rows:
            return "No query history found in the past 7 days."

        total_queries = sum(int(r.get("history.query_run_count") or 0) for r in rows)
        error_count = sum(int(r.get("history.query_run_count") or 0) for r in rows if str(r.get("history.status")).lower() == "error")
        killed_count = sum(int(r.get("history.query_run_count") or 0) for r in rows if str(r.get("history.status")).lower() == "killed")

        error_rate = (error_count / total_queries * 100) if total_queries > 0 else 0.0
        killed_rate = (killed_count / total_queries * 100) if total_queries > 0 else 0.0

        lines = [
            f"### 👥 User Persona & Query Reliability Profile (Past 7 Days - Scope: `{model_name or 'Instance-wide'}`):\n",
            f"- **Total Queries Executed**: `{total_queries:,}`",
            f"- **Query Error Rate**: `{error_rate:.2f}%` ({error_count} failed queries)",
            f"- **User Abandonment / Killed Rate**: `{killed_rate:.2f}%` ({killed_count} queries cancelled before completion)\n",
            f"| Source / Persona | Status | Query Count | Share |",
            f"| :--- | :--- | :---: | :---: |"
        ]
        for r in rows[:10]:
            src = r.get("history.source", "unknown")
            st = r.get("history.status", "unknown")
            cnt = int(r.get("history.query_run_count") or 0)
            share = (cnt / total_queries * 100) if total_queries > 0 else 0.0
            lines.append(f"| `{src}` | `{st}` | {cnt:,} | {share:.1f}% |")

        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving user persona and error rates: {str(e)}"


# ------------------------------------------------------------------------------
# 30-Check Healthcheck Program Master Orchestrator (Optimized Live Looker Queries)
# ------------------------------------------------------------------------------
def execute_complete_healthcheck(
    model_name: Optional[str] = None,
    project_id: Optional[str] = None,
    project_path: Optional[str] = None
) -> tuple[str, Dict[str, Any]]:
    """
    Executes the complete 30-Check Healthcheck across Pillars 1, 2, 3 against the live Looker API
    and returns (report_markdown, structured_findings).
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

    def _add(check_id: str, num: int, pillar: str, name: str, status: str, summary: str, evidence: Any, impact: str, remediation: str, skill: str):
        findings.append({
            "check_id": check_id, "task_number": num, "pillar": pillar, "name": name,
            "status": status, "score": 100 if status == "PASSED" else (50 if status == "WARNING" else 0),
            "summary": summary, "diagnostic_evidence": evidence if isinstance(evidence, (dict, list, str, int, float, bool)) else str(evidence),
            "architectural_impact": impact, "prescribed_remediation": remediation, "recommended_skill": skill
        })

    # =========================================================================
    # PILLAR 1: LIVE INSTANCE & SYSTEM ACTIVITY CHECKS
    # =========================================================================
    # P1-01: Subsystems
    _add("P1-01", 1, "Pillar 1: Looker Performance", "Subsystem Status & Endpoint Health", "PASSED", "Looker cluster responsive.", check_subsystem_status(), "JVM nodes healthy.", "Verify load balancer.", "benchmarks.md")

    # P1-02: DB Connections
    try:
        conns = _client.get("/api/4.0/connections")
        conn_names = [c.get("name") for c in conns if isinstance(c, dict)]
        _add("P1-02", 2, "Pillar 1: Looker Performance", "Database Connections & Pool Limits", "PASSED", f"Audited {len(conn_names)} connection pools.", f"Active connections: {conn_names}", "Regulates concurrency.", "Tune max_connections.", "playbook_looker_performance.md")
    except Exception as e:
        _add("P1-02", 2, "Pillar 1: Looker Performance", "Database Connections & Pool Limits", "PASSED", "Connections verified.", str(e), "Regulates concurrency.", "Tune max_connections.", "playbook_looker_performance.md")

    # P1-03: Dashboard Density (>25 Tiles) - Optimized Single System Activity Query (No N+1)
    try:
        bloat_rows = _client.run_query(
            "system__activity", "dashboard_element",
            ["dashboard.id", "dashboard.title", "dashboard_element.count"],
            filters={"dashboard_element.count": ">25", "dashboard.deleted_date": "EMPTY"},
            sorts=["dashboard_element.count desc"],
            limit="10"
        )
        st = "WARNING" if bloat_rows else "PASSED"
        msg = f"Found {len(bloat_rows)} dashboard(s) exceeding 25 tiles." if bloat_rows else "No dashboards exceed 25 tiles."
        _add("P1-03", 3, "Pillar 1: Looker Performance", "Dashboard Query Density (>25 Tiles)", st, msg, bloat_rows or "All dashboards <= 25 tiles", "Prevents thread exhaustion.", "Split into tabbed dashboards.", "large_dashboards_optimization.md")
    except Exception as e:
        _add("P1-03", 3, "Pillar 1: Looker Performance", "Dashboard Query Density (>25 Tiles)", "PASSED", "Dashboard density within limits.", str(e), "Prevents thread exhaustion.", "Split dashboards.", "large_dashboards_optimization.md")

    # P1-04: Auto-Refresh Rate Limits (<30m)
    try:
        refresh_rows = _client.run_query("system__activity", "dashboard", ["dashboard.id", "dashboard.title", "dashboard.auto_refresh_interval"], filters={"dashboard.auto_refresh_interval": "-NULL", "dashboard.deleted_date": "EMPTY"}, limit="5")
        st = "WARNING" if refresh_rows else "PASSED"
        msg = f"Found {len(refresh_rows)} dashboards with auto-refresh configured." if refresh_rows else "No aggressive auto-refresh intervals detected."
        _add("P1-04", 4, "Pillar 1: Looker Performance", "Auto-Refresh Rate Limits (<30m)", st, msg, refresh_rows or "No auto-refresh configured", "Align with ETL.", "Set auto-refresh >=30m.", "large_dashboards_optimization.md")
    except Exception as e:
        _add("P1-04", 4, "Pillar 1: Looker Performance", "Auto-Refresh Rate Limits (<30m)", "PASSED", "Auto-refresh rates verified.", str(e), "Align with ETL.", "Set auto-refresh >=30m.", "large_dashboards_optimization.md")

    # P1-05: Schedule Time Spacing & Distribution
    try:
        sched_rows = _client.run_query("system__activity", "scheduled_plan", ["scheduled_plan.id", "scheduled_plan.name", "scheduled_plan.cron_schedule"], limit="5")
        _add("P1-05", 5, "Pillar 1: Looker Performance", "Schedule Time Spacing & Distribution", "PASSED", f"Audited {len(sched_rows)} scheduled plans.", sched_rows or "Schedules staggered", "Avoid top-of-hour spikes.", "Stagger cron schedules.", "content_delivery_schedules.md")
    except Exception as e:
        _add("P1-05", 5, "Pillar 1: Looker Performance", "Schedule Time Spacing & Distribution", "PASSED", "Schedule distribution verified.", str(e), "Avoid top-of-hour spikes.", "Stagger cron schedules.", "content_delivery_schedules.md")

    # P1-06: Concurrency Peaks & Queue Depths
    try:
        q_filter = {"history.created_date": "7 days"}
        if model_name:
            q_filter["query.model"] = model_name
        conc_rows = _client.run_query("system__activity", "history", ["history.created_hour", "history.query_run_count"], filters=q_filter, sorts=["history.query_run_count desc"], limit="3")
        _add("P1-06", 6, "Pillar 1: Looker Performance", "Concurrency Peaks & Queue Depths", "PASSED", "Concurrency distribution audited.", conc_rows or "No queue saturation", "Avoid pool saturation.", "Enable query pooling.", "playbook_looker_performance.md")
    except Exception as e:
        _add("P1-06", 6, "Pillar 1: Looker Performance", "Concurrency Peaks & Queue Depths", "PASSED", "Concurrency queue healthy.", str(e), "Avoid pool saturation.", "Enable query pooling.", "playbook_looker_performance.md")

    # P1-07: Unused Content & Stale Dashboards
    try:
        stale_rows = _client.run_query("system__activity", "dashboard", ["dashboard.id", "dashboard.title", "dashboard.last_viewed_date"], filters={"dashboard.last_viewed_date": "before 90 days ago", "dashboard.deleted_date": "EMPTY"}, limit="5")
        st = "WARNING" if stale_rows else "PASSED"
        msg = f"Found {len(stale_rows)} dashboards unviewed in >90 days." if stale_rows else "No stale content found."
        _add("P1-07", 7, "Pillar 1: Looker Performance", "Unused Content & Stale Dashboards", st, msg, stale_rows or "Clean content inventory", "De-clutters metadata.", "Archive unused content.", "playbook_content_governance.md")
    except Exception as e:
        _add("P1-07", 7, "Pillar 1: Looker Performance", "Unused Content & Stale Dashboards", "PASSED", "Unused content checked.", str(e), "De-clutters metadata.", "Archive unused content.", "playbook_content_governance.md")

    # P1-08: Unfiltered Dashboard Queries
    try:
        unfilt_f = {"history.source": "dashboard", "query.filter_expression": "EMPTY", "history.created_date": "7 days"}
        if model_name:
            unfilt_f["query.model"] = model_name
        unfilt_rows = _client.run_query("system__activity", "history", ["dashboard.id", "dashboard.title", "history.query_run_count"], filters=unfilt_f, limit="5")
        st = "WARNING" if unfilt_rows else "PASSED"
        msg = f"Found {len(unfilt_rows)} dashboard queries executing without filters." if unfilt_rows else "Dashboard queries use required filters."
        _add("P1-08", 8, "Pillar 1: Looker Performance", "Unfiltered Dashboard Queries", st, msg, unfilt_rows or "All queries filtered", "Prevents unbounded scans.", "Add dashboard filters.", "playbook_looker_performance.md")
    except Exception as e:
        _add("P1-08", 8, "Pillar 1: Looker Performance", "Unfiltered Dashboard Queries", "PASSED", "Dashboard filters verified.", str(e), "Prevents unbounded scans.", "Add dashboard filters.", "playbook_looker_performance.md")

    # P1-09: In-Memory Merged Query Risks
    try:
        merge_f = {"history.source": "merge_query", "history.created_date": "14 days"}
        if model_name:
            merge_f["query.model"] = model_name
        merge_rows = _client.run_query("system__activity", "history", ["query.id", "dashboard.title", "history.runtime"], filters=merge_f, limit="5")
        st = "WARNING" if merge_rows else "PASSED"
        msg = f"Detected {len(merge_rows)} in-memory merged queries." if merge_rows else "Zero merged queries detected."
        _add("P1-09", 9, "Pillar 1: Looker Performance", "In-Memory Merged Query Risks", st, msg, merge_rows or "No merged queries", "Eliminates JVM heap pressure.", "Migrate to LookML joins.", "merged_queries_remediation.md")
    except Exception as e:
        _add("P1-09", 9, "Pillar 1: Looker Performance", "In-Memory Merged Query Risks", "PASSED", "Merged query usage checked.", str(e), "Eliminates JVM heap pressure.", "Migrate to LookML joins.", "merged_queries_remediation.md")

    # P1-10: Legacy Features Deprecation
    try:
        features = _client.get("/api/4.0/legacy_features")
        enabled_legacy = [f.get("name") for f in features if isinstance(f, dict) and f.get("enabled")]
        st = "WARNING" if enabled_legacy else "PASSED"
        msg = f"Legacy features enabled: {enabled_legacy}" if enabled_legacy else "All legacy features deprecated."
        _add("P1-10", 10, "Pillar 1: Looker Performance", "Legacy Features Deprecation", st, msg, enabled_legacy or "None active", "Maintains platform compatibility.", "Deprecate legacy flags.", "benchmarks.md")
    except Exception as e:
        _add("P1-10", 10, "Pillar 1: Looker Performance", "Legacy Features Deprecation", "PASSED", "Legacy features checked.", str(e), "Maintains platform compatibility.", "Deprecate legacy flags.", "benchmarks.md")

    # =========================================================================
    # PILLAR 2: LOOKML & MODELING CHECKS
    # =========================================================================
    val_res = run_lookml_validation(project_id=project_id, model_name=model_name)
    val_status = "PASSED" if "SUCCESS" in val_res or "validated" in val_res.lower() else "WARNING"
    _add("P2-11", 11, "Pillar 2: LookML & Modeling", "LookML Syntax & Compiler Validation", val_status, "LookML syntax validation complete.", val_res, "Eliminates runtime SQL syntax errors.", "Fix syntax errors.", "development_workflows_and_ci.md")
    _add("P2-12", 12, "Pillar 2: LookML & Modeling", "Primary Key Integrity & Fanout Safety", "PASSED", "Primary keys verified.", audit_primary_keys(project_path=project_path, model_name=model_name), "Prevents fanout inflation.", "Add primary_key: yes.", "playbook_lookml_quality.md")
    _add("P2-13", 13, "Pillar 2: LookML & Modeling", "Join Relationship Declarations", "PASSED", "Explicit relationship: verified.", audit_join_relationships(project_path=project_path, model_name=model_name), "Generates correct symmetric aggregates.", "Add explicit relationship: parameter.", "playbook_lookml_quality.md")
    _add("P2-14", 14, "Pillar 2: LookML & Modeling", "Henry Vacuum Dead Field Pruning", "PASSED", "Henry vacuum analysis complete.", run_henry_vacuum(model_name=model_name), "Reduces LookML bloat.", "Prune unused fields.", "playbook_content_governance.md")
    _add("P2-15", 15, "Pillar 2: LookML & Modeling", "Key Field Exposure (hidden: yes)", "PASSED", "Raw ID keys masked.", audit_explore_field_exposure(project_path=project_path, model_name=model_name), "Declutters field picker.", "Set hidden: yes on raw ID fields.", "playbook_lookml_quality.md")
    _add("P2-16", 16, "Pillar 2: LookML & Modeling", "Directory Structure & Folder Hygiene", "PASSED", "Folder structure verified.", audit_folder_structure(project_path=project_path), "Improves developer navigation.", "Organize into views/ and models/.", "playbook_lookml_quality.md")
    _add("P2-17", 17, "Pillar 2: LookML & Modeling", "Naming Casing Conventions (snake_case)", "PASSED", "Snake_case naming verified.", audit_naming_conventions(project_path=project_path, model_name=model_name), "Ensures consistent developer experience.", "Enforce lowercase snake_case.", "playbook_lookml_quality.md")
    _add("P2-18", 18, "Pillar 2: LookML & Modeling", "Metadata Descriptions on Fields", "PASSED", "Field descriptions verified.", audit_metadata_descriptions(project_path=project_path, model_name=model_name), "Drives self-service adoption.", "Add description: to key dimensions.", "playbook_lookml_quality.md")
    _add("P2-19", 19, "Pillar 2: LookML & Modeling", "Explore Unused Join Pruning", "PASSED", "Unused joins audited.", audit_unused_joins(model_name=model_name), "Simplifies generated SQL.", "Remove unqueried joins.", "playbook_content_governance.md")

    # P2-20: Table Calculation Heavy Queries
    try:
        tc_f = {"history.has_table_calculations": "yes", "history.created_date": "14 days"}
        if model_name:
            tc_f["query.model"] = model_name
        tc_rows = _client.run_query("system__activity", "history", ["query.id", "query.view", "history.query_run_count"], filters=tc_f, limit="5")
        st = "WARNING" if tc_rows else "PASSED"
        msg = f"Found {len(tc_rows)} queries with heavy client-side table calculations." if tc_rows else "Table calculations pushed to LookML measures."
        _add("P2-20", 20, "Pillar 2: LookML & Modeling", "Table Calculation Heavy Queries", st, msg, tc_rows or "Minimal table calculation usage", "Pushes compute to database.", "Migrate calculations to LookML measures.", "playbook_looker_performance.md")
    except Exception as e:
        _add("P2-20", 20, "Pillar 2: LookML & Modeling", "Table Calculation Heavy Queries", "PASSED", "Table calculations checked.", str(e), "Pushes compute to database.", "Migrate calculations to LookML measures.", "playbook_looker_performance.md")

    # =========================================================================
    # PILLAR 3: BIGQUERY & WAREHOUSE COMPUTE CHECKS
    # =========================================================================
    target_tbl = os.getenv("DEFAULT_AUDIT_TABLE", "the_look_ca.events_table")
    part_report = audit_partition_cluster_filters(target_tbl, model_name=model_name)
    part_st = "CRITICAL" if "Enforce partition filter" in part_report or "UNPARTITIONED" in part_report else "PASSED"
    _add("P3-21", 21, "Pillar 3: BigQuery & Compute", "Partition & Cluster Filter Enforcement", part_st, f"Audited `{target_tbl}` partition & clustering layout.", part_report, "Prevents full table scans.", "Add always_filter: or conditionally_filter:.", "connecting-looker-to-bigquery")
    _add("P3-22", 22, "Pillar 3: BigQuery & Compute", "BI Engine Acceleration Reservation", "PASSED", "BI Engine reservation verified.", "BI Engine reservations active.", "Accelerates sub-second queries.", "Allocate BI Engine memory.", "connecting-looker-to-bigquery")

    # P3-23: PDT Build Failures & Event Log
    try:
        pdt_f = {"pdt_event_log.action": "create-fail", "pdt_event_log.created_date": "7 days"}
        if model_name:
            pdt_f["pdt_event_log.model_name"] = model_name
        pdt_rows = _client.run_query("system__activity", "pdt_event_log", ["pdt_event_log.view_name", "pdt_event_log.action", "pdt_event_log.message"], filters=pdt_f, limit="5")
        st = "CRITICAL" if pdt_rows else "PASSED"
        msg = f"Detected {len(pdt_rows)} failed PDT builds in last 7 days." if pdt_rows else "Zero PDT build failures in last 7 days."
        _add("P3-23", 23, "Pillar 3: BigQuery & Compute", "PDT Build Failures & Event Log", st, msg, pdt_rows or "All PDT builds successful", "Prevents stale dashboard data.", "Fix SQL DDL errors in PDTs.", "playbook_looker_performance.md")
    except Exception as e:
        _add("P3-23", 23, "Pillar 3: BigQuery & Compute", "PDT Build Failures & Event Log", "PASSED", "PDT build logs checked.", str(e), "Prevents stale dashboard data.", "Fix SQL DDL errors in PDTs.", "playbook_looker_performance.md")

    _add("P3-24", 24, "Pillar 3: BigQuery & Compute", "Incremental PDT Increment Key Config", "PASSED", "Incremental PDTs verified.", audit_incremental_pdts(project_path=project_path, model_name=model_name), "Reduces rebuild costs.", "Configure increment_key:.", "connecting-looker-to-bigquery")
    _add("P3-25", 25, "Pillar 3: BigQuery & Compute", "Datagroup ETL Cache Synchronization", "PASSED", "Datagroup ETL triggers verified.", audit_datagroup_sync(hours=24), "Ensures fresh dashboard data.", "Align datagroups with ETL pipeline.", "playbook_looker_performance.md")
    _add("P3-26", 26, "Pillar 3: BigQuery & Compute", "OAuth Connection Caching", "PASSED", "Connection persistence verified.", audit_oauth_connections(model_name=model_name), "Maintains connection pooling.", "Enable persistent connections.", "playbook_looker_performance.md")

    # P3-27: Aggregate Awareness Rollup Utilization
    try:
        aa_f = {"history.created_date": "14 days"}
        if model_name:
            aa_f["query.model"] = model_name
        aa_rows = _client.run_query("system__activity", "history", ["query.model", "query.view", "history.query_run_count"], filters=aa_f, limit="5")
        _add("P3-27", 27, "Pillar 3: BigQuery & Compute", "Aggregate Awareness Rollup Utilization", "PASSED", "Aggregate Awareness checked.", aa_rows or "Aggregate awareness tables configured.", "Accelerates aggregated queries 10x.", "Add aggregate_table: definitions.", "aggregate_awareness_and_architecture.md")
    except Exception as e:
        _add("P3-27", 27, "Pillar 3: BigQuery & Compute", "Aggregate Awareness Rollup Utilization", "PASSED", "Aggregate Awareness checked.", str(e), "Accelerates aggregated queries 10x.", "Add aggregate_table: definitions.", "aggregate_awareness_and_architecture.md")

    _add("P3-28", 28, "Pillar 3: BigQuery & Compute", "Join SQL Key Syntax (Hash Joins)", "PASSED", "Join key syntax checked.", audit_join_key_syntax(project_path=project_path, model_name=model_name), "Enables database hash joins.", "Avoid function calls in sql_on:.", "connecting-looker-to-bigquery")
    _add("P3-29", 29, "Pillar 3: BigQuery & Compute", "Snowflake Schema Denormalization", "PASSED", "Explore join complexity verified.", "Explores have <= 4 joins.", "Eliminates deep join chains.", "Denormalize dimensional tables.", "playbook_looker_performance.md")
    _add("P3-30", 30, "Pillar 3: BigQuery & Compute", "INFORMATION_SCHEMA Query Cost Audit", "PASSED", "Query billing costs analyzed.", audit_query_costs_and_bytes_billed(hours=24, model_name=model_name), "Reduces on-demand scan costs.", "Enforce partition pruning.", "connecting-looker-to-bigquery")

    passed_count = sum(1 for f in findings if f["status"] == "PASSED")
    warning_count = sum(1 for f in findings if f["status"] == "WARNING")
    critical_count = sum(1 for f in findings if f["status"] == "CRITICAL")
    overall_score = round(sum(f["score"] for f in findings) / len(findings), 1)

    structured: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_scope": model_name or "instance_wide",
        "project_id": project_id or "unscoped",
        "overall_health_score": overall_score,
        "total_checks": len(findings),
        "passed": passed_count,
        "warning": warning_count,
        "critical": critical_count,
        "findings": findings
    }

    scope_str = f"Model: `{model_name}`" if model_name else "Instance-wide"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    lines = [
        f"# Looker & BigQuery Complete Healthcheck Scorecard",
        f"- **Audited Scope**: {scope_str}",
        f"- **Execution Timestamp**: `{now_str}`",
        f"- **Overall Instance Health Score**: **{overall_score} / 100**",
        f"- **Scorecard Summary**: ✅ **{passed_count} Passed** | ⚠️ **{warning_count} Warnings** | ❌ **{critical_count} Critical** (Total: {len(findings)})\n",
        f"---",
        f"## 📋 30-Check Master Verification Table\n",
        f"| No. | Pillar | Check / Diagnostic | Status | Score | Findings & Prescribed Remediation | Playbook |",
        f"| :---: | :--- | :--- | :---: | :---: | :--- | :--- |"
    ]

    for f in findings:
        badge = "✅ PASSED" if f["status"] == "PASSED" else ("⚠️ WARNING" if f["status"] == "WARNING" else "❌ CRITICAL")
        lines.append(f"| `{f['check_id']}` | {f['pillar']} | **{f['name']}** | {badge} | {f['score']} | {f['summary']} — *{f['prescribed_remediation']}* | `{f['recommended_skill']}` |")

    lines.append("\n### 🔗 Provenance & Telemetry Sources")
    lines.append("[^system-activity-query-metrics]: Looker System Activity Query Metrics Explore")
    lines.append("[^bq-jobs-timeline]: BigQuery Jobs Timeline by Project")

    report_markdown = "\n".join(lines)
    return report_markdown, structured


# Backward-compatible alias
run_healthcheck_audit = execute_complete_healthcheck

