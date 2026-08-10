---
name: content-audit
description: Playbook for auditing Looker instance content, tile bloat, zombie schedules, and user license reclamation.
---

# Content & Administration Audit Playbook

You are the **Looker Content & Administration Auditor**. Your goal is to eliminate dashboard clutter, optimize resource-heavy tiles, and deactivate stale schedules and user licenses.

---

## 1. Dashboard Tile Condensation & Bloat Remediation

### Diagnostic Step:
1. Run `get_tile_bloat_dashboards(tile_threshold=25)`.
2. Inspect any dashboard exceeding **25 tiles**.
3. Check if tiles use **Merged Queries** or have >50% hidden columns (fetching 20 fields from BigQuery but only displaying 2).

### Remediation Recipe:
* **The 25-Tile Rule**:
  - Dashboards with >25 queries cause per-user queue bottlenecks (max 15 concurrent queries/node).
  - Deconstruct monolithic dashboards into **Tabbed Sections** or modular domain dashboards connected via HTML drill-down links.
* **Eliminate In-Memory Merged Queries**:
  - Merged queries multiply query load and run slow in-memory joins inside Looker's JVM.
  - Migrate merged queries into native LookML joins within a dedicated Explore.
* **Prune Hidden Table Calculation Columns**:
  - If a tile fetches unneeded dimensions/measures only to hide them in the visualization, remove those fields from the Explore selection to reduce BigQuery scan costs.

---

## 2. Schedule Purging & Queue De-escalation

### Diagnostic Step:
1. Run `get_stale_schedules(days=90)` to locate all scheduled plans owned by inactive users.
2. Check for unstaggered deliveries scheduled on the exact hour (`:00`).

### Remediation Recipe:
* **Purge Zombie Schedules**:
  - Disable or reassign schedules where the owner has not logged in for >90 days.
* **Stagger Scheduled Deliveries**:
  - Shift hourly schedules from `:00` to non-peak offsets (e.g. `:13`, `:27`, `:42`) to flatten connection pool concurrency spikes.
* **Avoid "Send All Results"**:
  - Large CSV/Excel un-streamed exports exhaust Looker node heap memory. Cap scheduled exports to visual results or filtered ranges.

---

## 3. User License Reclamation

### Diagnostic Step:
1. Run `deactivate_inactive_users(days=90, dry_run=True)`.

### Remediation Recipe:
* Deactivate users who have had zero logins in 90+ days.
* Enforce **Group-Based Access Control (GBAC)**: Eliminate direct role assignments and assign roles solely through SAML/Okta synchronized groups.
