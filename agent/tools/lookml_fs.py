"""
Generic LookML Filesystem, Modeling Hygiene, and Henry CLI Tools.
Implements Pillar 2 & LookML Modeling Checks (Tasks 11-19, 24, 26, 28).
"""

import os
import re
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

LOOKER_CLI_BIN = os.path.expanduser(os.getenv("LOOKER_CLI_PATH", "~/.local/bin/looker-cli"))

def _get_project_dir(project_path: Optional[str] = None) -> Optional[Path]:
    raw_path = project_path or os.getenv("LOOKML_PROJECT_PATH", "")
    if raw_path:
        p = Path(os.path.expanduser(raw_path))
        if p.exists():
            return p
    return None

# ==============================================================================
# PILLAR 2: LOOKML & MODELING HEALTH CHECKS (Tasks 11 to 20)
# ==============================================================================

def run_lookml_validation(project_id: Optional[str] = None) -> str:
    """
    Task 11: Project Health Validation.
    Executes LookML compilation and syntax validation for any project via looker-cli.
    """
    pid = project_id or os.getenv("LOOKER_PROJECT_ID", "")
    if not pid:
        return "Please specify a `project_id` to validate."
    try:
        cmd = [LOOKER_CLI_BIN, "project", "validate", pid, "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
        status = "PASSED" if res.returncode == 0 else "FAILED / WARNINGS"
        return f"### 🛠️ LookML Project Validation Status ({pid} - {status}):\n```\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"LookML validation error: {str(e)}"

def audit_primary_keys(project_id: Optional[str] = None, project_path: Optional[str] = None) -> str:
    """
    Task 12: Primary Key Validation.
    Ensures every joined view has a valid primary key defined with `primary_key: yes` to prevent fanout double-counting.
    """
    local_dir = _get_project_dir(project_path)
    missing_pk_views = []
    
    if local_dir:
        for view_file in local_dir.rglob("*.view.lkml"):
            try:
                content = view_file.read_text(encoding="utf-8")
                if "primary_key: yes" not in content and "primary_key:yes" not in content:
                    missing_pk_views.append(str(view_file.relative_to(local_dir)))
            except Exception:
                continue
        return f"### 🔑 Primary Key Validation ({len(missing_pk_views)} Views Missing Primary Key):\n```json\n{json.dumps(missing_pk_views, indent=2)}\n```"

    return (
        "### 🔑 Primary Key Validation Guidance:\n"
        "1. Every joined view MUST declare a `primary_key: yes` dimension.\n"
        "2. Without a primary key, symmetric aggregations fail and fan-outs produce double-counted totals.\n"
        "3. For compound keys, use `sql: CONCAT(${col_a}, '-', ${col_b}) ;;`."
    )

def audit_join_relationships(project_id: Optional[str] = None, project_path: Optional[str] = None) -> str:
    """
    Task 13: Relationship Definitions.
    Audits explores for joins missing explicit `relationship:` parameters (which default to one_to_one, causing fanouts).
    """
    local_dir = _get_project_dir(project_path)
    flagged_joins = []
    
    if local_dir:
        for model_file in local_dir.rglob("*.lkml"):
            try:
                content = model_file.read_text(encoding="utf-8")
                join_blocks = re.findall(r"join:\s*([a-zA-Z0-9_]+)\s*\{([^}]+)\}", content)
                for join_name, block in join_blocks:
                    if "relationship:" not in block:
                        flagged_joins.append({
                            "file": str(model_file.relative_to(local_dir)),
                            "join": join_name,
                            "issue": "Missing explicit relationship parameter (defaults to one_to_one)"
                        })
            except Exception:
                continue
        return f"### 🔗 Join Relationship Audit ({len(flagged_joins)} Joins Missing Explicit Relationship):\n```json\n{json.dumps(flagged_joins, indent=2)}\n```"

    return "Explicitly declare `relationship: many_to_one` or `relationship: one_to_many` on all joins."

def run_henry_vacuum(model: Optional[str] = None, explore: Optional[str] = None, timeframe: int = 90) -> str:
    """
    Task 14: Unused Field Cleanup.
    Runs `henry vacuum explores` to identify unused dimensions and measures across models and explores.
    """
    try:
        cmd = ["henry", "vacuum", f"--timeframe={timeframe}"]
        if model: cmd.extend(["--model", model])
        if explore: cmd.extend(["--explore", explore])
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
        return f"### 🧹 Henry Vacuum Results ({timeframe} Days):\n```\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"Henry execution notice: {str(e)}"

def audit_explore_field_exposure(model: Optional[str] = None, explore: Optional[str] = None) -> str:
    """
    Task 15: Explore Field Exposure.
    Runs `henry analyze explores` to audit technical database fields, primary keys, and raw foreign keys that should be `hidden: yes`.
    """
    try:
        cmd = ["henry", "analyze", "explores"]
        if model: cmd.extend(["--model", model])
        if explore: cmd.extend(["--explore", explore])
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
        return f"### 👁️ Explore Field Exposure Audit:\n```\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"Henry analyze notice: {str(e)}"

def audit_folder_structure(project_path: Optional[str] = None) -> str:
    """
    Task 16: Folder Structure Hygiene.
    Audits directory nesting inside the LookML Git repo to verify folder segregation into `/views`, `/explores`, and `/models`.
    """
    local_dir = _get_project_dir(project_path)
    if not local_dir:
        return "Please provide `project_path` to audit folder structure."
    
    subdirs = [p.name for p in local_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
    has_views = any("view" in s.lower() for s in subdirs)
    has_models = any("model" in s.lower() for s in subdirs)
    
    report = {
        "project_directory": str(local_dir),
        "subdirectories_found": subdirs,
        "views_folder_present": has_views,
        "models_folder_present": has_models,
        "status": "HEALTHY" if (has_views and has_models) else "WARNING: Files not segregated into /views and /models"
    }
    return f"### 📁 LookML Folder Structure Hygiene:\n```json\n{json.dumps(report, indent=2)}\n```"

def audit_naming_conventions(project_path: Optional[str] = None) -> str:
    """
    Task 17: Standard Naming Strategy.
    Runs regex analysis across project files to catch non-standard naming (mixing camelCase and snake_case).
    """
    local_dir = _get_project_dir(project_path)
    if not local_dir:
        return "Standardize all dimension, measure, and explore identifiers to `snake_case`."
    
    inconsistent = []
    for lkml_file in local_dir.rglob("*.lkml"):
        try:
            content = lkml_file.read_text(encoding="utf-8")
            camel_matches = re.findall(r"(dimension|measure|explore):\s*([a-z0-9_]*[A-Z][a-zA-Z0-9_]*)", content)
            for f_type, name in camel_matches:
                inconsistent.append({"file": str(lkml_file.relative_to(local_dir)), "type": f_type, "identifier": name})
        except Exception:
            continue
            
    return f"### 🔤 Naming Convention Audit ({len(inconsistent)} CamelCase Identifiers Found):\n```json\n{json.dumps(inconsistent[:30], indent=2)}\n```"

def audit_metadata_descriptions(model_name: Optional[str] = None) -> str:
    """
    Task 18: Metadata & Descriptions.
    Audits dimensions and measures missing descriptions for UI tooltips using `henry analyze models/views`.
    """
    try:
        cmd = ["henry", "analyze", "models"]
        if model_name: cmd.extend(["--model", model_name])
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
        return f"### 📝 Metadata & Description Audit:\n```\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"Metadata audit notice: {str(e)}"

def audit_unused_joins(model: Optional[str] = None, explore: Optional[str] = None) -> str:
    """
    Task 19: Unused Joins Assessment.
    Runs `henry analyze explores --unused_joins` to identify redundant left joins never selected in user query runs.
    """
    try:
        cmd = ["henry", "analyze", "explores", "--unused_joins"]
        if model: cmd.extend(["--model", model])
        if explore: cmd.extend(["--explore", explore])
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
        return f"### ⛓️ Unused Joins Assessment:\n```\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"Unused joins audit notice: {str(e)}"

# ==============================================================================
# DERIVED TABLE & SYNTAX CHECKS (Tasks 24, 26, 28)
# ==============================================================================

def audit_incremental_pdts(project_path: Optional[str] = None) -> str:
    """
    Task 24: Incremental PDTs Audit.
    Searches derived table views to find static derived tables missing `increment_key` and `increment_offset`.
    """
    local_dir = _get_project_dir(project_path)
    if not local_dir:
        return "Implement `increment_key` on derived tables scanning large date-partitioned datasets."
    
    static_pdts = []
    for view_file in local_dir.rglob("*.view.lkml"):
        try:
            content = view_file.read_text(encoding="utf-8")
            if ("derived_table:" in content or "datagroup_trigger:" in content) and "increment_key:" not in content:
                static_pdts.append(str(view_file.relative_to(local_dir)))
        except Exception:
            continue
            
    return f"### ⏳ Incremental PDT Audit ({len(static_pdts)} Derived Tables Missing `increment_key`):\n```json\n{json.dumps(static_pdts, indent=2)}\n```"

def audit_oauth_connections(connection_name: Optional[str] = None) -> str:
    """
    Task 26: OAuth Caching Configuration.
    Verifies that connections relying on user OAuth use `persist_for` instead of datagroups to prevent regenerator failures.
    """
    cmd = [LOOKER_CLI_BIN, "connection", "ls", "--token-file"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        return f"### 🔐 OAuth Connection & PDT Regenerator Audit:\n```\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"OAuth connection notice: {str(e)}"

def audit_join_key_syntax(project_path: Optional[str] = None) -> str:
    """
    Task 28: Join Logic Optimization.
    Audits `sql_on` join clauses for string concatenations or function wrappers that prevent BigQuery hash joins.
    """
    local_dir = _get_project_dir(project_path)
    if not local_dir:
        return "Join on raw integer/base keys rather than string concatenations (CONCAT) to optimize warehouse hash joins."
    
    flagged = []
    for lkml_file in local_dir.rglob("*.lkml"):
        try:
            content = lkml_file.read_text(encoding="utf-8")
            concat_joins = re.findall(r"sql_on:\s*.*(CONCAT|concat|CAST|cast|COALESCE|coalesce).*", content)
            if concat_joins:
                flagged.append({"file": str(lkml_file.relative_to(local_dir)), "matches": concat_joins})
        except Exception:
            continue
            
    return f"### ⚡ Join Key Syntax Optimization ({len(flagged)} Files with String Operations in `sql_on`):\n```json\n{json.dumps(flagged, indent=2)}\n```"

# Basic File Operations
def list_lookml_files(project_id: Optional[str] = None, project_path: Optional[str] = None) -> str:
    """Lists LookML files."""
    local_dir = _get_project_dir(project_path)
    if local_dir:
        files = [str(p.relative_to(local_dir)) for p in local_dir.rglob("*.lkml")]
        return f"### LookML Files ({len(files)}):\n```json\n{json.dumps(files, indent=2)}\n```"
    pid = project_id or os.getenv("LOOKER_PROJECT_ID", "")
    try:
        cmd = [LOOKER_CLI_BIN, "project", "file", "ls", pid, "--plain", "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        return f"### Remote LookML Files:\n```\n{res.stdout}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def read_lookml_file(file_path: str, project_id: Optional[str] = None, project_path: Optional[str] = None) -> str:
    """Reads a LookML file."""
    local_dir = _get_project_dir(project_path)
    if local_dir:
        target = local_dir / file_path.lstrip("/")
        if target.exists():
            return f"### Content of `{file_path}`:\n```lookml\n{target.read_text(encoding='utf-8')}\n```"
    pid = project_id or os.getenv("LOOKER_PROJECT_ID", "")
    try:
        cmd = [LOOKER_CLI_BIN, "project", "file", "cat", pid, file_path.lstrip("/"), "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        return f"### Remote Content of `{file_path}`:\n```lookml\n{res.stdout}\n```"
    except Exception as e:
        return f"Error: {str(e)}"

def search_lookml_code(pattern: str, project_id: Optional[str] = None, project_path: Optional[str] = None) -> str:
    """Searches LookML code."""
    local_dir = _get_project_dir(project_path)
    if local_dir:
        results = []
        for p in local_dir.rglob("*.lkml"):
            try:
                c = p.read_text(encoding="utf-8")
                if re.search(pattern, c, re.IGNORECASE):
                    results.append(str(p.relative_to(local_dir)))
            except Exception:
                continue
        return f"### Search Results for `{pattern}`:\n```json\n{json.dumps(results, indent=2)}\n```"
    return f"Search for pattern: {pattern}"

def apply_lookml_patch(file_path: str, patch_content: str, project_path: Optional[str] = None, create_backup: bool = True) -> str:
    """Applies code patch to a LookML file."""
    local_dir = _get_project_dir(project_path)
    if not local_dir:
        return "Local project directory not found."
    target = local_dir / file_path.lstrip("/")
    if target.exists() and create_backup:
        target.with_suffix(target.suffix + ".bak").write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.write_text(patch_content, encoding="utf-8")
    return f"✅ Applied patch to `{file_path}`"
