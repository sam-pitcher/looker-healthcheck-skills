"""
Markdown Audit Reporter: Generates executive reports with PSO benchmark scoring.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any

PSO_THRESHOLDS = {
    "async_processing": {"target": 5.0, "warning": 10.0, "critical": 15.0, "unit": "s", "label": "Average Async Processing"},
    "execute_main_query": {"target": 4.87, "warning": 5.0, "critical": 15.0, "unit": "s", "label": "Main Query Execution"},
    "acquire_connection": {"target": 0.238, "warning": 0.24, "critical": 0.5, "unit": "s", "label": "Acquire Connection Time"},
    "model_init_computed": {"target": 2.42, "warning": 2.42, "critical": 5.0, "unit": "s", "label": "Model Init (Compute)"},
    "explore_init": {"target": 0.233, "warning": 0.233, "critical": 0.5, "unit": "s", "label": "Explore Init (Compute)"},
    "stream_to_cache": {"target": 0.223, "warning": 0.223, "critical": 0.5, "unit": "s", "label": "Stream to Cache Time"},
    "postprocessing": {"target": 0.223, "warning": 0.223, "critical": 0.5, "unit": "s", "label": "Post-Processing Time"},
}

def evaluate_metric(val: float, rule: Dict[str, Any]):
    if val is None or val == 0:
        return "🟢 Healthy", "Optimal"
    if val >= rule["critical"]:
        return "🔴 Critical", "Immediate Recipe Action Required"
    elif val >= rule["warning"]:
        return "🟡 Warning", "Approaching Threshold"
    return "🟢 Healthy", "Within PSO Guidelines"

class MarkdownReporter:
    @staticmethod
    def build(instance_url: str, kpis: Dict[str, Any], outliers: List[Dict[str, Any]], history: List[Dict[str, Any]]) -> str:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        async_avg = kpis.get("query_metrics.async_processing_average") or 0.001
        exec_avg = kpis.get("query_metrics.execute_main_query_average") or 0.0
        acq_avg = kpis.get("query_metrics.acquire_connection_average") or 0.0
        overhead_s = max(0.0, async_avg - (exec_avg + acq_avg))
        overhead_pct = (overhead_s / async_avg) * 100 if async_avg > 0 else 0.0

        report = []
        report.append(f"# Looker Instance Healthcheck & Performance Audit")
        report.append(f"**Instance:** `{instance_url}`  ")
        report.append(f"**Audited At:** `{now_str}`  ")
        report.append(f"**Auditing Framework:** Google PSO Consolidated Healthcheck Benchmarks  \n")
        report.append("---\n")

        # 1. Scorecard
        report.append("## 1. Executive Performance Scorecard\n")
        report.append("| Metric | Instance Current | PSO Benchmark | Status | Diagnostic Verdict |")
        report.append("| :--- | :---: | :---: | :---: | :--- |")

        action_recipes = set()
        metric_mappings = [
            ("async_processing", "query_metrics.async_processing_average"),
            ("execute_main_query", "query_metrics.execute_main_query_average"),
            ("acquire_connection", "query_metrics.acquire_connection_average"),
            ("model_init_computed", "query_metrics.model_init_computed_average"),
            ("explore_init", "query_metrics.explore_init_average"),
            ("stream_to_cache", "query_metrics.stream_to_cache_average"),
            ("postprocessing", "query_metrics.postprocessing_average"),
        ]

        for bench_key, query_key in metric_mappings:
            val = kpis.get(query_key, 0.0)
            rule = PSO_THRESHOLDS[bench_key]
            status, verdict = evaluate_metric(val, rule)
            report.append(f"| **{rule['label']}** | **`{val:.3f}{rule['unit']}`** | `< {rule['target']}{rule['unit']}` | {status} | {verdict} |")
            if "Critical" in status or "Warning" in status:
                if bench_key in ["model_init_computed", "explore_init"]:
                    action_recipes.add(1)
                elif bench_key in ["acquire_connection"]:
                    action_recipes.add(2)
                elif bench_key in ["execute_main_query"]:
                    action_recipes.add(3)
                elif bench_key in ["stream_to_cache", "postprocessing"]:
                    action_recipes.add(4)

        overhead_badge = "🟢 Healthy" if overhead_pct < 30 else ("🟡 Warning" if overhead_pct < 50 else "🔴 Critical")
        report.append(f"| **Indicative Looker Overhead** | **`{overhead_pct:.1f}%`** (`{overhead_s:.3f}s`) | `< 20.0%` | {overhead_badge} | Proportion of time spent inside Looker processing |")
        report.append("\n---\n")

        # 2. Phase Breakdown
        report.append("## 2. Query Latency Phase Distribution\n")
        report.append("```mermaid")
        report.append("pie title Latency Phase Distribution (Seconds)")
        report.append(f'    "Database Execution ({exec_avg:.2f}s)" : {max(0.01, exec_avg):.2f}')
        report.append(f'    "Looker Overhead ({overhead_s:.2f}s)" : {max(0.01, overhead_s):.2f}')
        report.append(f'    "Acquire Connection ({acq_avg:.2f}s)" : {max(0.01, acq_avg):.2f}')
        report.append("```\n")

        # 3. Top Outliers
        report.append("## 3. Slowest Outlier Queries\n")
        report.append("| Query ID | User | Explore / View | Dashboard | Async Runtime | DB Execution |")
        report.append("| :--- | :--- | :--- | :--- | :---: | :---: |")
        for q in outliers:
            qid = q.get("query.id", "N/A")
            uname = q.get("user.name", "System")
            qview = q.get("query.view", "N/A")
            dtitle = q.get("dashboard.title") or "Ad-hoc / Explore"
            q_async = q.get("query_metrics.async_processing") or 0.0
            q_db = q.get("query_metrics.execute_main_query") or 0.0
            report.append(f"| `{qid}` | {uname} | `{qview}` | {dtitle} | `{q_async:.2f}s` | `{q_db:.2f}s` |")

        report.append("\n---\n")

        # 4. Prescribed Recipes
        report.append("## 4. Prescribed Optimization Recipes\n")
        if not action_recipes:
            report.append("> [!NOTE]\n> All instance metrics are currently operating within healthy PSO benchmarks.\n")
        else:
            report.append("Execute the following master recipes from **`looker-healthcheck`** in your IDE:\n")
            if 1 in action_recipes:
                report.append("### 🛠️ Recipe 1: Project & Initialization Optimization")
                report.append("- Scope model inclusions to prevent compiling unreferenced views.")
            if 2 in action_recipes:
                report.append("### 🛠️ Recipe 2: Concurrency & Throttling Optimization")
                report.append("- Split >25 tile dashboards and eliminate merged queries.")
            if 3 in action_recipes:
                report.append("### 🛠️ Recipe 3: Database Execution & PDT Acceleration")
                report.append("- Materialize heavy transformations (>10s) with partition/cluster keys.")
            if 4 in action_recipes:
                report.append("### 🛠️ Recipe 4: Totals & Post-Processing Optimization")
                report.append("- Right-size row limits on single-value KPI cards and migrate table calculations to LookML measures.\n")

        return "\n".join(report)
