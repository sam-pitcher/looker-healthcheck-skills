"""
Transcriber 0-4 Scoring Rubric Evaluation Suite.
Evaluates LookML codebases across the 4 Focus Dimensions from playbook_transcriber_scoring.md:
  1. Dimension 1: LookML Modeling Quality (30% weight)
  2. Dimension 2: End-User Experience & Usability (25% weight)
  3. Dimension 3: Enterprise Architecture & PDT Performance (25% weight)
  4. Dimension 4: Governance & Testing (20% weight)
"""

import os
import re
from pathlib import Path
from typing import Dict, Any

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def evaluate_transcriber_score(project_path: Path) -> Dict[str, Any]:
    """
    Analyzes all .lkml files in a given project directory against the Transcriber rubric.
    Returns scores (0 to 4) for each dimension and a weighted overall score.
    """
    lkml_files = list(project_path.rglob("*.lkml"))
    if not lkml_files:
        return {"overall": 0.0, "d1": 0.0, "d2": 0.0, "d3": 0.0, "d4": 0.0, "files_checked": 0}

    total_content = ""
    for f in lkml_files:
        try:
            total_content += "\n" + f.read_text(encoding="utf-8")
        except Exception:
            pass

    # -------------------------------------------------------------
    # Dimension 1: LookML Modeling Quality (30%)
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # Dimension 2: End-User Experience (25%)
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # Dimension 3: Enterprise Architecture & PDTs (25%)
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # Dimension 4: Data Governance & Testing (20%)
    # -------------------------------------------------------------
    has_data_tests = "test:" in total_content or any("test" in str(f) for f in lkml_files)
    
    d4_score = 0.0
    if has_data_tests:
        d4_score = 4.0
    else:
        d4_score = 0.0

    # Weighted composite score: 30% D1 + 25% D2 + 25% D3 + 20% D4
    overall = round((d1_score * 0.30) + (d2_score * 0.25) + (d3_score * 0.25) + (d4_score * 0.20), 2)

    return {
        "overall": overall,
        "d1_lookml_quality": round(d1_score, 1),
        "d2_user_experience": round(d2_score, 1),
        "d3_architecture": round(d3_score, 1),
        "d4_governance_testing": round(d4_score, 1),
        "files_checked": len(lkml_files)
    }


def test_score_0_antipattern_eval():
    """Verify that the anti-pattern fixture accurately scores <= 1.0 (Unsatisfactory)."""
    bad_dir = FIXTURES_DIR / "score_0_antipattern"
    assert bad_dir.exists(), "Anti-pattern fixture directory missing."
    
    result = evaluate_transcriber_score(bad_dir)
    print(f"\n[Score 0 Anti-Pattern Fixture Evaluation] Overall Score: {result['overall']} / 4.0")
    print(f"  D1 (LookML Quality): {result['d1_lookml_quality']} / 4.0")
    print(f"  D2 (User Experience): {result['d2_user_experience']} / 4.0")
    print(f"  D3 (Architecture): {result['d3_architecture']} / 4.0")
    print(f"  D4 (Governance/Tests): {result['d4_governance_testing']} / 4.0")

    # Anti-pattern project must fail Transcriber benchmark (< 1.5)
    assert result["overall"] <= 1.5
    assert result["d4_governance_testing"] == 0.0  # No data tests


def test_score_4_exceptional_eval():
    """Verify that the enterprise fixture accurately scores >= 3.5 (Exceptional)."""
    good_dir = FIXTURES_DIR / "score_4_exceptional"
    assert good_dir.exists(), "Exceptional fixture directory missing."

    result = evaluate_transcriber_score(good_dir)
    print(f"\n[Score 4 Exceptional Fixture Evaluation] Overall Score: {result['overall']} / 4.0")
    print(f"  D1 (LookML Quality): {result['d1_lookml_quality']} / 4.0")
    print(f"  D2 (User Experience): {result['d2_user_experience']} / 4.0")
    print(f"  D3 (Architecture): {result['d3_architecture']} / 4.0")
    print(f"  D4 (Governance/Tests): {result['d4_governance_testing']} / 4.0")

    # Exceptional project must exceed expectations (>= 3.5)
    assert result["overall"] >= 3.5
    assert result["d1_lookml_quality"] >= 3.5
    assert result["d2_user_experience"] >= 3.5
    assert result["d3_architecture"] >= 3.5
    assert result["d4_governance_testing"] == 4.0
