# Looker Healthcheck Delivery Engagement Guide

This document defines the official **End-to-End Healthcheck Engagement Methodology**, stakeholder interview frameworks, thematic review structures, and consultant deliverables structured across the **4 Strategic Pillars**.

```
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                               HEALTHCHECK 4-PILLAR JOURNEY                                  │
 ├──────────────────┬──────────────────┬──────────────────────────┬────────────────────────────┤
 │ PILLAR 1:        │ PILLAR 2:        │ PILLAR 3:                │ PILLAR 4:                  │
 │ Discovery &      │ Diagnostics &    │ Thematic Customer        │ Remediation Roadmap &      │
 │ Walkthrough      │ Auditing         │ Review                   │ Handover                   │
 ├──────────────────┼──────────────────┼──────────────────────────┼────────────────────────────┤
 │ • Stakeholder    │ • System Activity│ • Present Thematic Review│ • Delivery of Clean-Up     │
 │   Discovery      │   Diagnostics    │   Slide Deck (Themes,    │   Spreadsheet              │
 │ • Instance       │ • Henry Pulse &  │   not raw tile dumps)    │ • Transcriber Action Plan  │
 │   Walkthrough    │   Vacuum Scans   │ • Prioritize Top ROI     │ • Style Guide & Testing    │
 │ • Pain Points &  │ • Model Transcri-│   Opportunities with     │   CI/CD Integration        │
 │   Use Patterns   │   ber Scoring    │   Screenshots & Evidence │ • Co-Dev / Handover        │
 └──────────────────┴──────────────────┴──────────────────────────┴────────────────────────────┘
```

---

## 1. Pillar 1: Discovery & Developer Walkthrough

Following the initial kickoff, the consultant conducts an environment walkthrough to assess architecture and developer strategy.

### Stakeholder Discovery Interview Framework
* **Developer Pain Points**: What specific bottlenecks exist during development, validation, or deployment?
* **User Experience Pain Points**: Which dashboards or explores do business users report as painfully slow or confusing?
* **Environment Topology**: Walk through instances (Dev/QA/Prod), projects, models, and key explores.
* **Developer Sync & Collaboration**: What is the process for keeping devs in sync (branching, PRs, code reviews)?
* **Representative Content**: What are the core business entities (orders, users, transactions) that power executive KPIs?
* **Slow Content Inventory**: What specific saved looks or dashboards are known to be slow?
* **User Onboarding & RBAC**: What is the process for adding new users, and how are roles and access controls applied?
* **Strategic Growth**: How is the data team or business expected to evolve in the next 6–12 months?

---

## 2. Pillar 2: Diagnostics & System Activity Auditing

Execute live diagnostic tooling, query profiling, and automated code scans across the environment:

### Core Diagnostic Protocols
1. **Live System Activity Telemetry**:
   * Query `system__activity.query_metrics` to benchmark Query Lifecycles, Looker Overhead %, Cache Hit %, and Connection Pool limits against target thresholds.
2. **Forensic Outlier Drill-Downs**:
   * Query `system__activity.query_metrics` and `history` to isolate the top slowest database queries, congested scheduler queues, and massive dashboards (>25 tiles).
3. **Model Bloat & Inactive Code Scans**:
   * Run Henry Pulse (`henry pulse --timeframe=90`) and Henry Vacuum (`henry vacuum --model=<model>`) to catalog 0-query Explores, Views, and Fields.
4. **LookML Syntax & Modern Runtime Audit**:
   * Run LookML compilation and validation via `looker-cli project validate <project_id>` to locate missing `primary_key: yes` declarations and deprecated syntax.

---

## 3. Pillar 3: Thematic Customer Review

Consultant review deliverables must **not be organized by raw tile**, but by **theme**:

### Performance Theme 1: Computational Efficiency
1. **Caching Policy (50% Target Benchmark)**:
   * Record `% Results from Cache`. If `< 50%`, sync Looker caching with warehouse ETL pipelines using named **Datagroups**.
   * Define datagroups in a dedicated shared config file and `include:` across models.
   * Ensure every user-facing explore has an assigned `persist_with:` datagroup.
2. **Query Latencies (< 10s Target Benchmark)**:
   * Target: Majority of user-issued queries must complete in `< 10 seconds`.
   * Prioritize high-usage explores that exhibit long runtimes (weighted by usage volume $\times$ latency).
3. **PDT Concurrency & Build Patterns**:
   * Inspect hourly PDT builds by connection. Note that PDTs build sequentially per connection and cause queue bottlenecks.
   * If PDTs rebuild hourly, verify if source ETL updates hourly. If not, switch to event-based datagroups (`sql_trigger_value`).
   * For very long-running PDTs, recommend moving logic upstream into warehouse ETL or partitioning tables.

### Performance Theme 2: Operational & Instance Load
1. **Hourly Schedules**:
   * Stagger scheduled deliveries away from top-of-the-hour (:00) spikes.
   * Disable **"Send All Results"** on massive un-paged queries to prevent Looker JVM memory exhaustion.
   * Keep concurrent PDF renders to a minimum.
2. **Dashboard Auto-Refresh**:
   * Never set auto-refresh intervals shorter than the ETL pipeline update frequency.
   * If a dashboard is displayed on a TV/trading desk, clone the dashboard for the screen and leave the interactive version without auto-refresh.
3. **The >25 Query Tile Rule**:
   * Recommend maximum 25 query tiles per dashboard.
   * Decouple large dashboards using tabs or **Custom HTML Drilling Links** (`link: { label: "Drill" url: "..." }`) to preserve filter context.

### Model Quality Theme: Transcriber 0–4 Scoring Rubric
Evaluate model quality across 4 focus areas (**LookML, Customer Success, Architecture, Data Culture**) using the **0 to 4 Transcriber Grading Rubric**:

```
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                           TRANSCRIBER 0–4 GRADING RUBRIC                                    │
 ├────┬────────────────────┬───────────────────────────────────────────────────────────────────┤
 │ 0  │ Unsatisfactory     │ Instance actively violates standard (e.g. raw autogenerated views)│
 │ 1  │ Needs Improvement  │ A few isolated instances of best practice, but mostly un-managed  │
 │ 2  │ Meets Expectations │ Average customer: Follows best practice 90% of the time           │
 │ 3  │ Exceeds            │ Organized with developer intent, clean comments, field grouping   │
 │ 4  │ Exceptional        │ Innovative use (e.g. dynamic sets per use case, full DRY modeling)│
 │ └────┴────────────────────┴───────────────────────────────────────────────────────────────────┘
```

---

## 4. Pillar 4: Remediation Roadmap & Handover

Deliver prioritized, concrete, and actionable improvements for the customer's engineering team:

### 1. Instance Clean-Up & Bloat Pruning
* Deliver the **Instance Clean-Up Spreadsheet** documenting 90-day unused Explores, Views, and Looks.
* **Pruning Safeguards**:
  * Never delete foreign keys / join keys (hide them with `hidden: yes` instead).
  * Protect fact table measure dependencies (`sales_amount` dimension must remain hidden if `total_sales_amount` depends on it).
  * Run LookML Validator and Content Validator before merging PRs.

### 2. Development Workflows Maturity Roadmap (The 3-Tier Framework)
```
 Tier 1: Pull Request Review Process
 ├── Level a: PRs required (anyone can approve)
 └── Level b: Formalized review process (at least 1 designated senior reviewer approval required)

 Tier 2: Testing Framework Layered into PRs
 ├── Level a: LookML Data Tests (`test:`) and Content Validator checks required for PR approval
 └── Level b: CI/CD automated pipeline integrated in GitHub Actions / GitLab CI

 Tier 3: Multi-Stage Promotion Topology
 ├── Level a: Dedicated Dev Instance -> Production Instance
 └── Level b: Dev Instance -> QA Instance -> Production Instance (Enterprise SLA / Embedded)
```

### 3. Security & Access Governance (GBAC)
* Enforce **Group-Based Access Control (GBAC)**: Users must inherit roles through Groups, not directly assigned.
* Eliminate orphaned groups, roles, and duplicate model/permission sets.

### 4. Advanced Architecture & Aggregate Awareness
* Implement `aggregate_table:` within top high-volume explores to deliver pre-aggregated speed while preserving granular drillability.
