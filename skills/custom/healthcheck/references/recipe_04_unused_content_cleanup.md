# Recipe 04: Identification of Unused Content & LookML Bloat (Component 4)

## 1. Objective & Purpose
Eliminate model bloat, recover compute capacity, and protect instance throughput by identifying and safely decommissioning:
1. **Unused Dashboards & Looks** (Zero user views in past 90 days).
2. **Unused Explores** (Zero query runs across all models in past 90 days).
3. **Dead LookML Dimensions & Measures** (Zero query references in past 90 days via Henry CLI).
4. **Zombie Schedules** (Active scheduled deliveries owned by users inactive or disabled for >90 days).
5. **Fatal Schedules** (Recurring scheduled jobs failing on deleted views/looks or unauthorized access).

```
                     CONTENT LIFECYCLE & DEPRECATION FUNNEL
 ┌───────────────────────────┬───────────────────────────┬───────────────────────────┐
 │ Stage 1: Identification   │ Stage 2: Soft Deprecation │ Stage 3: Permanent Purge  │
 ├───────────────────────────┼───────────────────────────┼───────────────────────────┤
 │ • 90-day System Activity  │ • Move Dashboards to Trash│ • Hard delete after 30d   │
 │ • Henry Vacuum Dead Code  │ • Mark Explores hidden:yes│ • Remove LookML fields    │
 │ • Fatal Schedule Log Scans│ • Disable Zombie Schedules│ • Reassign owner to SvcAcct│
 └───────────────────────────┴───────────────────────────┴───────────────────────────┘
```

---

## 2. Diagnostic System Activity Queries

### Step 1: Unused Dashboards (0 Views in > 90 Days)
```json
{
  "model": "system__activity",
  "view": "dashboard",
  "fields": [
    "dashboard.id",
    "dashboard.title",
    "dashboard.created_time",
    "user.name",
    "history.most_recent_run_at_date",
    "history.query_run_count"
  ],
  "filters": {
    "dashboard.moved_to_trash": "No",
    "history.most_recent_run_at_date": "before 90 days ago"
  },
  "sorts": ["history.query_run_count desc"],
  "limit": "50"
}
```

### Step 2: Unused Explores (0 Queries in > 90 Days)
```json
{
  "model": "system__activity",
  "view": "history",
  "fields": [
    "query.model",
    "query.view",
    "history.query_run_count",
    "history.most_recent_run_at_date"
  ],
  "filters": {
    "history.most_recent_run_at_date": "before 90 days ago",
    "query.model": "-NULL"
  },
  "sorts": ["history.query_run_count asc"],
  "limit": "50"
}
```

### Step 3: Zombie Schedules (Inactive Owners > 90 Days)
```json
{
  "model": "system__activity",
  "view": "user",
  "fields": [
    "user.id",
    "user.name",
    "user_facts.last_ui_login_date",
    "scheduled_plan.count",
    "scheduled_plan.name"
  ],
  "filters": {
    "user_facts.last_ui_login_date": "before 90 days ago",
    "user.is_disabled": "No",
    "scheduled_plan.count": ">0"
  },
  "limit": "50"
}
```

### Step 4: Fatal Failing Schedules (Broken Queries & Permissions)
```json
{
  "model": "system__activity",
  "view": "scheduled_plan",
  "fields": [
    "scheduled_plan.id",
    "scheduled_plan.name",
    "scheduled_job.status",
    "scheduled_job.status_detail",
    "user.name"
  ],
  "filters": {
    "scheduled_job.status": "failure",
    "scheduled_job.status_detail": "%An API error occurred%,%User missing permission%,%Not authorized%,%view for this Look cannot be found%,%User cannot run Look%,%User cannot run Dashboard%"
  },
  "sorts": ["scheduled_plan.id desc"],
  "limit": "50"
}
```

---

## 3. Henry CLI Dead Field Vacuuming

Use the open-source **Henry** CLI to scan the LookML codebase against System Activity history:

```bash
# 1. Run Henry Pulse for broad health overview
henry pulse --timeframe=90

# 2. Run Henry Vacuum on a specific model to find unused fields
henry vacuum --model=<model_name> --timeframe=90

# 3. Scan a specific explore
henry vacuum --model=<model_name> --explore=<explore_name> --timeframe=90
```

---

## 4. The 3-Step Clean-Up & Governance Workflow

### Step 1: Deprecate Dashboards & Looks (30-Day Trash Holding)
1. Export a list of all dashboards with 0 runs in >90 days.
2. Communicate with dashboard creators (or department leads) giving a 14-day notice.
3. Move candidate dashboards to **Trash** (soft delete). Looker holds trashed content for 30 days before permanent deletion, allowing easy restoration if needed.

### Step 2: Hide Unused Explores Before Deletion
Do **not** delete explore files immediately, as external reports or scheduled jobs might depend on them.
1. Add `hidden: yes` to the explore definition in the `.model.lkml` or `.explore.lkml` file.
2. Monitor System Activity for 30 days. If zero queries are logged, remove the explore block entirely.

### Step 3: Prune Unused LookML Fields
When Henry flags dozens of unused dimensions:
1. Do not delete raw database columns from `.view.lkml` if they might be needed for joins.
2. Add `hidden: yes` to unqueried foreign keys and technical IDs.
3. Prune exposed fields at the explore level using the `fields:` parameter:
   ```lookml
   explore: transactions {
     # Expose all base view fields except internal technical IDs
     fields: [ALL_FIELDS*, -transactions.internal_batch_id, -transactions.etl_checksum]
   }
   ```

### Step 4: Remediate Broken & Zombie Schedules
1. **Delete Fatal Schedules**: Immediately delete all scheduled jobs failing with "view not found" or "permission error".
2. **Reassign Zombie Schedules**: Transfer business-critical recurring exports owned by departed employees to dedicated Looker Service Accounts (e.g. `looker-automation@company.com`).
