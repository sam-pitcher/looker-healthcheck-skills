#!/usr/bin/env python3
"""
Looker Healthcheck & PSO Performance Audit Generator
Queries Looker system__activity, evaluates metrics against Google PSO benchmarks,
and generates a comprehensive diagnostic report with prescriptive recipe actions.
"""

import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime

# Benchmarks derived from Google PSO Consolidated Healthcheck Dashboard
PSO_BENCHMARKS = {
    "async_processing": {"target": 5.0, "warning": 10.0, "critical": 15.0, "unit": "s", "label": "Average Async Processing"},
    "execute_main_query": {"target": 4.87, "warning": 5.0, "critical": 15.0, "unit": "s", "label": "Main Query Execution"},
    "acquire_connection": {"target": 0.238, "warning": 0.24, "critical": 0.5, "unit": "s", "label": "Acquire Connection Time"},
    "model_init_computed": {"target": 2.42, "warning": 2.42, "critical": 5.0, "unit": "s", "label": "Model Init (Compute)"},
    "model_init_cache": {"target": 1.0, "warning": 1.0, "critical": 2.0, "unit": "s", "label": "Model Init (Cache)"},
    "explore_init": {"target": 0.233, "warning": 0.233, "critical": 0.5, "unit": "s", "label": "Explore Init (Compute)"},
    "marshalled_cache_load": {"target": 0.351, "warning": 0.351, "critical": 0.75, "unit": "s", "label": "Explore Init (Cache)"},
    "prepare": {"target": 0.439, "warning": 0.44, "critical": 1.0, "unit": "s", "label": "Prepare Average"},
    "postprocessing": {"target": 0.223, "warning": 0.223, "critical": 0.5, "unit": "s", "label": "Post-Processing Time"},
    "stream_to_cache": {"target": 0.223, "warning": 0.223, "critical": 0.5, "unit": "s", "label": "Stream to Cache Time"},
    "project_init": {"target": 0.10, "warning": 0.10, "critical": 0.25, "unit": "s", "label": "Project Init Time"}
}

LOOKER_VERIFY_SSL = os.getenv("LOOKER_VERIFY_SSL", "true").lower() in ("true", "1", "yes", "t")

def get_ssl_context():
    if LOOKER_VERIFY_SSL:
        return ssl.create_default_context()
    return ssl._create_unverified_context()

def _extract_cli_profile():
    config_path = os.path.expanduser(os.getenv("LOOKER_CLI_CONFIG", "~/.config/looker-cli/config.yaml"))
    if not os.path.exists(config_path):
        return {}
    try:
        import re
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        host_m = re.search(r"host:\s*([^\s\n]+)", content)
        port_m = re.search(r"port:\s*([^\s\n]+)", content)
        token_m = re.search(r"access_token:\s*([^\s\n]+)", content)
        host = host_m.group(1).strip("\"'") if host_m else ""
        port = port_m.group(1).strip("\"'") if port_m else "443"
        raw_token = token_m.group(1).strip("\"'") if token_m else ""
        token = raw_token if raw_token not in ("null", "None", "''", '""') else ""
        base_url = f"https://{host}" if port in ("443", "19999") or LOOKER_VERIFY_SSL else f"http://{host}"
        if port not in ("443", "80"):
            base_url = f"https://{host}:{port}" if LOOKER_VERIFY_SSL else f"http://{host}:{port}"
        return {"base_url": base_url if host else "", "access_token": token}
    except Exception:
        return {}

def load_config():
    """Load Looker settings from OAuth session, environment variables, or CLI config."""
    cli_data = _extract_cli_profile()
    base_url = os.getenv("LOOKERSDK_BASE_URL", "").rstrip("/") or cli_data.get("base_url", "")
    oauth_token = os.getenv("LOOKERSDK_OAUTH_TOKEN") or os.getenv("LOOKER_OAUTH_TOKEN") or os.getenv("LOOKERSDK_ACCESS_TOKEN") or cli_data.get("access_token", "")
    return {
        "base_url": base_url,
        "client_id": os.getenv("LOOKERSDK_CLIENT_ID", ""),
        "client_secret": os.getenv("LOOKERSDK_CLIENT_SECRET", ""),
        "oauth_token": oauth_token,
        "project_id": os.getenv("LOOKER_PROJECT_ID", "")
    }

def authenticate(config):
    """Authenticate and obtain API access token via OAuth inheritance or API3 credentials."""
    if config.get("oauth_token"):
        return config["oauth_token"]
    
    if not config.get("base_url") or not config.get("client_id") or not config.get("client_secret"):
        raise ValueError(
            "Looker Authentication Error: No active OAuth session or API3 credentials found.\n"
            "Run 'looker-cli session login --oauth' to authenticate under your user identity, or set LOOKERSDK_CLIENT_ID / LOOKERSDK_CLIENT_SECRET."
        )
    
    ssl_context = get_ssl_context()
    login_url = f"{config['base_url']}/api/4.0/login"
    payload = urllib.parse.urlencode({
        "client_id": config["client_id"],
        "client_secret": config["client_secret"]
    }).encode("utf-8")
    
    req = urllib.request.Request(login_url, data=payload, method="POST")
    with urllib.request.urlopen(req, context=ssl_context) as resp:
        data = json.loads(resp.read().decode())
        return data["access_token"]

def run_inline_query(config, token, model, view, fields, filters=None, sorts=None, limit="50"):
    """Execute an inline query against Looker API."""
    ssl_context = get_ssl_context()
    query_url = f"{config['base_url']}/api/4.0/queries/run/json"
    body = {
        "model": model,
        "view": view,
        "fields": fields,
        "limit": str(limit)
    }
    if filters:
        body["filters"] = filters
    if sorts:
        body["sorts"] = sorts

    req = urllib.request.Request(
        query_url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, context=ssl_context) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Query failed: {e.code} - {e.read().decode()}", file=sys.stderr)
        return []

def evaluate_status(val, benchmark_info):
    """Evaluate metric status against PSO benchmarks."""
    if val is None or val == 0:
        return "🟢 Healthy", "Optimal"
    target = benchmark_info["target"]
    warning = benchmark_info["warning"]
    critical = benchmark_info["critical"]
    
    if val >= critical:
        return "🔴 Critical", "Immediate Recipe Action Required"
    elif val >= warning:
        return "🟡 Warning", "Approaching Threshold"
    else:
        return "🟢 Healthy", "Within PSO Guidelines"

from typing import Optional

def generate_healthcheck_report(config, token, model_name: Optional[str] = None):
    """Run diagnostics and generate comprehensive Markdown report."""
    print("Collecting Looker System Activity KPIs...")
    
    kpi_filters = {"query.model": model_name} if model_name else None
    
    # 1. High Level Query Metrics
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
    kpi_results = run_inline_query(config, token, "system__activity", "query_metrics", kpi_fields, filters=kpi_filters, limit="1")
    kpis = kpi_results[0] if kpi_results else {}

    # 2. History Status Breakdown
    history_fields = ["history.source", "history.status", "history.query_run_count"]
    history_results = run_inline_query(config, token, "system__activity", "history", history_fields, filters=kpi_filters, limit="25")

    # 3. Outlier Queries
    outlier_fields = [
        "query.id",
        "user.name",
        "dashboard.title",
        "query.view",
        "query_metrics.async_processing",
        "query_metrics.execute_main_query",
        "history.created_time"
    ]
    outlier_results = run_inline_query(
        config, token, "system__activity", "query_metrics",
        outlier_fields,
        filters=kpi_filters,
        sorts=["query_metrics.async_processing desc"],
        limit="5"
    )

    # 4. Compute Indicative Looker Overhead
    async_avg = kpis.get("query_metrics.async_processing_average") or 0.001
    exec_avg = kpis.get("query_metrics.execute_main_query_average") or 0.0
    acq_avg = kpis.get("query_metrics.acquire_connection_average") or 0.0
    overhead_seconds = max(0, async_avg - (exec_avg + acq_avg))
    overhead_pct = (overhead_seconds / async_avg) * 100 if async_avg > 0 else 0.0

    # Build Markdown Report
    from datetime import timezone
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report = []
    report.append(f"# Looker Instance Healthcheck & Performance Audit")
    report.append(f"**Instance:** `{config['base_url']}`  ")
    report.append(f"**Audited At:** `{now_str}`  ")
    report.append(f"**Diagnostic Standard:** Google Cloud PSO Consolidated Healthcheck Benchmarks  \n")
    report.append("---\n")

    # Executive Scorecard
    report.append("## 1. Executive Performance Scorecard\n")
    report.append(f"| Metric | Current Instance Average | PSO Benchmark | Status | Verdict |")
    report.append(f"| :--- | :---: | :---: | :---: | :--- |")
    
    # Evaluate each metric
    mappings = [
        ("async_processing", "query_metrics.async_processing_average"),
        ("execute_main_query", "query_metrics.execute_main_query_average"),
        ("acquire_connection", "query_metrics.acquire_connection_average"),
        ("model_init_computed", "query_metrics.model_init_computed_average"),
        ("explore_init", "query_metrics.explore_init_average"),
        ("stream_to_cache", "query_metrics.stream_to_cache_average"),
        ("postprocessing", "query_metrics.postprocessing_average"),
    ]

    action_recipes = set()

    for bench_key, metric_key in mappings:
        val = kpis.get(metric_key, 0.0)
        b_info = PSO_BENCHMARKS[bench_key]
        status, verdict = evaluate_status(val, b_info)
        report.append(f"| **{b_info['label']}** | **`{val:.3f}{b_info['unit']}`** | `< {b_info['target']}{b_info['unit']}` | {status} | {verdict} |")
        if "Critical" in status or "Warning" in status:
            if bench_key in ["model_init_computed", "explore_init", "project_init"]:
                action_recipes.add(1)
            elif bench_key in ["acquire_connection"]:
                action_recipes.add(2)
            elif bench_key in ["execute_main_query"]:
                action_recipes.add(3)
            elif bench_key in ["stream_to_cache", "postprocessing"]:
                action_recipes.add(4)

    # Overhead Score
    overhead_status = "🟢 Healthy" if overhead_pct < 30 else ("🟡 Warning" if overhead_pct < 50 else "🔴 Critical")
    report.append(f"| **Indicative Looker Overhead** | **`{overhead_pct:.1f}%`** (`{overhead_seconds:.3f}s`) | `< 20.0%` | {overhead_status} | Proportion of time spent inside Looker processing |")
    report.append("\n---\n")

    # Phase Breakdown
    report.append("## 2. Query Lifecycle Phase Breakdown\n")
    report.append("```mermaid")
    report.append("pie title Latency Phase Distribution (Seconds)")
    report.append(f'    "Database Execution ({exec_avg:.2f}s)" : {max(0.01, exec_avg):.2f}')
    report.append(f'    "Looker Overhead ({overhead_seconds:.2f}s)" : {max(0.01, overhead_seconds):.2f}')
    report.append(f'    "Acquire Connection ({acq_avg:.2f}s)" : {max(0.01, acq_avg):.2f}')
    report.append("```\n")

    # Outlier Queries
    report.append("## 3. Top Slowest Outlier Queries\n")
    report.append("| Query ID | User | Explore / View | Dashboard | Async Runtime | DB Execution |")
    report.append("| :--- | :--- | :--- | :--- | :---: | :---: |")
    for q in outlier_results:
        qid = q.get("query.id", "N/A")
        uname = q.get("user.name", "System")
        qview = q.get("query.view", "N/A")
        dtitle = q.get("dashboard.title") or "Ad-hoc / Explore"
        q_async = q.get("query_metrics.async_processing") or 0.0
        q_db = q.get("query_metrics.execute_main_query") or 0.0
        report.append(f"| `{qid}` | {uname} | `{qview}` | {dtitle} | `{q_async:.2f}s` | `{q_db:.2f}s` |")

    report.append("\n---\n")

    # History Breakdown
    report.append("## 4. Query Traffic & Status Breakdown\n")
    report.append("| Query Source | Status | Executed Queries |")
    report.append("| :--- | :---: | :---: |")
    for h in history_results:
        src = h.get("history.source", "unknown")
        st = h.get("history.status", "unknown")
        count = h.get("history.query_run_count", 0)
        st_badge = "🟢 Complete" if st == "complete" else ("🔴 Error" if st == "error" else f"⚪ {st}")
        report.append(f"| `{src}` | {st_badge} | **{count:,}** |")

    report.append("\n---\n")

    # Prescribed Action Recipes
    report.append("## 5. Prescribed Optimization Actions\n")
    if not action_recipes:
        report.append("> [!NOTE]\n> **All instance KPIs are currently within PSO healthy benchmarks.** No immediate critical refactoring is needed. Continue enforcing performance-by-design standards.\n")
    else:
        report.append("Based on the diagnosed bottlenecks, execute the following master recipes from **`looker-healthcheck`**:\n")
        if 1 in action_recipes:
            report.append("### 🛠️ Recipe 1: Project & Initialization Optimization")
            report.append("- Scoped includes in model files (`include: \"/views/orders/*.view\"` instead of wildcards).")
            report.append("- Establish scheduled deployment windows to avoid compiler cache busting during peak hours.\n")
        if 2 in action_recipes:
            report.append("### 🛠️ Recipe 2: Concurrency & Throttling Optimization")
            report.append("- Split >25 tile dashboards into tabbed layouts or link via drill-down links.")
            report.append("- Eliminate merged queries in favor of native LookML joins.\n")
        if 3 in action_recipes:
            report.append("### 🛠️ Recipe 3: Database Execution & PDT Acceleration")
            report.append("- Materialize heavy transformations (>10s) into partitioned/clustered PDTs.")
            report.append("- Verify join cardinality to eliminate `SUM_DISTINCT` / symmetric aggregations.\n")
        if 4 in action_recipes:
            report.append("### 🛠️ Recipe 4: Totals & Post-Processing Optimization")
            report.append("- Right-size row limits (e.g. single-value tiles set to limit 1-500).")
            report.append("- Migrate client-side table calculations into native LookML model measures.\n")

    return "\n".join(report)

def main():
    config = load_config()
    if not config.get("oauth_token") and (not config.get("client_id") or not config.get("client_secret")):
        print("Missing Looker OAuth session or API credentials. Run `looker-cli session login --oauth --client-id com.looker.cli`.", file=sys.stderr)
        sys.exit(1)
    
    token = authenticate(config)
    report_md = generate_healthcheck_report(config, token)
    print(report_md)

if __name__ == "__main__":
    main()
