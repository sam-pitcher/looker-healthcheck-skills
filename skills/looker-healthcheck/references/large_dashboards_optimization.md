# Large Dashboards & Auto-Refresh Optimization (Deep-Dive)

This reference document defines the **Large Dashboard Decomposition Rules**, **Auto-Refresh Audit**, and **Queries-Per-Run Ratios** extracted from the `google_pso__large_dashboards__query_count` dashboard.

---

## 1. The >25 Query Tile Rule & Anti-Patterns

A dashboard's complexity is measured by its **Total Query Tiles**, which excludes markdown/text headers:

$$ \text{Total Query Tiles} = \text{dashboard\_element.count} - \text{dashboard\_element.count\_text} $$

```
                                DASHBOARD SIZE EVALUATION
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        ▼                                   ▼                                   ▼
[HEALTHY: 1 - 15 TILES]             [WARNING: 16 - 25 TILES]            [CRITICAL: > 25 TILES]
 • Single screen viewport            • Approaches browser memory limit   • Breaches 15 queries/node limit
 • Fast rendering (<3s)              • Potential tile queue contention   • Causes per_user_throttler lag
 • High user engagement              • Action: Implement filters         • Action: Deconstruct dashboard
```

---

## 2. Auto-Refresh Audit (The Silent Resource Drain)

Auto-refreshing dashboard tiles run continuous background queries even when no human is viewing the screen:

| Refresh Interval | Impact Assessment | Recommended Remediation |
| :--- | :--- | :--- |
| **`< 5 Minutes`** | **CRITICAL**: Saturates DB connection pools & drains warehouse budget. | Increase to `> 30 mins` or link to PDT trigger. |
| **`5 - 30 Minutes`**| **HIGH**: Creates regular queue spikes during peak hours. | Align interval with data pipeline load frequency. |
| **`> 30 Minutes`** | **ACCEPTABLE**: Safe for wallboard displays. | Ensure dashboard is marked for TV use only. |

---

## 3. Diagnostic System Activity Queries

### A. Large Dashboards Exceeding 25 Tiles
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "dashboard",
  "fields": [
    "dashboard.id",
    "dashboard.title",
    "dashboard_element.count",
    "dashboard_element.count_text",
    "dashboard_element.count_look",
    "dashboard_element.count_lookless",
    "dashboard_element.count_merge_query"
  ],
  "filters": {
    "dashboard_element.count": ">25",
    "dashboard.moved_to_trash": "No"
  },
  "sorts": ["dashboard_element.count desc"],
  "limit": "50"
}' --verify-ssl=false
```

### B. Auto-Refresh Dashboards & Refresh Frequency
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "dashboard",
  "fields": [
    "dashboard.id",
    "dashboard.title",
    "dashboard_element.refresh_interval_ordered"
  ],
  "filters": {
    "dashboard.moved_to_trash": "No",
    "dashboard_element.refresh_interval_ordered": "NOT NULL"
  },
  "sorts": ["dashboard_element.refresh_interval_ordered asc"],
  "limit": "50"
}' --verify-ssl=false
```

### C. Queries Per Dashboard Run Ratio
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "dashboard_performance",
  "fields": [
    "dashboard.title",
    "history.dashboard_run_count",
    "history.query_run_count_drill",
    "dashboard_history_stats.avg_tile_runtime"
  ],
  "filters": {
    "history.completed_date": "7 days",
    "dashboard.id": "NOT NULL"
  },
  "sorts": ["history.query_run_count_drill desc"],
  "limit": "20"
}' --verify-ssl=false
```

---

## 4. Remediation Workflow for Large Dashboards

1. **Deconstruct into Tabbed Navigation**:
   - Split wide operational dashboards into domain-specific tabs (e.g. Overview, Performance, Regional Details).
2. **Implement Drill Links Instead of Summary + Detail on One Page**:
   - Use `link: { label: "Drill to Detail" url: "/dashboards/..." }` in LookML to open secondary dashboards on click.
3. **Remove Unused Auto-Refresh Intervals**:
   - Turn off auto-refresh unless explicitly configured for live monitoring screens.
