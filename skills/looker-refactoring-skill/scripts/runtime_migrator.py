#!/usr/bin/env python3
"""
LookML Runtime Migrator & Syntax Scanner.
Detects legacy LookML parameters and missing primary keys to ensure compatibility with modern Looker runtime.
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List

DEPRECATED_PATTERNS = [
    (r"sql_trigger_value\s*:", "Deprecated `sql_trigger_value` parameter found. Migrate to `datagroup_trigger` or `interval_trigger`."),
    (r"view:\s*\+\w+", "Refinement found without proper include or modern runtime declaration."),
    (r"measure:\s*\w+\s*\{[^}]*type:\s*count_distinct[^}]*sql:\s*\$\{TABLE\}\.", "Legacy count_distinct syntax without symmetric aggregates safety."),
]

def scan_lookml_project(project_dir: str) -> Dict[str, Any]:
    """
    Scans all .lkml files in a directory for legacy syntax and missing primary keys.
    """
    p = Path(project_dir)
    if not p.exists():
        return {"status": "error", "message": f"Path {project_dir} does not exist"}

    findings = []
    view_files = list(p.rglob("*.view.lkml"))
    model_files = list(p.rglob("*.model.lkml"))

    # 1. Scan for primary keys in view files
    for vf in view_files:
        content = vf.read_text(encoding="utf-8", errors="ignore")
        if "primary_key: yes" not in content and "primary_key:yes" not in content:
            findings.append({
                "file": str(vf.relative_to(p)),
                "type": "MISSING_PRIMARY_KEY",
                "severity": "HIGH",
                "message": "View is missing a declared `primary_key: yes` dimension. Risk of symmetric join calculation errors."
            })

    # 2. Scan for deprecated keywords
    for lkml_file in list(view_files) + list(model_files) + list(p.rglob("*.explore.lkml")):
        content = lkml_file.read_text(encoding="utf-8", errors="ignore")
        for pattern, msg in DEPRECATED_PATTERNS:
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                findings.append({
                    "file": str(lkml_file.relative_to(p)),
                    "type": "LEGACY_SYNTAX",
                    "severity": "WARNING",
                    "message": msg
                })

    return {
        "status": "success",
        "scanned_files": len(view_files) + len(model_files),
        "total_findings": len(findings),
        "findings": findings
    }

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/Users/sampitcher/Documents/Projects/thelook-antigravity"
    print(json.dumps(scan_lookml_project(target), indent=2))
