# Recipe 04: Identification of Unused Content & LookML Bloat (Component 4)

## 1. Objective & Purpose
Eliminate model bloat, free up compute capacity, and protect instance throughput by identifying:
1. **Unused Dashboards & Looks** (Zero user views in past 90 days).
2. **Unused Explores** (Zero query runs in past 90 days).
3. **Zombie Schedules** (Active scheduled deliveries owned by users inactive for >90 days).
4. **Fatal Schedules to Delete** (Recurring scheduled jobs failing on deleted views/looks or unauthorized access).
5. **Legacy Features** still active on the instance.

---

## 2. Diagnostic Execution Protocols

### Step 1: Unused Dashboards (Past 90 Days)
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity", "view": "dashboard",
  "fields": [
    "dashboard.id", "dashboard.title", "dashboard.created_time",
    "user.name", "history.query_run_count"
  ],
  "filters": {
    "dashboard.moved_to_trash": "No",
    "history.most_recent_run_at_date": "before 90 days ago"
  },
  "limit": "50"
}' --verify-ssl=false
```

### Step 2: Unused Explores (Past 90 Days)
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity", "view": "history",
  "fields": [
    "query.model", "query.view", "history.query_run_count", "history.most_recent_run_at_date"
  ],
  "filters": {
    "history.most_recent_run_at_date": "before 90 days ago",
    "query.model": "-NULL"
  },
  "limit": "50"
}' --verify-ssl=false
```

### Step 3: Zombie Schedules (Inactive Users > 90 Days)
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity", "view": "user",
  "fields": [
    "user.name", "user_facts.last_ui_login_date",
    "history.most_recent_query_date", "scheduled_job.count"
  ],
  "filters": {
    "user_facts.last_ui_login_date": "before 90 days ago",
    "user.is_disabled": "No",
    "scheduled_job.count": ">0"
  },
  "limit": "50"
}' --verify-ssl=false
```

### Step 4: Fatal Schedules to Delete (Broken Content)
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity", "view": "scheduled_plan",
  "fields": [
    "scheduled_plan.id", "scheduled_job.status", "user.name",
    "scheduled_job.status_detail"
  ],
  "filters": {
    "scheduled_job.status_detail": "%An API error occurred%,%User missing permission%,%Not authorized%,%view for this Look cannot be found%,%User cannot run Look%,%User cannot run Dashboard%"
  },
  "limit": "50"
}' --verify-ssl=false
```

---

## 3. Cleanup & Deprecation Workflow

1. **Delete Dead Schedules**:
   - Delete scheduled jobs whose status details show missing views or unauthorized users.
2. **Reclaim Zombie Schedules**:
   - Reassign business-critical schedules owned by departed users to service accounts, and cancel unneeded ones.
3. **Hide Before Deleting Explores**:
   - Mark unused explores with `hidden: yes` first.
4. **Soft-Delete Stale Dashboards**:
   - Move 90-day unused dashboards to Trash.
