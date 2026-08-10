# History Query Analysis & Persona Profiling (Deep-Dive)

This reference document defines the **Persona-Based Query Segmentation**, **Query Complexity Categorization (Clean vs Feature-Laden)**, and **Dashboard Error/Killed Query Rate** metrics extracted from the `google_pso__history_query_analysis` dashboard.

---

## 1. User Persona Query Profiling

Segmenting query performance by user tier isolates whether slow queries impact developers, ad-hoc analysts, or broad executive viewers:

| Persona Tier | Filter Condition | Target Average Runtime | Primary Bottleneck Risk |
| :--- | :--- | :---: | :--- |
| **Viewer Users** | `user_facts.is_viewer: 'Yes'` | **`< 3.0s`** | Dashboard tile bloat; un-cached production views. |
| **Explorer Users** | `user_facts.is_explorer: 'Yes'` | **`< 5.0s`** | Massive row limits, ad-hoc custom fields, unindexed explores. |
| **Developers** | `user_facts.is_developer: 'Yes'` | **`< 10.0s`** | Dev-mode cache invalidation; compiling uncommitted LookML. |
| **Admins** | `user_facts.is_admin: 'Yes'` | **`-`** | Heavy System Activity audits and maintenance scripts. |

---

## 2. Query Complexity Classification: Clean vs Feature-Laden

Understanding whether latency comes from base SQL or client-side transformations:

```
                                  LOOKER QUERY COMPLEXITY
                                             │
        ┌────────────────────────────────────┼────────────────────────────────────┐
        ▼                                    ▼                                    ▼
[CLEAN BASELINE QUERIES]            [CUSTOM FIELD QUERIES]               [PIVOT & TOTAL QUERIES]
Filters:                             Filter:                              Filters:
 • query.total: 'No'                  • query.dynamic_fields: "-EMPTY"     • query.formatted_pivots: "-EMPTY"
 • query.row_totals: 'No'            Symptom:                             • query.row_totals: 'Yes'
 • query.formatted_pivots: EMPTY      Ad-hoc calculations created by       • query.total: 'Yes'
 • query.dynamic_fields: EMPTY        explorers in the UI.                 Symptom:
Baseline SQL performance.            Remediation: Migrate to LookML.      Separate subtotal queries + RAM pivots.
```

---

## 3. Error Rate & Killed Query Diagnostics

### Formulas:
$$ \text{Dashboard Error Rate \%} = \frac{\text{Count of Database Queries with Status 'error'}}{\text{Total Database Queries for Dashboard}} \times 100 $$
$$ \text{Dashboard Killed Rate \%} = \frac{\text{Count of Database Queries with Status 'killed'}}{\text{Total Database Queries for Dashboard}} \times 100 $$

> [!IMPORTANT]
> **Killed Query Warning**: Dashboards with a high **Killed Query Rate** indicate end-user abandonment. Users are hitting "Cancel" or closing their browser tabs because the dashboard takes too long to load.

---

## 4. Analytical System Activity Queries

### A. Dashboard Error & Killed Rates
```json
{
  "model": "system__activity",
  "view": "history",
  "fields": [
    "dashboard.title",
    "history.database_result_query_count",
    "history.query_run_count"
  ],
  "filters": {
    "history.status": "error,killed",
    "dashboard.title": "-NULL"
  },
  "sorts": ["history.query_run_count desc"],
  "limit": "15"
}
```

### B. Top 50 Most Frequent Errors
```json
{
  "model": "system__activity",
  "view": "history",
  "fields": ["history.message", "history.query_run_count"],
  "filters": {"history.status": "error", "history.message": "-NULL"},
  "sorts": ["history.query_run_count desc"],
  "limit": "50"
}
```

### C. Top 20 Most Frequent Queries (Candidates for Aggregate Awareness)
```json
{
  "model": "system__activity",
  "view": "history",
  "fields": ["history.query_run_count", "query.link", "query.model", "query.view"],
  "sorts": ["history.query_run_count desc"],
  "limit": "20"
}
```
