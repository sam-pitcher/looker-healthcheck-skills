---
name: bq-jobs-diagnostics
description: Audit BigQuery warehouse performance, slot saturation timelines, query cost outliers, stage spills, and table partitioning/clustering alignment using the bq CLI and INFORMATION_SCHEMA.
---

# ⚡ BigQuery Jobs Diagnostics Skill

This skill guides an agent or engineer to audit BigQuery query workloads, diagnose slot contention, identify unpartitioned table scans, and evaluate cost outliers using the standard Google Cloud `bq` CLI and `INFORMATION_SCHEMA`.

---

## 🧭 When to Use This Skill

Activate this skill when:
* Auditing BigQuery slot saturation, reservation limits, or query queueing
* Detecting large unpartitioned or unclustered full table scans from Looker
* Investigating query stage memory spills to disk and expensive shuffle operations
* Evaluating opportunities for LookML Aggregate Awareness rollups


* Uses Google Cloud Application Default Credentials (ADC) or active gcloud session (`gcloud auth login`).
* **Required IAM Roles**:
  - `roles/bigquery.jobUser` (run diagnostic queries)
  - `roles/bigquery.metadataViewer` or `roles/bigquery.dataViewer` (inspect schema & `INFORMATION_SCHEMA`)
* Standard execution command:
  ```bash
  bq query --use_legacy_sql=false --format=prettyjson "<SQL>"
  ```
  Or use the helper wrapper:
  ```bash
  bash skills/bq-jobs-diagnostics/scripts/run_bq_query.sh "<SQL>"
  ```

---

## 📋 4-Step BigQuery Diagnostic Protocol

### Step 1: Slot Contention & Saturation Timelines
Query `region-us.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT` to determine if Looker queries suffered from slot starvation or queueing:
```sql
SELECT
  period_start,
  period_slot_ms / 1000 AS avg_slots_consumed,
  period_shuffle_ram_usage_ratio,
  period_estimated_runnable_units AS queued_units
FROM `region-us.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT`
WHERE period_start >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND job_type = "QUERY"
ORDER BY avg_slots_consumed DESC
LIMIT 20;
```
* **Target SLA**: Queued units = 0. If `queued_units > 0`, queries were throttled due to slot starvation.
* Consult concept: [`bundle/bigquery_compute/computations/slot_consumption_timeline.md`](../../bundle/bigquery_compute/computations/slot_consumption_timeline.md)

### Step 2: Table Partitioning & Clustering Alignment
Query `INFORMATION_SCHEMA.TABLE_STORAGE` and `INFORMATION_SCHEMA.COLUMNS` to find fact tables over 10M rows lacking partitioning or clustering:
```sql
SELECT
  project_id,
  table_schema AS dataset_id,
  table_name,
  total_rows,
  total_logical_bytes / POW(1024, 3) AS size_gb
FROM `region-us.INFORMATION_SCHEMA.TABLE_STORAGE`
WHERE total_rows > 10000000
ORDER BY total_logical_bytes DESC
LIMIT 15;
```
* **Rule**: Any fact table with >10M rows MUST be partitioned by date/timestamp and clustered by high-cardinality filter columns.
* Consult concept: [`bundle/bigquery_compute/computations/table_partition_ddl.md`](../../bundle/bigquery_compute/computations/table_partition_ddl.md)

### Step 3: Query Costs & Bytes Billed Outliers
Inspect `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT` for expensive runaway queries:
```sql
SELECT
  job_id,
  user_email,
  total_bytes_billed / POW(1024, 4) AS tb_billed,
  (total_bytes_billed / POW(1024, 4)) * 6.25 AS estimated_cost_usd,
  total_slot_ms / 1000 AS slot_seconds,
  query
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND end_time IS NOT NULL
ORDER BY total_bytes_billed DESC
LIMIT 10;
```
* Consult concept: [`bundle/bigquery_compute/computations/bytes_billed_by_model.md`](../../bundle/bigquery_compute/computations/bytes_billed_by_model.md)

### Step 4: Aggregate Awareness Candidates
Identify queries scanning billions of rows for summary metrics (e.g. daily sales, active users). Recommend LookML `aggregate_table` rollups to eliminate repeat raw table scans.
* Consult concept: [`bundle/bigquery_compute/references/aggregate_awareness_and_architecture.md`](../../bundle/bigquery_compute/references/aggregate_awareness_and_architecture.md)

---

## 📚 Related OKF Knowledge Assets

* [Warehouse Optimization Guide](../../bundle/bigquery_compute/references/warehouse_optimization.md)
* [BI Engine Optimization](../../bundle/bigquery_compute/references/bi_engine_optimization.md)
* [Scoring Rubric: BigQuery Compute](../../bundle/bigquery_compute/playbooks/scoring_bigquery_compute.md)
