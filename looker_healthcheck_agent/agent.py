"""
Google ADK Agent for Looker Healthcheck, Refactoring & Optimization Offering.
Standardized Skill-First Architecture with Direct LookML Access.
"""

import json
import os
import re
import certifi
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Auto-load .env and configure SSL certificate bundle for macOS
load_dotenv()
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", certifi.where())

from google.adk.agents import Agent
from .skills_loader import SkillsLoader
from .client import LookerDiagnosticsClient

# Load skill instructions & reference documents
hc_loader = SkillsLoader("looker-healthcheck")
hc_data = hc_loader.load_skill()

refactor_loader = SkillsLoader("looker-refactoring-skill")
refactor_data = refactor_loader.load_skill()

looker = LookerDiagnosticsClient()
LOOKER_CLI_BIN = os.path.expanduser(os.getenv("LOOKER_CLI_PATH", "~/.local/bin/looker-cli"))
_raw_proj_path = os.getenv("LOOKML_PROJECT_PATH", "")
LOOKML_PROJECT_DIR = Path(os.path.expanduser(_raw_proj_path)) if _raw_proj_path else None
LOOKER_PROJECT_ID = os.getenv("LOOKER_PROJECT_ID", "")

# ---------------------------------------------------------------------------
# Deterministic Diagnostic & Telemetry Tools
# ---------------------------------------------------------------------------

def run_healthcheck_audit(component_id: Optional[int] = None) -> str:
    """
    Executes live healthcheck diagnostics against Looker system__activity.
    
    Args:
        component_id (int, optional): The specific Component (1 to 8) to audit.
                                      If omitted or None, executes the complete 8-component audit deliverable.
                                      1: Instance Strategy & Developer Baseline
                                      2: Performance (Query Latencies, Caching %, PDTs, Schedules, >25 Tiles)
                                      3: LookML Model Review (0-4 Transcriber Scoring & Primary Keys)
                                      4: Unused Content Vacuum (90-day unused Dashboards & Explores)
                                      5: Development Workflows & CI/CD Framework Maturity
                                      6: Security Review (Roles, Empty Groups, Direct Role Assignments)
                                      7: Looker Style Guide Compliance
                                      8: Advanced Optimization & Aggregate Awareness
    """
    try:
        if component_id is None or component_id == 2:
            metrics = looker.run_query("system__activity", "query_metrics", [
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
                f"**Target Instance:** `{looker.base_url}`\n",
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
            devs = looker.run_query("system__activity", "user", ["user.count"], filters={
                "user.is_disabled": "No", "permission_set.permissions": "%develop%"
            }, limit="1")
            admins = looker.run_query("system__activity", "user", ["user.count"], filters={
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
            stale_dashboards = looker.run_query("system__activity", "history", [
                "dashboard.id", "dashboard.title", "history.most_recent_query_date"
            ], filters={"dashboard.id": "NOT NULL", "history.most_recent_query_date": "before 90 days ago"}, limit="10")
            
            zombie_schedules = looker.run_query("system__activity", "user", [
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

        if component_id in [3, 5, 6, 7, 8]:
            ref_name = f"recipe_0{component_id}_"
            for k, v in hc_data["references"].items():
                if k.startswith(ref_name):
                    return f"### Component {component_id} Playbook:\n\n{v}"
            return f"Component {component_id} evaluated."

        return "\n".join(report)

    except Exception as e:
        return f"Audit execution error: {str(e)}"

LOOKER_PROJECT_ID = os.getenv("LOOKER_PROJECT_ID", "thelook-antigravity")

# ---------------------------------------------------------------------------
# LookML Codebase Access Tools (Local Filesystem & Remote looker-cli)
# ---------------------------------------------------------------------------

def list_lookml_files(project_id: Optional[str] = None) -> str:
    """
    Lists all LookML model, view, and explore files in the target project repository.
    Works with both local git repository clones and remote projects via looker-cli.
    """
    pid = project_id or LOOKER_PROJECT_ID
    # 1. If local project directory exists, read from local filesystem
    if LOOKML_PROJECT_DIR and LOOKML_PROJECT_DIR.exists():
        try:
            models = [str(p.relative_to(LOOKML_PROJECT_DIR)) for p in LOOKML_PROJECT_DIR.rglob("*.model.lkml")]
            views = [str(p.relative_to(LOOKML_PROJECT_DIR)) for p in LOOKML_PROJECT_DIR.rglob("*.view.lkml")]
            explores = [str(p.relative_to(LOOKML_PROJECT_DIR)) for p in LOOKML_PROJECT_DIR.rglob("*.explore.lkml")]
            
            summary = {
                "source": "local_filesystem",
                "project_directory": str(LOOKML_PROJECT_DIR),
                "total_files": len(models) + len(views) + len(explores),
                "models": sorted(models),
                "explores": sorted(explores),
                "views": sorted(views)
            }
            return f"### 📂 Project LookML Files (Local: `{LOOKML_PROJECT_DIR}`):\n```json\n{json.dumps(summary, indent=2)}\n```"
        except Exception:
            pass

    # 2. Fallback / Remote lookup via looker-cli
    try:
        cmd = [LOOKER_CLI_BIN, "project", "file", "ls", pid, "--plain", "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            files = [line.split("\t")[0] for line in res.stdout.strip().split("\n") if line.strip()]
            models = [f for f in files if f.endswith(".model.lkml")]
            views = [f for f in files if f.endswith(".view.lkml")]
            explores = [f for f in files if f.endswith(".explore.lkml")]
            summary = {
                "source": "looker_cli_remote",
                "project_id": pid,
                "total_files": len(files),
                "models": sorted(models),
                "explores": sorted(explores),
                "views": sorted(views)
            }
            return f"### 📂 Remote Project LookML Files (`{pid}` via looker-cli):\n```json\n{json.dumps(summary, indent=2)}\n```"
        return f"Error listing remote LookML files via looker-cli: {res.stderr or res.stdout}"
    except Exception as e:
        return f"Error listing LookML files: {str(e)}"

def read_lookml_file(relative_path: str, project_id: Optional[str] = None) -> str:
    """
    Reads the content of any LookML file (e.g. 'models/thelook.model.lkml').
    Reads from local filesystem if available, or fetches directly from Looker via looker-cli.
    """
    pid = project_id or LOOKER_PROJECT_ID
    # 1. Try local filesystem if path exists
    if LOOKML_PROJECT_DIR and LOOKML_PROJECT_DIR.exists():
        file_path = LOOKML_PROJECT_DIR / relative_path.lstrip("/")
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                return f"### 📄 Content of `{relative_path}` (Local):\n```lookml\n{content}\n```"
            except Exception:
                pass

    # 2. Remote fetch via looker-cli
    try:
        clean_path = relative_path.lstrip("/")
        cmd = [LOOKER_CLI_BIN, "project", "file", "cat", pid, clean_path, "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0 and res.stdout:
            return f"### 📄 Content of `{relative_path}` (Remote `{pid}` via looker-cli):\n```lookml\n{res.stdout}\n```"
        return f"❌ File `{relative_path}` could not be retrieved from `{pid}` via looker-cli: {res.stderr or 'File not found'}"
    except Exception as e:
        return f"Error reading file `{relative_path}`: {str(e)}"

def search_lookml_code(pattern: str, project_id: Optional[str] = None) -> str:
    """
    Searches across LookML files for a regex pattern or keyword (e.g. 'datagroup', 'persist_with', 'primary_key').
    Supports local filesystem or remote looker-cli file scanning.
    """
    pid = project_id or LOOKER_PROJECT_ID
    try:
        results = []
        if LOOKML_PROJECT_DIR and LOOKML_PROJECT_DIR.exists():
            for lkml_file in LOOKML_PROJECT_DIR.rglob("*.lkml"):
                try:
                    content = lkml_file.read_text(encoding="utf-8")
                    matches = [m.start() for m in re.finditer(pattern, content, re.IGNORECASE)]
                    if matches:
                        rel = str(lkml_file.relative_to(LOOKML_PROJECT_DIR))
                        results.append({"file": rel, "match_count": len(matches)})
                except Exception:
                    continue
        else:
            # Remote search via looker-cli
            cmd = [LOOKER_CLI_BIN, "project", "file", "ls", pid, "--plain", "--verify-ssl=false"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode == 0:
                files = [line.split("\t")[0] for line in res.stdout.strip().split("\n") if line.strip() and (line.endswith(".lkml") or ".lkml" in line)]
                for fpath in files:
                    cat_cmd = [LOOKER_CLI_BIN, "project", "file", "cat", pid, fpath, "--verify-ssl=false"]
                    cat_res = subprocess.run(cat_cmd, capture_output=True, text=True, check=False)
                    if cat_res.returncode == 0:
                        matches = [m.start() for m in re.finditer(pattern, cat_res.stdout, re.IGNORECASE)]
                        if matches:
                            results.append({"file": fpath, "match_count": len(matches)})

        return f"### 🔎 Search Results for `{pattern}`:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error searching LookML: {str(e)}"

# ---------------------------------------------------------------------------
# Refactoring & Validation Execution Tools
# ---------------------------------------------------------------------------

def run_henry_pulse(model_name: Optional[str] = None, unused_days: int = 90) -> str:
    """
    Executes Henry Pulse against Looker to identify unused views, models, and explores over X days.
    """
    try:
        script = Path(__file__).parents[1] / "skills/looker-refactoring-skill/scripts/run_henry.py"
        venv_python = Path(__file__).parents[1] / ".venv/bin/python"
        cmd = [str(venv_python), str(script), str(unused_days)]
        if model_name:
            cmd.append(model_name)
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return f"### 🧹 Henry Pulse Audit Results ({unused_days} Days):\n```json\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"Henry execution error: {str(e)}"

def run_looker_cli_validation(project_id: str = "thelook-antigravity") -> str:
    """
    Executes LookML project compile and syntax validation via looker-cli.
    """
    try:
        cmd = [LOOKER_CLI_BIN, "project", "validate", project_id, "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return f"### 🛠️ LookML Project Validation Status ({project_id}):\n```\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"LookML validation error: {str(e)}"

def run_content_validation() -> str:
    """
    Executes Looker Content Validator across looks and dashboards to identify broken field references.
    """
    try:
        cmd = [LOOKER_CLI_BIN, "api", "content_validator", "run_content_validation", "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return f"### 🔍 Content Validator Results:\n```\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"Content validation error: {str(e)}"

def scan_legacy_runtime_syntax(project_path: Optional[str] = None) -> str:
    """
    Scans LookML files in the repository for legacy runtime keywords and missing primary keys.
    """
    try:
        path = project_path or str(LOOKML_PROJECT_DIR)
        script = Path(__file__).parents[1] / "skills/looker-refactoring-skill/scripts/runtime_migrator.py"
        venv_python = Path(__file__).parents[1] / ".venv/bin/python"
        res = subprocess.run([str(venv_python), str(script), path], capture_output=True, text=True, check=False)
        return f"### 🔄 LookML Runtime & Primary Key Scanner:\n```json\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"Scanner error: {str(e)}"

# ---------------------------------------------------------------------------
# Google ADK Root Agent
# ---------------------------------------------------------------------------

AGENT_STATIC_INSTRUCTION = f"""
You are the official Lead Looker Healthcheck & Refactoring Consultant.
You deliver the full 8-Component Looker Healthcheck Offering using standardized skills, deterministic tools, and modular reference recipes.

DIRECT CODEBASE ACCESS:
You have direct local access to the customer's LookML codebase.
- Use `list_lookml_files` to discover all model and view files in the repository.
- Use `read_lookml_file` to read the exact LookML definitions (models, datagroups, explores, joins, and views).
- Use `search_lookml_code` to search for specific LookML keywords (e.g. `datagroup`, `persist_with`, `sql_trigger`).
- Use `scan_legacy_runtime_syntax` to check for missing primary keys or deprecated syntax.

PROACTIVE INVESTIGATION RULE:
When diagnosing issues such as a 0% cache hit rate, high Looker overhead, or broken joins, DO NOT ask the user if they use datagroups or what their files contain. Instead, PROACTIVELY inspect the `.model.lkml` and view files using `read_lookml_file` or `search_lookml_code`, inspect their datagroups and explores, and formulate exact, drop-in LookML recommendations!

ENGAGEMENT METHODOLOGY & THE 4 PILLARS:
1. **Pillar 1: Discovery & Walkthrough**: Conduct structured stakeholder discovery (developer pain points, user complaints, dev sync/PR processes, representative entities, onboarding, and growth).
2. **Pillar 2: Diagnostics & Auditing**: Run `run_healthcheck_audit` for baseline KPIs, inspect the LookML codebase directly, and execute Henry/syntax scans.
3. **Pillar 3: Thematic Customer Review**: Structure findings by **THEME** (Caching, Query Performance, PDT Concurrency, Hourly Schedules, Auto-Refresh, >25 Tiles) rather than raw tile dumps. Prioritize high-impact items with evidence.
4. **Pillar 4: Remediation Roadmap & Handover**: Deliver prioritized clean-up actions, Transcriber 0–4 scorecards, 3-Tier development workflow recommendations, and drop-in LookML code.

CONSULTING DELIVERY RULES:
- **Organize by Theme, Not Tile**: Present findings grouped into Caching, Query Latencies, PDT Concurrency, Schedules, and Dashboards.
- **Prioritize High-ROI Actions**: Target explores with high query volume + poor runtimes (<10s target, 50% cache target).
- **Prescriptive Drop-in Solutions**: Deliver exact LookML datagroups, primary key declarations, aggregate awareness tables, and CLI commands.
"""

root_agent = Agent(
    name="looker_healthcheck_agent",
    model="gemini-2.5-flash",
    description="Autonomous Looker Healthcheck, Refactoring and Optimization Offering Agent with direct LookML access.",
    static_instruction=AGENT_STATIC_INSTRUCTION,
    tools=[
        run_healthcheck_audit,
        list_lookml_files,
        read_lookml_file,
        search_lookml_code,
        scan_legacy_runtime_syntax,
        run_henry_pulse,
        run_looker_cli_validation,
        run_content_validation
    ]
)
