---
type: Attested Computation
title: BigQuery Query Cost & Bytes Billed Audit
description: Sanctioned BigQuery SQL query to compute total gigabytes billed and dollar costs grouped by user and job.
status: stable
runtime: bigquery
parameters:
  - name: hours
    type: integer
    required: false
  - name: cost_per_tb
    type: float
    required: false
executor: { resource: agent/tools/bq_client.py, receipt: "['job_id', 'executed_sql', 'total_gb_billed', 'estimated_cost_usd']" }
attester: { resource: evals/test_tools.py }
generated: { by: looker_healthcheck_agent/v0.2, at: "2026-08-20T12:00:00Z" }
verified: { by: "human:sampitcher", at: "2026-08-20T14:00:00Z" }
sources:
  - id: bq-jobs-by-project
    resource: region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    title: BigQuery Jobs by Project
---

# Computation

```sql
SELECT
  user_email,
  COUNT(1) as total_queries,
  ROUND(SUM(total_bytes_billed) / POW(1024, 3), 2) as total_gb_billed,
  ROUND((SUM(total_bytes_billed) / POW(1024, 4)) * 6.25, 2) as estimated_cost_usd
FROM
  `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND job_type = 'QUERY'
GROUP BY 1
ORDER BY total_gb_billed DESC
LIMIT 20;
```

Audits on-demand query execution expenses and identifies costly unpruned query scans.[^bq-jobs-by-project]

[^bq-jobs-by-project]: BigQuery Jobs by Project
