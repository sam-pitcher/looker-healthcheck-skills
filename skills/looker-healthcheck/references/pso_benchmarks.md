# Google PSO Consolidated Healthcheck Benchmarks Reference

This document provides the complete reference of metrics, calculation expressions, notes, and benchmark thresholds derived from the **Google PSO Consolidated Healthcheck Dashboard**.

---

## 1. High-Level Performance Metrics

### Async Processing Time (`async_processing`)
* **Definition**: The total amount of time a query takes to complete, inclusive of pre-query processing, main query execution, totals execution, and post-query processing.
* **PSO Benchmark**: `< 5.0s`
* **Warning**: `> 10.0s` (Orange)
* **Critical**: `> 15.0s` (Red)

### Indicative Looker Overhead
* **Definition**: The percentage and duration of time a query spends being processed exclusively within Looker (pre and post-processing) versus waiting for the database.
* **Calculation**:
  $$\text{Looker Overhead Time} = \text{Async Processing} - (\text{Execute Main Query} + \text{Acquire Connection})$$
  $$\text{Looker Overhead \%} = \frac{\text{Looker Overhead Time}}{\text{Async Processing}} \times 100$$
* **Benchmark**: `< 20%`
* **Warning**: `> 30%` (Indicates heavy in-Looker computations, table calcs, unindexed models, or large row payloads).

### Cache Percentage (`cache_percent`)
* **Definition**: The percentage of queries served directly from Looker's cache rather than querying the database.
* **Calculation**:
  $$\text{Cache \%} = 1 - \left(\frac{\text{database\_result\_query\_count}}{\text{query\_run\_count}}\right)$$
* **Benchmark**: `> 50%` for standard reporting / dashboards.

---

## 2. Initialization Phase Benchmarks

| Metric | Benchmark | Description & Tuning Actions |
| :--- | :---: | :--- |
| **`project_init`** | `< 0.10s` | Time taken to initialize the project from code. If high, break project out into smaller components using a Hub & Spoke architecture. |
| **`model_init_computed`** | `< 2.42s` | Time taken to compile and validate the model from raw code. If high, break models out into smaller scoped domain files and establish scheduled deployment windows during off-peak hours. |
| **`model_init_cache`** | `< 1.00s` | Time taken to validate model from cache. Should execute in under 1 second. |
| **`explore_init`** | `< 0.23s` | Time taken to compile explore definitions from code. If high, optimize joins, remove unused fields, and reduce compiler complexity. |
| **`marshalled_cache_load`** | `< 0.35s` | Time taken to validate explore code from cache. If high, prune joins and move custom dimensions to native LookML. |
| **`prepare`** | `< 0.44s` | Time taken to prepare the final SQL statement from LookML. If high, migrate complex calculations back to the database or into PDTs. |

---

## 3. Query Execution Phase Benchmarks

| Metric | Benchmark | Description & Tuning Actions |
| :--- | :---: | :--- |
| **`acquire_connection`** | `< 0.24s` | Time taken to obtain a connection from Looker's connection pool to the database. If high, review `Max Connections per Node` in Looker Admin $\rightarrow$ Connections. |
| **`queued`** | `0.00s` | Time a query spends waiting for a free Looker worker thread. If high, reduce >25 tile dashboards and eliminate merged queries. |
| **`per_user_throttler`** | `0.00s` | Looker throttles each user to a maximum of 15 queries per node concurrently. If applied, disperse burst schedules and refactor large dashboards. |
| **`execute_main_query`** | `< 4.87s` | Main query runtime inside the database warehouse. Optimize via table indexing, partitioning, clustering, and PDT pre-aggregation. |
| **`execute_totals_query`** | `Selective` | Looker executes separate queries for subtotals. Disable totals on high-throughput tiles. |
| **`execute_grand_totals_query`** | `Selective` | Looker executes separate queries for grand totals. Review necessity on dashboard tiles. |

---

## 4. Post-Processing Phase Benchmarks

| Metric | Benchmark | Description & Tuning Actions |
| :--- | :---: | :--- |
| **`stream_to_cache`** | `< 0.22s` | Time taken to format and stream results to browser cache. If high, audit table calculations, heavy pivots, and reduce row limits. |
| **`post_processing`** | `< 0.22s` | Looker post-processing time. Convert table calculations to LookML measures. |
| **`load_process_and_stream_main_query`** | `< 0.24s` | Streamed query time. Ensure query row limits match visualization needs. |
| **`load_main_query_in_memory`** | `< 0.24s` | Non-streamed query time to buffer results into memory. |
| **`cache_load`** | `< 0.24s` | Time taken to retrieve results from the result set cache. |
