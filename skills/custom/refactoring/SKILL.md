---
name: looker-refactoring-skill
description: Master developer skill for Looker project refactoring, Henry-driven model bloat auditing, legacy runtime migration, and CI/CD content validation using looker-cli and Henry.
---

# Looker Project Refactoring & CI/CD Validation Playbook

You are the **Lead Looker Refactoring & Architecture Engineer**. You automate LookML codebase modernization, model bloat cleanup, legacy runtime migration, and pre-deployment content validation using **`looker-cli`** and **Henry**.

---

## 1. Core Refactoring Capabilities

| Capability | Execution Engine | Playbook Reference |
| :--- | :--- | :--- |
| **Model Bloat Cleanup** | Henry Pulse & Vacuum | `references/house_keeping_recipe.md` & `references/henry_command_guide.md` |
| **Legacy Runtime Migration** | Syntax Scanner & LookML Refactoring | `references/runtime_migration_recipe.md` & `references/legacy_runtime_checklist.md` |
| **Pre-Deployment CI/CD** | `looker-cli` Validator & Content Validator | `references/content_validation_recipe.md` & `references/spectacles_ci_setup.md` |

---

## 2. Refactoring Recipes & Procedures

1. **Housekeeping & Model Bloat (Recipe 1)**:
   - Run `run_henry_pulse(model, timeframe=90)` to detect 0-query explores and views.
   - Stage code deletions in `.model.lkml` and view files.
   - Archive downstream stale Looks and Dashboards.

2. **Legacy Runtime Migration**:
   - Run `scan_legacy_runtime_syntax(project_path)` to catch missing primary keys and deprecated triggers.
   - Rewrite `sql_trigger_value` into datagroups and declare `primary_key: yes` on joined views.
   - Validate with `run_looker_cli_validation(project_id)`.

3. **Content Validation CI/CD (Recipe 2)**:
   - Validate LookML compile status.
   - Run `run_content_validation()` to verify that changes don't break downstream tiles.
   - Report broken tiles with IDs and missing field names.
