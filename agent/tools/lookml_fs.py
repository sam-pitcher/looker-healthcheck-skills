"""
LookML Filesystem, Git, and Looker CLI Quality Tools.
Handles local/remote file reading, Henry CLI vacuuming, LookML linting, and patch applications.
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
LOOKML_PROJECT_DIR = Path(os.path.expanduser(os.getenv("LOOKML_PROJECT_PATH", "~/Documents/Projects/thelook-antigravity")))
LOOKER_PROJECT_ID = os.getenv("LOOKER_PROJECT_ID", "thelook-antigravity")

def list_lookml_files(project_id: Optional[str] = None) -> str:
    """
    Lists all LookML model, view, and explore files in the target project.
    Reads from local filesystem if found, otherwise queries Looker remotely via looker-cli.
    
    Args:
        project_id (str, optional): Target LookML project ID (default: from .env).
    """
    pid = project_id or LOOKER_PROJECT_ID
    if LOOKML_PROJECT_DIR.exists():
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
        return f"Error listing LookML files: {res.stderr or res.stdout}"
    except Exception as e:
        return f"Error listing LookML files: {str(e)}"

def read_lookml_file(relative_path: str, project_id: Optional[str] = None) -> str:
    """
    Reads the full raw content of any LookML file (e.g. 'models/thelook.model.lkml').
    Reads from local filesystem if found, otherwise fetches remotely via looker-cli.
    
    Args:
        relative_path (str): Relative path to the file.
        project_id (str, optional): Target LookML project ID.
    """
    pid = project_id or LOOKER_PROJECT_ID
    if LOOKML_PROJECT_DIR.exists():
        file_path = LOOKML_PROJECT_DIR / relative_path.lstrip("/")
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                return f"### 📄 Content of `{relative_path}` (Local):\n```lookml\n{content}\n```"
            except Exception:
                pass

    try:
        clean_path = relative_path.lstrip("/")
        cmd = [LOOKER_CLI_BIN, "project", "file", "cat", pid, clean_path, "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        if res.returncode == 0 and res.stdout:
            return f"### 📄 Content of `{relative_path}` (Remote `{pid}` via looker-cli):\n```lookml\n{res.stdout}\n```"
        return f"❌ File `{relative_path}` could not be retrieved from `{pid}`: {res.stderr or 'Not found'}"
    except Exception as e:
        return f"Error reading file `{relative_path}`: {str(e)}"

def search_lookml_code(pattern: str, project_id: Optional[str] = None) -> str:
    """
    Searches across LookML files for keywords or regex (e.g. 'datagroup', 'persist_with', 'primary_key').
    
    Args:
        pattern (str): Search pattern / regex.
        project_id (str, optional): Target LookML project ID.
    """
    pid = project_id or LOOKER_PROJECT_ID
    try:
        results = []
        if LOOKML_PROJECT_DIR.exists():
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
    Executes Henry CLI vacuum to identify unused models, explores, and fields over X days.
    
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
        # Fallback to python module execution if available
        try:
            cmd = [sys.executable, "-m", "henry", "vacuum", f"--timeframe={timeframe}"]
            if model:
                cmd.extend(["--model", model])
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
            return f"### 🧹 Henry Vacuum Results ({timeframe} Days):\n```\n{res.stdout or res.stderr}\n```"
        except Exception as fallback_e:
            return f"Henry execution failed: {str(e)} (Fallback: {str(fallback_e)})"

def apply_lookml_patch(file_path: str, patch_content: str, create_backup: bool = True) -> str:
    """
    Applies updated LookML code to a target file in the local project repository.
    
    Args:
        file_path (str): Relative or absolute path to the .lkml file.
        patch_content (str): Complete updated code content for the file.
        create_backup (bool): Whether to create a .bak backup file (default: True).
    """
    try:
        target = LOOKML_PROJECT_DIR / file_path.lstrip("/")
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
    Executes LookML compilation and syntax validation via looker-cli.
    
    Args:
        project_id (str, optional): Target LookML project ID.
    """
    pid = project_id or LOOKER_PROJECT_ID
    try:
        cmd = [LOOKER_CLI_BIN, "project", "validate", pid, "--verify-ssl=false"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
        status = "PASSED" if res.returncode == 0 else "FAILED / WARNINGS"
        return f"### 🛠️ LookML Project Validation Status ({pid} - {status}):\n```\n{res.stdout or res.stderr}\n```"
    except Exception as e:
        return f"LookML validation error: {str(e)}"
