# Content Delivery & Schedule Optimization Framework (Deep-Dive)

This reference document defines the diagnostic protocols, failure pattern matching, and zombie schedule cleanup procedures extracted from the `google_pso__content_delivery` dashboard.

---

## 1. Core Scheduling Failure Patterns & Root Causes

```
                                  SCHEDULED DELIVERY BOTTLENECK
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ▼                                    ▼                                    ▼
[ZOMBIE SCHEDULES]                   [BROKEN CONTENT DELIVERY]            [TIMEOUTS & CONGESTION]
Inactive Users (>90 days login)      Fatal LookML/Content Errors          Warehouse / Concurrency Limits
 • Former employees running daily     • "The view for this Look not found" • "Query execution timeout"
 • Scheduled jobs never cancelled     • "User cannot run Dashboard"        • "Enqueue for execute" queue lag
 • Wasting DB compute & licenses      • "Not authorized to run plan"       • Top-of-the-hour pileups (:00)
```

---

## 2. Diagnostic Protocols & Queries

### A. Inactive Users with Active Schedules (Zombie Schedules)
Finds active users who have not logged into Looker for over 90 days but are still triggering recurring background deliveries:
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "user",
  "fields": [
    "user.name",
    "user_facts.last_ui_login_date",
    "history.most_recent_query_date",
    "scheduled_job.count"
  ],
  "filters": {
    "user_facts.last_ui_login_date": "before 90 days ago",
    "user.is_disabled": "No",
    "scheduled_job.count": ">0"
  },
  "sorts": ["scheduled_job.count desc"],
  "limit": "100"
}' --verify-ssl=false
```

### B. Schedules to Delete (Fatal Broken Schedules)
Identifies recurring scheduled jobs that continuously fail due to missing views, deleted Looks, or permissions:
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "scheduled_plan",
  "fields": [
    "scheduled_plan.id",
    "scheduled_job.status",
    "user.name",
    "scheduled_job.status_detail",
    "scheduled_plan_destination.type",
    "scheduled_plan_destination.format"
  ],
  "filters": {
    "scheduled_job.status_detail": "%An API error occurred%,%User missing permission to send to specified destination%,%Not authorized to run scheduled plan%,%The view for this Look cannot be found%,%User cannot run Look%,%User cannot run Dashboard%"
  },
  "sorts": ["scheduled_plan.id desc"],
  "limit": "100"
}' --verify-ssl=false
```

### C. Schedules with Connection Timeouts
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "scheduled_plan",
  "fields": [
    "scheduled_job.created_time",
    "scheduled_job.finalized_time",
    "scheduled_plan.id",
    "user.name",
    "scheduled_job.status_detail",
    "scheduled_job_stage.stage"
  ],
  "filters": {
    "scheduled_job.status_detail": "%timeout%"
  },
  "sorts": ["scheduled_job.created_time desc"],
  "limit": "50"
}' --verify-ssl=false
```

### D. Hourly Queue Congestion Heatmap (`enqueue_for_execute`)
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "scheduled_plan",
  "fields": [
    "scheduled_job_stage.started_hour_of_day",
    "scheduled_job_stage.started_day_of_week",
    "scheduled_job_stage.avg_runtime",
    "scheduled_job.count"
  ],
  "filters": {
    "scheduled_job_stage.stage": "enqueue_for_execute"
  },
  "limit": "500"
}' --verify-ssl=false
```

---

## 3. Remediation Best Practices

1. **Delete Dead Schedules**:
   - Immediately delete schedules referencing non-existent Looks/Views or unauthorized users.
2. **Reassign or Disable Zombie Schedules**:
   - Disable or reassign schedules owned by inactive users (`>90 days` since last login).
3. **Decongest Top-of-the-Hour Schedules**:
   - Stagger cron schedules across the hour (e.g. `12 * * * *` or `37 * * * *` instead of `00 * * * *`).
4. **Avoid "Send All Results" for Heavy Dashboards**:
   - For large datasets, send a summary dashboard with a direct link, or write a dedicated ETL/PDT export rather than unthrottled scheduled PDF/CSV dumps.
