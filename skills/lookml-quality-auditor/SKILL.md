---
name: lookml-quality-auditor
description: Audits LookML codebases against enterprise modeling standards, primary key integrity (eliminating SUM_DISTINCT symmetric aggregate fanout hashing), explicit join relationships, dead field vacuuming, and conversational AI / Gemini readiness. Scores projects on the 0–4 Transcriber Rubric.
---

# 🔍 LookML Quality Auditor

This skill audits LookML projects for semantic correctness, data modeling integrity, maintainability, and enterprise readiness.

It implements the authoritative **0–4 Transcriber Scoring Rubric** (Unsatisfactory to Exceptional) and executes a 30-check audit across:
1. **LookML Modeling Quality** (30% weight) — Primary key integrity, explicit join cardinalities, symmetric aggregate safety, casing hygiene.
2. **End-User Usability & Field Picker Hygiene** (25% weight) — Masked foreign/surrogate keys, descriptions, drill fields, field picker pruning.
3. **Enterprise Architecture & Performance** (25% weight) — Datagroups, incremental PDTs, Aggregate Awareness rollups, modular directory hierarchy.
4. **Data Governance & Development Culture** (20% weight) — LookML data tests, Git PR reviews, GBAC access control, CI validation (Spectacles / looker-cli).

---

## 🧭 When to Use This Skill

Activate this skill when:
* Auditing LookML files, views, explores, or whole projects for best practices.
* Diagnosing SQL issues caused by Looker fanouts or CPU-intensive symmetric aggregates (`SUM(DISTINCT ...)`).
* Scoring a LookML project against the 0–4 maturity rubric.
* Preparing LookML for Looker Studio or Conversational Analytics / Gemini in Looker.
* Reviewing PRs or migrating legacy LookML codebases.

---

## 🛠️ Tooling & Scripts

* **Stream LookML**:
  ```bash
  bash skills/lookml-quality-auditor/scripts/stream_lookml.sh <project_id> <output_dir>
  ```
* **Validate LookML via Looker Compiler**:
  ```bash
  bash skills/lookml-quality-auditor/scripts/validate_lookml.sh <project_id>
  ```
* **Automated Rules Scanner**:
  ```bash
  python3 skills/lookml-quality-auditor/scripts/audit_lookml_rules.py <lookml_dir>
  ```

---

## 📋 The 0–4 Transcriber Scoring Rubric

| Score | Rating | Standard Definition |
| :--- | :--- | :--- |
| **`0`** | **Unsatisfactory** | Missing primary keys on joined views (causing fanout multiplication), raw surrogate keys exposed to business users, monolithic multi-thousand-line files, no datagroups configured. |
| **`1`** | **Needs Improvement** | Fact views have primary keys, but dimension views lack them; arbitrary `persist_for: "24 hours"`; ~50% of fields lack descriptions; confusing field pickers. |
| **`2`** | **Meets Expectations** *(Baseline)* | Adheres to best practices ~85–90% of the time: Joined views have `primary_key: yes` and explicit `relationship:`; snake_case naming; major explores use datagroups. |
| **`3`** | **Exceeds Expectations** | 100% field description coverage; comprehensive `drill_fields:` on all measures; `group_label` used for multi-currency/date dims; explores capped at 40–50 fields. |
| **`4`** | **Exceptional** | State-of-the-art enterprise LookML: Dynamic Aggregate Awareness tables (`aggregate_table`); automated CI/CD pipeline running LookML tests; Hub & Spoke modular imports; strict GBAC. |

---

## 📚 Deep-Dive References

* [Transcriber 0–4 Scoring Rubric & Checklist](references/playbook_transcriber_scoring.md)
* [LookML Quality Diagnostic Playbook](references/playbook_lookml_quality.md)
* [Scoring Weights & Calculations](references/scoring_lookml_quality.md)
* [Conversational Analytics & Gemini Readiness](references/conversational_analytics_best_practices.md)
* [Content Validation & Broken Schedule Recipe](references/content_validation_recipe.md)
* [Merged Queries Remediation](references/merged_queries_remediation.md)
* [Spectacles CI Setup](references/spectacles_ci_setup.md)
* [Henry Command Guide & Dead Field Pruning](references/henry_command_guide.md)
* [Housekeeping & Orphan Content Recipe](references/house_keeping_recipe.md)
