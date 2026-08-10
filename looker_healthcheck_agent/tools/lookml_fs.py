"""
Generic LookML Filesystem, Git, and Looker CLI Quality Tools.
Operates dynamically across ANY Looker project and LookML codebase.
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

def list_lookml_files(project_id: Optional[str] = None, project_path: Optional[str] = None) -> str:
    """
    Lists all LookML model, view, and explore files for any project.
    Reads from a local filesystem directory if available, or fetches remotely from Looker via looker-cli.
    
    Args:
        project_id (str, optional): Target Looker project ID (e.g. 'analytics', 'marketing_hub').
        project_path (str, optional): Path to local Git repository clone if analyzing locally.
    """
    local_dir = _get_project_dir(project_path)
    if local_dir:
        try:
            models = [str(p.relative_to(local_dir)) for p in local_dir.rglob("*.model.lkml")]
            views = [str(p.relative_to(local_dir)) for p in local_dir.rglob("*.view.lkml")]
            explores = [str(p.relative_to(local_dir)) for p in local_dir.rglob("*.explore.lkml")]
            summary = {
                "source": "local_filesystem",
                "project_directory": str(local_dir),
                "total_files": len(models) + len(views) + len(explores),
                "models": sorted(models),
                "explores": sorted(explores),
                "views": sorted(views)
            }
            return f"### 📂 Project LookML Files (Local: `{local_dir}`):\n```json\n{json.dumps(summary, indent=2)}\n```"
        except Exception:
            pass

    pid = project_id or os.getenv("LOOKER_PROJECT_ID", "")
    if not pid:
        return "Please specify a `project_id` or configure `LOOKML_PROJECT_PATH` in environment."

    try:
        cmd = [LOOKER_CLI_BIN, "project", "file", "ls", pid, "--plain", "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
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
        return f"Error listing LookML files for project `{pid}`: {res.stderr or res.stdout}"
    except Exception as e:
        return f"Error listing LookML files: {str(e)}"

def read_lookml_file(file_path: str, project_id: Optional[str] = None, project_path: Optional[str] = None) -> str:
    """
    Reads the full raw content of any LookML file (e.g. 'models/core.model.lkml' or 'views/users.view.lkml').
    Reads from local filesystem if found, otherwise fetches remotely from Looker via looker-cli.
    
    Args:
        file_path (str): Relative path to the LookML file within the project.
        project_id (str, optional): Target Looker project ID if fetching remotely.
        project_path (str, optional): Path to local Git repository clone.
    """
    local_dir = _get_project_dir(project_path)
    if local_dir:
        target = local_dir / file_path.lstrip("/")
        if target.exists():
            try:
                content = target.read_text(encoding="utf-8")
                return f"### 📄 Content of `{file_path}` (Local):\n```lookml\n{content}\n```"
            except Exception:
                pass

    pid = project_id or os.getenv("LOOKER_PROJECT_ID", "")
    if not pid:
        return f"Please provide `project_id` or set `LOOKML_PROJECT_PATH` to read `{file_path}`."

    try:
        clean_path = file_path.lstrip("/")
        cmd = [LOOKER_CLI_BIN, "project", "file", "cat", pid, clean_path, "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        if res.returncode == 0 and res.stdout:
            return f"### 📄 Content of `{file_path}` (Remote `{pid}` via looker-cli):\n```lookml\n{res.stdout}\n```"
        return f"❌ File `{file_path}` could not be retrieved from `{pid}`: {res.stderr or 'File not found'}"
    except Exception as e:
        return f"Error reading file `{file_path}`: {str(e)}"

def search_lookml_code(pattern: str, project_id: Optional[str] = None, project_path: Optional[str] = None) -> str:
    """
    Searches across LookML files for any keyword or regex pattern (e.g. 'datagroup', 'persist_with', 'primary_key').
    
    Args:
        pattern (str): Search pattern or regex.
        project_id (str, optional): Target Looker project ID.
        project_path (str, optional): Path to local repository.
    """
    local_dir = _get_project_dir(project_path)
    try:
        results = []
        if local_dir:
            for lkml_file in local_dir.rglob("*.lkml"):
                try:
                    content = lkml_file.read_text(encoding="utf-8")
                    matches = [m.start() for m in re.finditer(pattern, content, re.IGNORECASE)]
                    if matches:
                        rel = str(lkml_file.relative_to(local_dir))
                        results.append({"file": rel, "match_count": len(matches)})
                except Exception:
                    continue
        else:
            pid = project_id or os.getenv("LOOKER_PROJECT_ID", "")
            if not pid:
                return "Please specify `project_id` or `project_path` to search LookML code."
            cmd = [LOOKER_CLI_BIN, "project", "file", "ls", pid, "--plain", "--verify-ssl=false"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
            if res.returncode == 0:
                files = [line.split("\t")[0] for line in res.stdout.strip().split("\n") if line.strip() and ".lkml" in line]
                for fpath in files:
                    cat_cmd = [LOOKER_CLI_BIN, "project", "file", "cat", pid, fpath, "--verify-ssl=false"]
                    cat_res = subprocess.run(cat_cmd, capture_output=True, text=True, check=False, timeout=15)
                    if cat_res.returncode == 0:
                        matches = [m.start() for m in re.finditer(pattern, cat_res.stdout, re.IGNORECASE)]
                        if matches:
                            results.append({"file": fpath, "match_count": len(matches)})

        return f"### 🔎 Search Results for `{pattern}`:\n```json\n{json.dumps(results, indent=2)}\n```"
    except Exception as e:
        return f"Error searching LookML: {str(e)}"

def run_henry_vacuum(model: Optional[str] = None, explore: Optional[str] = None, timeframe: int = 90) -> str:
    """
    Executes Henry CLI vacuum to identify unused models, explores, and fields across any model.
    
    Args:
        model (str, optional): Target LookML model name.
        explore (str, optional): Target LookML explore name.
        timeframe (int): Audit timeframe in days (default: 90).
    """
    try:
        cmd = ["henry", "vacuum", f"--timeframe={timeframe}"]
        if model:
            cmd.extend(["--model", model])
        if explore:
            cmd.extend(["--explore", explore])
            
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
        output = res.stdout if res.stdout else res.stderr
        return f"### 🧹 Henry Vacuum Results ({timeframe} Days):\n```\n{output}\n```"
    except Exception as e:
        try:
            cmd = [sys.executable, "-m", "henry", "vacuum", f"--timeframe={timeframe}"]
            if model:
                cmd.extend(["--model", model])
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
            return f"### 🧹 Henry Vacuum Results ({timeframe} Days):\n```\n{res.stdout or res.stderr}\n```"
        except Exception as fallback_e:
            return f"Henry execution failed: {str(e)} (Fallback: {str(fallback_e)})"

def apply_lookml_patch(file_path: str, patch_content: str, project_path: Optional[str] = None, create_backup: bool = True) -> str:
    """
    Applies updated LookML code to any file in the local project repository.
    
    Args:
        file_path (str): Relative path to the .lkml file.
        patch_content (str): Complete updated code content for the file.
        project_path (str, optional): Path to local project directory.
        create_backup (bool): Whether to create a .bak backup file (default: True).
    """
    local_dir = _get_project_dir(project_path)
    if not local_dir:
        return f"Cannot write to local file: Local repository path `{project_path}` not found."
    try:
        target = local_dir / file_path.lstrip("/")
        if not target.parent.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            
        if target.exists() and create_backup:
            bak_path = target.with_suffix(target.suffix + ".bak")
            bak_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
            
        target.write_text(patch_content, encoding="utf-8")
        return f"✅ Successfully updated LookML file `{file_path}`. Backup created: {create_backup}"
    except Exception as e:
        return f"Error applying LookML patch to `{file_path}`: {str(e)}"

def run_lookml_validation(project_id: Optional[str] = None) -> str:
    """
    Executes LookML compilation and syntax validation for any project via looker-cli.
    
    Args:
        project_id (str, optional): Target LookML project ID.
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
