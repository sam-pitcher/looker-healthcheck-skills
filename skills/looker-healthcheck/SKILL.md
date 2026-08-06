---
name: looker-healthcheck
description: >-
  Master developer skill for diagnosing, auditing, and optimizing Looker instance performance and LookML codebases.
  Implements Google PSO (Professional Services Organization) Consolidated Healthcheck benchmarks and automated recipes
  spanning query lifecycle phases: initialization, concurrency/throttling, database execution, post-processing, and dashboard hygiene.
license: Apache-2.0
metadata:
  publisher: google
  version: v1
---

# Looker Healthcheck & Performance Recipes (PSO Framework)

This master developer skill governs the auditing, diagnosis, and systematic optimization of Looker instances and LookML projects. Built upon the architectural benchmarks and diagnostic heuristics established by the **Google Cloud Professional Services Organization (PSO)** in the Consolidated Healthcheck framework, it provides actionable, recipe-based strategies to resolve instance bottlenecks, eliminate query throttles, and accelerate dashboard performance.

All optimizations developed under this skill must be dialect-agnostic, preserve business logic integrity, and enforce performance-by-design standards.

---

## 1. The 3-Phase Query Lifecycle Diagnostic Framework

Every analytical request in Looker moves through three distinct phases. Performance optimization begins by isolating which phase is causing latency:

```
                           THE LOOKER QUERY LIFECYCLE
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                                TOTAL ASYNC RUNTIME                               │
 └──────────────────────────────────────────────────────────────────────────────────┘
            │                                 │                               │
            ▼                                 ▼                               ▼
 ┌──────────────────────┐          ┌──────────────────────┐        ┌──────────────────────┐
 │ 1. INITIALIZATION    │          │ 2. QUERY EXECUTION   │        │ 3. POST-PROCESSING   │
 ├──────────────────────┤          ├──────────────────────┤        ├──────────────────────┤
 │ • project_init       │          │ • acquire_connection │        │ • post_processing    │
 │ • model_init_computed│          │ • queued             │        │ • stream_to_cache    │
 │ • model_init_cache   │          │ • per_user_throttler │        │ • cache_load         │
 │ • explore_init_comput│          │ • execute_main_query │        │ • table calculations │
 │ • marshalled_cache   │          │ • totals_queries     │        │ • pivot formatting   │
 └──────────────────────┘          └──────────────────────┘        └──────────────────────┘
```

---

## 2. PSO Diagnostic Benchmarks & Threshold Matrix

When evaluating `system__activity.query_metrics`, the agent **MUST** compare instance metrics against the following Google PSO performance benchmarks:

| Phase | Metric Name | PSO Benchmark | Warning Threshold | Critical / Action Trigger | Primary Root Cause |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Overall** | `async_processing_average` | `< 5.00s` | `> 10.00s` | `> 15.00s` | High Looker overhead or unoptimized database query |
| **Init** | `project_init` | `< 0.05s` | `> 0.10s` | `> 0.25s` | Monolithic project with too many models/views |
| **Init** | `model_init_computed_average` | `< 2.42s` | `> 2.42s` | `> 5.00s` | Model too large; frequent developer deploys at peak hours |
| **Init** | `model_init_cache_average` | `< 1.00s` | `> 1.00s` | `> 2.00s` | Model bloated with hundreds of unused explores |
| **Init** | `explore_init_average` | `< 0.23s` | `> 0.23s` | `> 0.50s` | Too many complex joins, circular joins, or heavy Liquid |
| **Init** | `marshalled_cache_load_average`| `< 0.35s`| `> 0.35s` | `> 0.75s` | Excessive custom fields or redundant join paths |
| **Init** | `prepare_average` | `< 0.44s` | `> 0.44s` | `> 1.00s` | Complex derived table SQL generation; unmigrated calcs |
| **Exec** | `acquire_connection_average` | `< 0.24s` | `> 0.24s` | `> 0.50s` | Connection pool saturation; Max Connections per Node too low |
| **Exec** | `queued_average` | `0.00s` | `> 0.50s` | `> 1.00s` | Looker worker thread starvation (>25 tile dashboards) |
| **Exec** | `per_user_throttler_average` | `0.00s` | Applied | `> 1.00s` | User exceeded 15 queries/node limit (Merged queries, burst tiles) |
| **Exec** | `execute_main_query_average` | `< 4.87s` | `> 5.00s` | `> 15.00s` | Unindexed database scans; missing PDTs; `SUM_DISTINCT` fanouts |
| **Exec** | `execute_totals_query_average`| `Selective`| Heavy Volume | Significant lag | Grand/Row totals running on high-throughput dashboards |
| **Post** | `postprocessing_average` | `< 0.22s` | `> 0.22s` | `> 0.50s` | Excessive table calculations; heavy pivots; huge row limits |
| **Post** | `stream_to_cache_average` | `< 0.22s` | `> 0.22s` | `> 0.50s` | Browser rendering unconstrained results (>5,000 rows on single values) |
| **Post** | `cache_percent` | `> 50%` | `< 30%` | `< 15%` | Unconfigured datagroups; cache invalidation on every run |

---

## 3. Diagnostic Investigation Workflow

When optimizing an instance or troubleshooting performance complaints, follow this sequential 4-step investigation:

### Step 1: System Activity Introspection
Execute queries against `system__activity.query_metrics` and `history` using `looker-cli` or the Looker API to isolate the bottleneck:
```bash
# Check top outlier queries by async processing runtime
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": ["query.id", "dashboard.title", "query.view", "query_metrics.async_processing_average", "query_metrics.execute_main_query_average"],
  "sorts": ["query_metrics.async_processing_average desc"],
  "limit": "20"
}' --verify-ssl=false
```

### Step 2: Phase Attribution
Calculate the **Indicative Looker Overhead**:
$$\text{Looker Overhead \%} = \frac{\text{Async Processing} - (\text{Execute Main Query} + \text{Acquire Connection})}{\text{Async Processing}} \times 100$$
* If **Looker Overhead > 30%** $\rightarrow$ Execute **Recipe 1, 2, or 4** (Looker-layer / Semantic / Dashboard issue).
* If **Execute Main Query > 70%** $\rightarrow$ Execute **Recipe 3** (Database / PDT / Join Cardinality issue).

---

## 4. The 5 Master Optimization Recipes

---

### Recipe 1: Project & Initialization Optimization (`project_init`, `model_init`, `explore_init`)

#### Target Symptoms:
* `project_init > 0.10s`
* `model_init_computed > 2.42s` or `model_init_cache > 1.00s`
* `explore_init > 0.23s`

#### Root Cause Analysis:
Monolithic project architectures with hundreds of views included indiscriminately via `include: "/*.view"` force Looker to compile all views for every query, invalidating the compiler cache on every developer commit.

#### Optimization Actions:
1. **Model-Level Scoping**: Replace wildcard view inclusions with explicit includes:
   ```lookml
   # ❌ Anti-pattern: Compiles every file in the project
   include: "/views/*.view"

   # ✅ Best Practice: Include only the domain views required for this model
   include: "/views/orders/*.view"
   include: "/views/users/*.view"
   ```
2. **Hub & Spoke Project Architecture**: Break giant multi-department repositories into a Core Hub project (shared database views) and Spoke projects (departmental models) using LookML Project Import (`local_dependency` / `remote_dependency`).
3. **Explore Join Pruning**: Utilize `required_joins` and scoped fields to prevent Looker from instantiating unreferenced join trees.

---

### Recipe 2: Concurrency, Throttling & Connection Pool Optimization (`queued`, `per_user_throttler`, `acquire_connection`)

#### Target Symptoms:
* `per_user_throttler_average > 0s` (queries hit the 15 concurrent queries/node throttle)
* `queued_average > 0.50s` (queries waiting for available thread slots)
* `acquire_connection_average > 0.24s` (database connection wait times)

#### Root Cause Analysis:
Looker enforces a per-user, per-node throttler (maximum 15 concurrent query tasks per user). Dashboards containing >25 tiles, un-staggered schedule deliveries, or merged queries trigger instant throttling storms.

#### Optimization Actions:
1. **Enforce Dashboard Tile Budget (Max 25 Tiles)**:
   - Split bloated dashboards (>25 tiles) into tabbed dashboards or link child dashboards using LookML HTML drill-down links.
2. **Eliminate Merged Queries**:
   - Merged queries execute multiple independent database queries per tile, multiplying query load by 2x-4x.
   - Refactor merged queries into a single native LookML explore with proper `join` relationships.
3. **Stagger Scheduled Content Deliveries**:
   - Identify burst schedules clustered at `:00` or `:30` past the hour.
   - Distribute deliveries across off-peak windows (e.g. `:07`, `:18`, `:42`).
4. **Tune Max Connections per Node**:
   - In Looker Admin $\rightarrow$ Connections, evaluate `Max Connections per Node`. If the database CPU utilization is low (<40%) but `acquire_connection` is high, safely increase the connection limit.

---

### Recipe 3: Database Execution & PDT Acceleration (`execute_main_query`)

#### Target Symptoms:
* `execute_main_query_average > 4.87s` (or outlier queries exceeding 15s)
* High BigQuery bytes scanned / Snowflake warehouse credit burn.
* Compiler injecting `SUM_DISTINCT` / `AVG_DISTINCT`.

#### Root Cause Analysis:
Full table scans, incorrect join cardinalities causing symmetric aggregations, unindexed foreign keys, or complex joins computed on-the-fly.

#### Optimization Actions:
1. **Fix Join Cardinality & Symmetric Aggregations**:
   - Ensure every `join:` declares the exact `relationship:` (`many_to_one`, `one_to_one`, `one_to_many`).
   - Mismatched relationships force Looker to inject expensive `_DISTINCT` hash functions.
2. **Materialize via Partitioned / Clustered PDTs**:
   - For queries with runtime >10s across large tables (>10M rows), build a Persistent Derived Table.
   - **Mandatory**: Define partition keys and clustering/index keys matching the most common dashboard filters:
     ```lookml
     view: customer_order_summary_pdt {
       derived_table: {
         explore_source: order_items {
           column: user_id {}
           column: total_gross_margin {}
           column: order_created_date {}
         }
         datagroup_trigger: ecommerce_daily_datagroup
         partition_keys: ["order_created_date"]
         cluster_keys: ["user_id"]
       }
     }
     ```
3. **Implement Aggregate Awareness**:
   - For high-frequency summary dashboards, add `aggregate_table` definitions to the Explore. Looker will automatically route rollup queries to pre-computed aggregate tables.

---

### Recipe 4: Totals, Table Calculations & Post-Processing Optimization (`stream_to_cache`, `postprocessing`)

#### Target Symptoms:
* `stream_to_cache_average > 0.22s` or `postprocessing_average > 0.22s`
* `execute_totals_query_average` or `execute_grand_totals_query_average` causing query bottlenecks.

#### Root Cause Analysis:
Looker runs separate, parallel SQL queries for grand totals and subtotals. Heavy in-browser table calculations and large unconstrained row limits (e.g., 5,000 rows on single-value KPI cards) exhaust browser memory.

#### Optimization Actions:
1. **Right-size Query Row Limits**:
   - Ensure single-value KPI tiles have `limit: 1` or `limit: 500` instead of the default 5,000.
2. **Migrate Table Calculations to LookML**:
   - Table calculations execute client-side in the browser on unaggregated rows.
   - Convert calculations (e.g., Profit Margin = `(Revenue - Cost) / Revenue`) into native LookML measures:
     ```lookml
     measure: profit_margin {
       type: number
       sql: 1.0 * ${total_profit} / NULLIF(${total_revenue}, 0) ;;
       value_format_name: percent_2
     }
     ```
3. **Audit Totals Usage**:
   - Remove Grand Totals and Row Totals from dashboard tiles where summary rows are not strictly necessary.

---

### Recipe 5: Caching & Datagroup Strategy (`cache_percent`)

#### Target Symptoms:
* `cache_percent < 30%` on high-traffic production instances.
* Repeated identical queries hitting the database warehouse.

#### Root Cause Analysis:
Explores using static `persist_for: "24 hours"` or missing datagroup assignments, causing cache invalidation on arbitrary timers rather than when data actually refreshes.

#### Optimization Actions:
1. **Establish Centralized Datagroups**:
   - Define model-level datagroups triggered by the ETL pipeline:
     ```lookml
     datagroup: warehouse_etl_datagroup {
       sql_trigger_value: SELECT MAX(completed_at) FROM etl_pipeline_log ;;
       max_cache_age: "24 hours"
     }
     ```
2. **Assign Datagroups to Explores**:
   - Ensure every `explore:` block declares `persist_with: warehouse_etl_datagroup`.
3. **Align PDT and Explore Rebuilds**:
   - Share the same datagroup between PDTs and the Explores querying them so data invalidation occurs simultaneously.

---

## 5. Verification & Delta Measurement Protocol

After applying any recipe, the agent **MUST** verify and document the performance delta:

1. **Syntax & Model Validation**:
   ```bash
   looker-cli project validate <project_id> --verify-ssl=false
   ```
2. **Pre vs Post Measurement Matrix**:
   Document the exact before/after metrics:

| Metric | Before Optimization | After Optimization | % Improvement |
| :--- | :---: | :---: | :---: |
| **Async Processing** | `14.2s` | `2.1s` | **-85.2%** |
| **Execute Main Query** | `11.8s` | `1.4s` | **-88.1%** |
| **Per-User Throttling** | `Applied (12 queries)`| `0s (Zero Throttles)` | **100% Fixed** |
| **Cache Hit Rate** | `18%` | `64%` | **+255%** |
