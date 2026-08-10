# Benchmark Standards & Query Lifecycle Playbook

This reference document contains the official **Performance Benchmarks**, **Query Lifecycle Definitions**, **Warning Thresholds**, and **Architectural Guidance Notes** extracted from historical health check dashboards.

---

## 1. Complete Query Lifecycle Metrics & Guidance

### Phase 1: Initialization Phase

#### `project_init` (Benchmark: < 0.10s | Target: < 0.05s)
* **Definition**: The time taken to initialize the LookML project schema.
* **Architectural Guidance**: Project Init should execute in under 0.10 seconds. If higher, the LookML project has become monolithic with too many view files and dependencies.
* **Remediation Recipe**: Refactor into a **Hub and Spoke** architecture, where shared core dimensions live in a central repository and domain-specific models live in separate spoke projects.

#### `model_init_computed` (Benchmark: < 2.42s | Warning: > 2.44s)
* **Definition**: The average time taken to compile and validate models directly from LookML code (on cache miss or first load).
* **Architectural Guidance**: Should only impact a small fraction of queries. If high, break large models out into smaller, domain-specific `.model.lkml` files.
* **Remediation Recipe**: Break monolithic models containing dozens of explores into targeted model files. Implement deployment windows to avoid cache invalidations during peak business hours.

#### `model_init_cache` (Benchmark: < 0.50s | Warning: > 1.00s)
* **Definition**: The average time taken to validate model definitions from memory cache.
* **Architectural Guidance**: Should impact the vast majority of queries and return in under 1.00 second. If elevated, model schemas are too complex and need scoping.

#### `explore_init` (Benchmark: < 0.233s | Warning: > 0.233s)
* **Definition**: The average time taken to initialize and compile an Explore from LookML code.
* **Architectural Guidance**: If high, review explores for join efficiency, remove unnecessary joined views, prune unused dimensions/measures, and restrict developer production deployment frequency during peak hours.

#### `marshalled_cache_load` (Explore Init: Cache) (Benchmark: < 0.351s | Warning: > 0.351s)
* **Definition**: Time taken to validate and load cached Explore schemas from disk/memory.
* **Architectural Guidance**: Should execute under 0.351s. If elevated, simplify explore joins and move ad-hoc custom fields into LookML.

#### `prepare` (Benchmark: < 0.20s | Warning: > 0.439s)
* **Definition**: The amount of time Looker takes to generate the SQL query following LookML validation.
* **Architectural Guidance**: If excessively high, review complex Liquid logic, replace dynamic derived tables with Persistent Derived Tables (PDTs), migrate calculations back to warehouse SQL, and enable the latest LookML runtime compiler.

---

### Phase 2: Query Execution Phase

#### `acquire_connection` (Benchmark: < 0.238s | Warning: > 0.238s)
* **Definition**: Time for Looker to obtain an active database connection from the connection pool (including credential lookup and pool instantiation).
* **Architectural Guidance**: If elevated or impacting a large number of queries, Looker is sending more concurrent queries than the warehouse connection pool allows.
* **Remediation Recipe**: Increase **Max Connections per Node** in Looker Connection Settings, or reduce concurrency spikes by staggering scheduled deliveries.

#### `queued` (Benchmark: 0.00s | Warning: > 0.10s)
* **Definition**: Time a query sits waiting for an available Looker worker thread.
* **Architectural Guidance**: Looker worker pool exhausted. Review connections per node, enforce the **25-tile dashboard budget**, and optimize slow database queries to increase throughput.

#### `per_user_throttler` (Benchmark: 0.00s | Cap: 15 queries/node)
* **Definition**: Time spent queued by Looker's built-in 15 concurrent queries/user limit.
* **Architectural Guidance**: Triggered by dashboards with >25 tiles, merged queries (which multiply queries per tile), and unstaggered cron deliveries.
* **Remediation Recipe**: Stagger scheduled deliveries away from top-of-the-hour (:00), deconstruct large dashboards into tabs, and replace merged queries with native LookML explores.

#### `execute_main_query` (Benchmark: < 4.87s | Warning: > 5.00s | Critical: > 15.00s)
* **Definition**: Pure warehouse database query execution runtime.
* **Architectural Guidance**: Optimize via Aggregate Awareness tables, BigQuery partition/cluster pruning, indexing, removing unneeded subqueries, and templated filters in derived tables.

#### Totals Queries (`execute_totals_query`, `execute_row_totals_query`, `execute_grand_totals_query`) (Benchmark: < 0.238s)
* **Definition**: Separate database queries executed by Looker to calculate subtotals and grand totals.
* **Architectural Guidance**: Totals queries run separately from the main query. Disable totals on high-throughput dashboards unless strictly required.

---

### Phase 3: Post-Query Execution Phase

#### `stream_to_cache` & `postprocessing` (Benchmark: < 0.223s | Warning: > 0.223s)
* **Definition**: Time taken to format, apply table calculations/pivots, and stream results to browser cache.
* **Architectural Guidance**: If high, review row limits (avoid 5,000-row limits on single-value KPI cards), remove excessive UI table calculations, and replace merged queries.

#### In-Memory Loading (`load_process_and_stream_main_query` vs `load_main_query_in_memory`) (Benchmark: < 0.238s)
* **Streamed Queries** (`load_process_and_stream_main_query`): Fast, direct HTTP streaming to client.
* **Non-Streamed Queries** (`load_main_query_in_memory`): Loads entire result set into Looker instance RAM (triggered by totals, merged queries, or certain visualization types). Must remain under 0.238s.

#### `cache_load` (Benchmark: < 0.238s)
* **Definition**: Time taken to retrieve raw result sets from Looker's cache on cache hit.

---

## 2. Summary Benchmark Matrix

| Lifecycle Stage | Metric Field | Target Benchmark | Warning Threshold | Critical Threshold |
| :--- | :--- | :---: | :---: | :---: |
| **Async Processing** | `async_processing_average` | **`< 5.00s`** | `> 9.999s` | `> 14.999s` |
| **Looker Overhead** | `(Async - (Main + Conn)) / Async` | **`< 20.0%`** | `> 30.0%` | `> 50.0%` |
| **Cache Hit Ratio** | `1 - (DB_Runs / Total_Runs)` | **`> 50.0%`** | `< 40.0%` | `< 20.0%` |
| **Project Init** | `project_init` | **`< 0.05s`** | `> 0.100s` | `> 0.250s` |
| **Model Init (Compute)** | `model_init_computed` | **`< 2.42s`** | `> 2.440s` | `> 5.000s` |
| **Model Init (Cache)** | `model_init_cache` | **`< 0.50s`** | `> 1.000s` | `> 2.500s` |
| **Explore Init (Compute)**| `explore_init` | **`< 0.233s`** | `> 0.233s` | `> 0.500s` |
| **Explore Init (Cache)** | `marshalled_cache_load` | **`< 0.351s`** | `> 0.351s` | `> 0.750s` |
| **SQL Prepare** | `prepare` | **`< 0.20s`** | `> 0.439s` | `> 1.000s` |
| **Acquire Connection** | `acquire_connection` | **`< 0.238s`** | `> 0.238s` | `> 0.500s` |
| **Worker Queue Time** | `queued` | **`0.00s`** | `> 0.100s` | `> 0.500s` |
| **Per-User Throttle** | `per_user_throttler` | **`0.00s`** | `> 0.000s` | `> 1.000s` |
| **Main Query Exec** | `execute_main_query` | **`< 4.87s`** | `> 5.000s` | `> 15.000s` |
| **Stream to Cache** | `stream_to_cache` | **`< 0.223s`** | `> 0.223s` | `> 0.500s` |
| **Post-Processing** | `postprocessing` | **`< 0.223s`** | `> 0.223s` | `> 0.500s` |
| **In-Memory Loading** | `load_main_query_in_memory` | **`< 0.10s`** | `> 0.238s` | `> 0.500s` |
| **Totals Query Exec** | `execute_totals_query` | **`< 0.238s`** | `> 0.500s` | `> 1.500s` |
