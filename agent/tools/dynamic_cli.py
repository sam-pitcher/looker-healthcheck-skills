"""
Dynamic Looker CLI Meta-Discovery, Payload Inspection, and Guarded Execution Tools.
Replaces monolithic static wrappers with high-leverage dynamic CLI exploration
while enforcing safety guardrails to block destructive commands.
"""

import os
import re
import json
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

LOOKER_CLI_BIN = os.path.expanduser(os.getenv("LOOKER_CLI_PATH", "~/.local/bin/looker-cli"))
LOOKER_VERIFY_SSL = os.getenv("LOOKER_VERIFY_SSL", "true").lower() in ("true", "1", "yes", "t")

# Guardrail: Destructive command patterns blocked unless explicitly confirmed
DESTRUCTIVE_PATTERNS = [
    r"\brm\b",
    r"\bdelete\b",
    r"\bdelete_\w+",
    r"\bdrop\b",
    r"\btruncate\b",
    r"\bwipeout\b",
    r"\bdestroy\b",
    r"\bpurge\b"
]

def _get_cli_auth_flags() -> List[str]:
    """Retrieves active host, token, and SSL configuration to ensure CLI commands authenticate reliably."""
    from agent.tools.looker_api import _client
    flags = []
    try:
        if not _client.token:
            _client.authenticate()
    except Exception:
        pass

    if _client.base_url:
        host = _client.base_url.replace("https://", "").replace("http://", "").split(":")[0]
        flags.append(f"--host={host}")
        flags.append("--port=443")
    
    if _client.token:
        flags.append(f"--token={_client.token}")
    
    if not _client.verify_ssl:
        flags.append("--verify-ssl=false")
    else:
        flags.append("--verify-ssl=true")

    return flags


def _run_cli(args: List[str], input_str: Optional[str] = None, timeout: int = 60) -> tuple[int, str, str]:
    """Internal helper to execute looker-cli safely with injected session credentials."""
    cmd = [LOOKER_CLI_BIN] + args
    
    # Inject auth flags for commands that interact with Looker API (unless already specified)
    cmd_str = " ".join(args)
    if not any(a.startswith("--token") for a in args) and not any(a.startswith("--profile") for a in args):
        auth_flags = _get_cli_auth_flags()
        for f in auth_flags:
            flag_name = f.split("=")[0]
            if not any(a.startswith(flag_name) for a in args):
                cmd.append(f)

    try:
        res = subprocess.run(
            cmd,
            input=input_str,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout
        )
        return res.returncode, res.stdout, res.stderr
    except FileNotFoundError:
        return 127, "", f"Looker CLI binary not found at '{LOOKER_CLI_BIN}'. Run `installing-looker-cli` skill."
    except subprocess.TimeoutExpired:
        return 124, "", f"Command execution timed out after {timeout}s."
    except Exception as e:
        return 1, "", str(e)


def looker_cli_discover(category_or_query: Optional[str] = None) -> str:
    """
    Dynamic Looker CLI Discovery Tool.
    Allows the agent to explore available Looker CLI commands, API endpoints, and subcommands dynamically.
    
    Args:
        category_or_query: Optional search keyword (e.g. 'dashboard', 'query', 'user', 'health') 
                           or category to display subtree for (e.g. 'api', 'dashboard', 'project').
                           If None, returns high-level CLI command tree.
    """
    if not category_or_query:
        code, stdout, stderr = _run_cli(["meta", "tree"], timeout=15)
        if code == 0:
            lines = stdout.splitlines()[:60]
            return f"### 🧭 Looker CLI Command Tree (Root):\n```text\n{chr(10).join(lines)}\n```\n*(Use `looker_cli_discover('query')` or `looker_cli_discover('api <category>')` to drill down)*"
        return f"CLI discovery notice: {stderr or stdout}"

    query = category_or_query.strip()
    
    if " " in query or query in ("api", "dashboard", "folder", "project", "health", "attribute", "connection", "user", "role", "session"):
        args = ["meta", "tree"] + query.split()
        code, stdout, stderr = _run_cli(args, timeout=20)
        if code == 0 and stdout.strip():
            return f"### 🌳 CLI Tree for `{query}`:\n```text\n{stdout.strip()}\n```"
    
    code, stdout, stderr = _run_cli(["meta", "search", query], timeout=20)
    if code == 0:
        lines = stdout.strip().splitlines()
        summary = "\n".join(lines[:40])
        total_msg = f"\n*({len(lines)} matching commands found)*" if len(lines) > 40 else ""
        return f"### 🔍 Looker CLI Discovery Results for `{query}`:\n```text\n{summary}\n```{total_msg}"
    
    return f"Looker CLI discovery error: {stderr or stdout}"


def looker_cli_inspect_payload(command_path: str) -> str:
    """
    Dynamic Command & Payload Inspector.
    Inspects parameter schemas, required flags, and request body JSON templates for any Looker CLI command.
    
    Args:
        command_path: Space-separated command (e.g. 'api query run_inline_query', 'project validate', 'dashboard cat').
    """
    args = shlex.split(command_path.strip())
    
    template_res = ""
    code, stdout, stderr = _run_cli(args + ["--template"], timeout=15)
    if code == 0 and stdout.strip() and "{" in stdout:
        template_res = stdout.strip()

    code, help_stdout, help_stderr = _run_cli(args + ["--help"], timeout=15)
    help_text = help_stdout.strip() if code == 0 else help_stderr.strip()

    output = f"### 📋 Command Specification: `looker-cli {command_path}`\n\n"
    if template_res:
        output += f"#### 📝 Request Body JSON Template (`--template`):\n```json\n{template_res}\n```\n\n"
    
    if help_text:
        output += f"#### 📖 Usage & Flags (`--help`):\n```text\n{help_text}\n```"

    return output


def looker_cli_execute(
    command_args: str,
    body_json: Optional[str] = None,
    allow_mutation: bool = False
) -> str:
    """
    Guarded Looker CLI Execution Tool.
    Executes any Looker CLI command under the caller's inherited OAuth session with safety guardrails.
    
    Args:
        command_args: Command arguments string (e.g. 'user me', 'api project all_projects', 'query runquery 1234').
        body_json: Optional JSON string payload to pass to the command or stdin.
        allow_mutation: Must be explicitly set to True when running mutative or destructive operations (e.g. delete/update).
    """
    clean_cmd = command_args.strip()
    
    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, clean_cmd, re.IGNORECASE):
            if not allow_mutation:
                return (
                    f"⛔ SAFETY GUARDRAIL TRIGGERED: The command `looker-cli {clean_cmd}` matches destructive operation pattern '{pattern}'.\n"
                    f"If you intended to execute this mutation, please set `allow_mutation=True` after confirming with the user."
                )

    args = shlex.split(clean_cmd)
    input_payload = body_json.strip() if body_json else None

    code, stdout, stderr = _run_cli(args, input_str=input_payload, timeout=60)
    
    if code == 0:
        res_str = stdout.strip() or "(Command succeeded with empty response)"
        return f"### ✅ Output of `looker-cli {clean_cmd}`:\n```\n{res_str}\n```"
    
    if code == 1 and ("401" in (stderr + stdout) or "token expired" in (stderr + stdout).lower()):
        return "⚠️ Looker session expired or unauthorized. Please run `looker-cli session login --oauth --client-id com.looker.cli` in your terminal to refresh."
    
    return f"### ⚠️ Command Failed (`looker-cli {clean_cmd}` - Exit Code {code}):\n```\n{stderr.strip() or stdout.strip()}\n```"


def run_consolidated_healthcheck_benchmark(
    model_name: Optional[str] = None,
    project_id: Optional[str] = None
) -> str:
    """
    One-Click Consolidated Healthcheck Benchmark.
    Executes the complete 30-Check Healthcheck Program across all 3 pillars:
      - Pillar 1: Instance & Content Health (Tasks 01-10)
      - Pillar 2: LookML & Modeling Quality (Tasks 11-20)
      - Pillar 3: BigQuery & Warehouse Compute (Tasks 21-30)
    Gathers live PSO System Activity benchmarks, calculates scores, and persists report.
    
    Args:
        model_name: Optional LookML model name to scope all audits to.
        project_id: Optional LookML project ID.
    """
    import sys
    from pathlib import Path
    from agent.tools.looker_api import execute_complete_healthcheck
    from agent.tools.storage import save_audit_report
    
    # 1. Execute live System Activity PSO benchmarks runner from skills
    pso_section = ""
    try:
        runner_path = Path(__file__).resolve().parent.parent.parent / "skills" / "custom" / "healthcheck" / "scripts"
        if str(runner_path) not in sys.path:
            sys.path.insert(0, str(runner_path))
        import looker_healthcheck_runner as runner
        config = runner.load_config()
        token = runner.authenticate(config)
        pso_section = runner.generate_healthcheck_report(config, token, model_name=model_name)
    except Exception as e:
        pso_section = f"> [!NOTE]\n> Live PSO System Activity metrics skipped ({str(e)}). Proceeding with 30-check methodology scorecard.\n"

    # 2. Execute 30-Check methodology audit
    report_markdown, structured = execute_complete_healthcheck(
        model_name=model_name,
        project_id=project_id
    )
    
    combined_report = f"{pso_section}\n\n---\n\n{report_markdown}"
    save_status = save_audit_report(combined_report, structured, model_name=model_name, project_id=project_id)
    
    score = structured.get("overall_health_score", 0.0)
    passed = structured.get("passed", 0)
    warning = structured.get("warning", 0)
    critical = structured.get("critical", 0)
    total = structured.get("total_checks", 30)
    
    scope_str = f"Model: `{model_name}`" if model_name else "Instance-wide"
    
    summary_banner = (
        f"## 🏆 Consolidated Healthcheck Benchmark Complete\n"
        f"- **Scope**: {scope_str}\n"
        f"- **Overall Health Score**: **{score}/100**\n"
        f"- **Metrics Scorecard**: ✅ {passed} Passed | ⚠️ {warning} Warnings | ❌ {critical} Critical (Total: {total})\n"
        f"- **Persistence**: {save_status}\n\n"
        f"---\n\n"
    )
    
    return summary_banner + combined_report
