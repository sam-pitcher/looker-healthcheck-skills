---
name: looker-performance-auditor
description: Audits Looker query lifecycle latency (Looker JVM overhead % vs DB execution vs connection wait), dashboard tile density, auto-refresh intervals, schedule staggering, and System Activity history.
---

# ⚡ Looker Performance & Content Auditor

This skill audits Looker instance performance, query lifecycle phases, dashboard bloat, and content governance.

It isolates whether latency stems from **Looker JVM processing**, **database execution**, or **connection queue starvation**, and prescribes specific architectural fixes.

---

## 🧭 When to Use This Skill

Activate this skill when:
* Users report that Looker dashboards or explores are running slowly.
* Diagnosing whether query slowness is caused by Looker (table calculations, rendering) or the underlying warehouse.
* Auditing dashboard hygiene (tile counts > 25, unchecked auto-refresh intervals).
* Analyzing query queueing and connection pool contention.
* Re-architecting scheduled delivery plans stacked at top-of-hour (`:00`).

---

## 🛠️ Tooling & Scripts

* **Looker System Activity Runner**:
  ```bash
  looker-cli query runquery '<JSON>'
  ```
* **Safe CLI Wrapper**:
  ```bash
  bash skills/looker-bq-healthcheck/scripts/safe_looker.sh query_metrics run ...
  ```

---

## 📋 The 3-Way Latency Triage Methodology

Deconstruct query duration via `system__activity/query_metrics`:

$$\text{Looker Overhead \%} = \frac{\text{async\_processing} - (\text{execute\_main\_query} + \text{acquire\_connection})}{\text{async\_processing}} \times 100$$

| Metric | Target SLA | Root Cause If High | Remediation Playbook |
| :--- | :--- | :--- | :--- |
| **Looker JVM Overhead %** | **< 20%** | Heavy table calculations, giant pivot tables, unmerged dimensions, complex Liquid templating. | Shift computations to LookML measures or warehouse views; prune exposed fields. |
| **Database Execution Time** | **< 5.0s** | Unpartitioned table scans, missing primary keys (symmetric aggregation), un-indexed filters. | See `lookml-quality-auditor` and `bq-jobs-diagnostics`. |
| **Connection Wait Time** | **< 0.25s** | Exhausted connection pool, massive concurrency burst (>25 tiles loading simultaneously). | Lower dashboard tile density; increase max connections; stagger schedules. |

---

## 📚 Deep-Dive References

* [Looker Performance Playbook](references/playbook_looker_performance.md)
* [Content Governance & Scheduling Playbook](references/playbook_content_governance.md)
* [Query Latency Phase Breakdown](references/query_latency_breakdown.md)
* [System Activity Audit Queries](references/system_activity_queries.md)
* [History Query Analysis](references/history_query_analysis.md)
* [Query Outliers Diagnosis](references/query_outliers_diagnosis.md)
* [Large Dashboards Optimization (>25 Tiles)](references/large_dashboards_optimization.md)
* [Single Dashboard Optimization Checklist](references/single_dashboard_optimization.md)
* [Scheduled Content Staggering](references/content_delivery_schedules.md)
* [Performance Benchmarks](references/benchmarks.md)
