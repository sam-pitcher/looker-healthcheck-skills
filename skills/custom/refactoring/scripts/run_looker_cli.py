#!/usr/bin/env python3
"""
Python wrapper for looker-cli execution.
Handles project validation, branch checkouts, and content validation API calls.
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

LOOKER_CLI_BIN = os.path.expanduser(os.getenv("LOOKER_CLI_PATH", "~/.local/bin/looker-cli"))
DEFAULT_PID = os.getenv("LOOKER_PROJECT_ID", "")

def run_project_validation(project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes LookML compilation and validation via looker-cli.
    """
    pid = project_id or DEFAULT_PID
    if not pid:
        return {"status": "error", "message": "project_id is required."}
    cmd = [LOOKER_CLI_BIN, "project", "validate", pid, "--verify-ssl=false"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return {
            "status": "success" if res.returncode == 0 else "failure",
            "returncode": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_content_validation() -> Dict[str, Any]:
    """
    Executes content validation across Looks and Dashboards using looker-cli / content_validator API.
    """
    cmd = [LOOKER_CLI_BIN, "api", "content_validator", "run_content_validation", "--verify-ssl=false"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return {
            "status": "success" if res.returncode == 0 else "failure",
            "returncode": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def list_project_files(project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Lists all files in a remote LookML project via looker-cli.
    """
    pid = project_id or DEFAULT_PID
    if not pid:
        return {"status": "error", "message": "project_id is required."}
    cmd = [LOOKER_CLI_BIN, "project", "file", "ls", pid, "--plain", "--verify-ssl=false"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        files = []
        if res.returncode == 0:
            for line in res.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split("\t") if p.strip()]
                if len(parts) >= 2:
                    files.append({"id": parts[0], "path": parts[1], "type": parts[2] if len(parts) > 2 else "unknown"})
        return {
            "status": "success" if res.returncode == 0 else "failure",
            "project_id": pid,
            "total_files": len(files),
            "files": files,
            "raw_output": res.stdout or res.stderr
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def cat_project_file(project_id: Optional[str], file_path: str) -> Dict[str, Any]:
    """
    Reads the content of a LookML file from a remote project via looker-cli.
    """
    pid = project_id or DEFAULT_PID
    if not pid:
        return {"status": "error", "message": "project_id is required."}
    cmd = [LOOKER_CLI_BIN, "project", "file", "cat", pid, file_path, "--verify-ssl=false"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return {
            "status": "success" if res.returncode == 0 else "failure",
            "project_id": pid,
            "file_path": file_path,
            "content": res.stdout,
            "error": res.stderr if res.returncode != 0 else None
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if action == "validate":
        pid = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PID
        print(json.dumps(run_project_validation(pid), indent=2))
    elif action == "content":
        print(json.dumps(run_content_validation(), indent=2))
    elif action == "files":
        pid = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PID
        print(json.dumps(list_project_files(pid), indent=2))
    elif action == "cat":
        pid = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PID
        fpath = sys.argv[3] if len(sys.argv) > 3 else "models/core.model.lkml"
        print(json.dumps(cat_project_file(pid, fpath), indent=2))
