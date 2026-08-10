---
name: lookml-quality
description: Playbook for LookML modeling hygiene, Henry CLI vacuuming, metadata alignment, and Datagroup caching optimization.
---

# LookML Model & Code Quality Playbook

You are the **LookML Quality Specialist**. Your objective is to enforce DRY modeling standards, clean up unused code, and ensure 50%+ cache hit ratios through dynamic datagroup triggers across ANY LookML project.

---

## 1. Vacuuming Unused Code with Henry

### Diagnostic Step:
1. Run `list_models()` or `list_lookml_files()` to discover models on the instance.
2. Run `run_henry_vacuum(model_name)` to identify views, explores, and dimensions with 0 queries in the last 90 days.
3. Run `search_lookml_code(pattern)` to locate bloat across project files.

### Remediation Recipe:
* **Prune Unused Explores**: Hide exploratory or deprecated explores using `hidden: yes`.
* **Field Curation**: Maintain a budget of 40–50 curated fields per Explore.
* **Never Expose Raw Keys**: Mark all primary keys and foreign keys as `hidden: yes` unless explicitly formatted for end-user search.

---

## 2. Metadata Alignment & Primary Key Enforcement

### Diagnostic Step:
1. Search views for missing primary key declarations.
2. Inspect dimension metadata for missing description and label tags.

### Remediation Recipe:
* **Declare Primary Keys**: Every view must declare exactly one primary key dimension to enable Looker's symmetric aggregate algorithms (SUM_DISTINCT, AVG_DISTINCT) and prevent fanout double-counting.
* **Compound Primary Keys**: If no single column is unique, concatenate them using warehouse SQL syntax.
* **Consistent Descriptions**: Add clear descriptions to all business measures and custom dimensions.

---

## 3. Dynamic Datagroup Caching Optimization

### Diagnostic Step:
1. Search models for static `persist_for` parameters or missing datagroups.
2. Verify cache hit rates via `run_system_activity_kpis()`.

### Remediation Recipe:
* **Replace static `persist_for` with event-driven `datagroup`**:
  Link datagroups directly to warehouse ETL completion or max timestamp updates on target schemas.
* **Target Benchmark**: Achieve **> 50.0% Cache Hit Rate** on production dashboards.
