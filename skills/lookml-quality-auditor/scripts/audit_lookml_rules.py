#!/usr/bin/env python3
"""
LookML Quality Rules Auditor & 0-4 Transcriber Scoring Engine.
Scans LookML files (.lkml) across a repository or directory and computes
scores across the 4 Focus Dimensions:
  1. Dimension 1: LookML Modeling Quality (30% weight)
  2. Dimension 2: End-User Experience & Usability (25% weight)
  3. Dimension 3: Enterprise Architecture & PDT Performance (25% weight)
  4. Dimension 4: Data Governance & Testing (20% weight)
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any


def evaluate_lookml_project(project_path: Path) -> Dict[str, Any]:
    lkml_files = list(project_path.rglob("*.lkml"))
    if not lkml_files:
        return {
            "overall_score": 0.0,
            "rating": "No LookML files found",
            "dimensions": {},
            "files_scanned": 0
        }

    total_content = ""
    for f in lkml_files:
        try:
            total_content += "\n" + f.read_text(encoding="utf-8")
        except Exception:
            pass

    # Dimension 1: Modeling Quality (30%)
    has_pk = "primary_key: yes" in total_content
    has_explicit_rel = bool(re.search(r"relationship:\s*(many_to_one|one_to_many|one_to_one)", total_content))
    has_bad_casing = bool(re.search(r"\b(dimension|measure):\s*[A-Z]", total_content))
    
    d1_score = 0.0
    if has_pk:
        d1_score += 1.5
    if has_explicit_rel:
        d1_score += 1.5
    if not has_bad_casing:
        d1_score += 1.0
    d1_score = min(4.0, d1_score)

    # Dimension 2: End-User Experience (25%)
    has_hidden_keys = "hidden: yes" in total_content
    has_descriptions = "description:" in total_content
    has_drill_fields = "drill_fields:" in total_content
    
    d2_score = 0.0
    if has_hidden_keys:
        d2_score += 1.5
    if has_descriptions:
        d2_score += 1.5
    if has_drill_fields:
        d2_score += 1.0
    d2_score = min(4.0, d2_score)

    # Dimension 3: Enterprise Architecture & PDTs (25%)
    has_datagroups = "datagroup:" in total_content or "datagroup_trigger:" in total_content or "persist_with:" in total_content
    has_aggregate_table = "aggregate_table:" in total_content
    is_modular = any("explores" in str(f) for f in lkml_files) and any("views" in str(f) for f in lkml_files)
    
    d3_score = 0.0
    if has_datagroups:
        d3_score += 1.5
    if has_aggregate_table:
        d3_score += 1.5
    if is_modular:
        d3_score += 1.0
    d3_score = min(4.0, d3_score)

    # Dimension 4: Data Governance & Testing (20%)
    has_data_tests = "test:" in total_content or any("test" in str(f) for f in lkml_files)
    d4_score = 4.0 if has_data_tests else 0.0

    # Composite 0-4 score
    overall = round((d1_score * 0.30) + (d2_score * 0.25) + (d3_score * 0.25) + (d4_score * 0.20), 2)

    rating_map = [
        (0.0, 0.99, "0 - Unsatisfactory"),
        (1.0, 1.99, "1 - Needs Improvement"),
        (2.0, 2.99, "2 - Meets Expectations"),
        (3.0, 3.49, "3 - Exceeds Expectations"),
        (3.5, 4.0, "4 - Exceptional"),
    ]
    rating = "Unknown"
    for low, high, label in rating_map:
        if low <= overall <= high:
            rating = label
            break

    return {
        "overall_score": overall,
        "rating": rating,
        "files_scanned": len(lkml_files),
        "dimensions": {
            "d1_lookml_quality": round(d1_score, 1),
            "d2_user_experience": round(d2_score, 1),
            "d3_architecture": round(d3_score, 1),
            "d4_governance_testing": round(d4_score, 1)
        },
        "findings": {
            "has_primary_keys": has_pk,
            "has_explicit_join_relationships": has_explicit_rel,
            "has_proper_casing": not has_bad_casing,
            "has_hidden_surrogate_keys": has_hidden_keys,
            "has_descriptions": has_descriptions,
            "has_drill_fields": has_drill_fields,
            "has_datagroups": has_datagroups,
            "has_aggregate_tables": has_aggregate_table,
            "is_modular_hierarchy": is_modular,
            "has_data_tests": has_data_tests
        }
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 audit_lookml_rules.py <lookml_dir_or_project>")
        sys.exit(1)

    target_dir = Path(sys.argv[1]).resolve()
    if not target_dir.exists():
        print(f"Error: Directory not found: {target_dir}")
        sys.exit(1)

    results = evaluate_lookml_project(target_dir)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
