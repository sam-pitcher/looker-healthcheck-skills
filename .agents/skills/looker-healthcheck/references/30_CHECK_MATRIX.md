# 30-Check Healthcheck Matrix & PSO Benchmarks

This reference lists the 30 standardized checks across the 3 pillars, their target benchmarks, and severity triggers.

---

## Pillar 1: Looker Instance & Query Lifecycle Performance

| Check ID | Check Name | Target Benchmark / SLA | Warning Trigger | Critical Trigger |
| :---: | :--- | :--- | :--- | :--- |
| **P1-01** | Subsystem Health & API Latency | API Response $< 150\text{ms}$ | Latency $> 300\text{ms}$ | Endpoint error (5xx) |
| **P1-02** | Connection Pool Limits | Concurrency $< 80\%$ pool capacity | Concurrency $> 80\%$ | Connection queue wait $> 1\text{s}$ |
| **P1-03** | Dashboard Tile Density | $\le 25$ query tiles per dashboard | $26–35$ query tiles | $> 35$ query tiles |
| **P1-04** | Auto-Refresh Rates | Refresh rate $\ge$ ETL frequency | Refresh $< 30\text{m}$ | Refresh $< 10\text{m}$ |
| **P1-05** | Schedule Time Staggering | Scheduled deliveries off-hour | $5–10$ jobs on `:00` | $> 10$ jobs on `:00` |
| **P1-06** | Query Concurrency Peaks | Evenly distributed concurrency | Peak $> 3\times$ average | Queue wait spike $> 2\text{s}$ |
| **P1-07** | Stale Content Deprecation | 0 unused dashboards ($>90$ days) | $5–20$ stale items | $> 20$ stale items |
| **P1-08** | Explore Filter Enforcement | Required partition/date filter | Fact explore missing filter | Unbounded scan on $>10\text{M}$ rows |
| **P1-09** | Merged Queries in Production | 0 merged query tiles in prod | $1–3$ merged tiles | $> 3$ merged tiles (JVM OOM risk)|
| **P1-10** | Legacy Feature Deprecation | 0 deprecated features enabled | $1–2$ deprecated flags | Critical legacy feature active |

---

## Pillar 2: LookML Modeling & Code Quality

| Check ID | Check Name | Target Benchmark / SLA | Warning Trigger | Critical Trigger |
| :---: | :--- | :--- | :--- | :--- |
| **P2-11** | Syntax & Compilation Health | 0 LookML validation errors | Minor linter warnings | Validator compilation error |
| **P2-12** | Primary Key Integrity | 100% joined views have PK | Missing PK on small table | Missing PK causing `SUM(DISTINCT)` |
| **P2-13** | Explicit Join Cardinality | 100% explicit `relationship:` | Default `many_to_one` used | Cartesian cross join (`type: cross`) |
| **P2-14** | Henry Dead Field Vacuum | 0 unused dimensions/measures | $10–25\%$ dead fields | $> 25\%$ dead fields exposed |
| **P2-15** | Raw Foreign Key Masking | 100% `_id`/`_pk`/`_fk` hidden | Technical key visible in UI | Key exposed in user-facing explore |
| **P2-16** | Folder & File Organization | Views & models modularized | Monolithic files ($>500$ lines)| Unorganized root directory |
| **P2-17** | `snake_case` Naming Standard | 100% snake_case fields | CamelCase or spaces in names | Broken naming convention |
| **P2-18** | User-Facing Descriptions | 100% measures have descriptions| Descriptions on $<80\%$ fields | 0 descriptions (Gemini blind) |
| **P2-19** | Explore Join Bloat | $\le 6$ joined views per explore | $7–12$ joins in explore | $> 12$ joins (chasm/fanout risk) |
| **P2-20** | Table Calculation Bloat | Server-side LookML measures | $> 5$ table calcs on tile | Heavy client-side post-processing |

---

## Pillar 3: BigQuery & Warehouse Compute Optimization

| Check ID | Check Name | Target Benchmark / SLA | Warning Trigger | Critical Trigger |
| :---: | :--- | :--- | :--- | :--- |
| **P3-21** | Partition & Cluster Alignment | All fact tables partitioned | Unclustered $> 1\text{GB}$ table | Unpartitioned $> 10\text{M}$ row scan |
| **P3-22** | BI Engine Acceleration | Memory allocated for hot tables | BI Engine partially disabled | BI Engine bypass due to complex SQL |
| **P3-23** | PDT Build Failure Logs | 0 PDT regeneration failures | PDT rebuild runtime $> 15\text{m}$ | PDT rebuild loop / failure |
| **P3-24** | Incremental PDT Strategy | Fact PDTs built incrementally | Full rebuild on $> 50\text{M}$ rows | Re-scan of full table every hour |
| **P3-25** | Datagroup ETL Sync Triggers | Cache invalidation on ETL load | Time-based cache age mismatch | Volatile trigger (`GENERATE_UUID()`) |
| **P3-26** | User Attribute Cache Scope | Cache hits across user groups | Over-scoped user attributes | Cache miss on every user query |
| **P3-27** | Aggregate Awareness Rollups | Hot explores have aggregate tables| Daily queries hitting raw grain | Repeated $> 10\text{GB}$ scan for rollup |
| **P3-28** | SQL Join Function Overhead | Pure indexed join keys | String trimming in `sql_on:` | `REGEXP_CONTAINS` in `sql_on:` |
| **P3-29** | Table Denormalization Audit | Star/Snowflake dimensional model| 10+ joins for simple reporting| Extreme normalization join penalty |
| **P3-30** | Query Costs & Bytes Billed | 95th percentile query $< 1\text{GB}$| Single query $> 5\text{GB}$ billed | Repeated $> 50\text{GB}$ query burst |
