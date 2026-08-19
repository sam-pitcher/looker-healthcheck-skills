# Looker & BigQuery Performance Audit: 'thelook' Model / 'flights' Explore

## 1. Summary of Findings

A performance audit on the 'thelook' model, specifically focusing on the 'flights' explore, identified a chronically slow query (`query.id: 112008`) with an average runtime of over 50 seconds. The root cause is sub-optimal SQL generation stemming from the LookML model, which leads to poor database performance.

## 2. Root Cause Analysis: Inefficient Timezone Conversion

The primary driver of the latency is the repeated use of the `CONVERT_TZ` function in the generated SQL. This happens on the `dep_time` column for both the dimension and the filter.

**Problematic SQL Snippet:**
```sql
SELECT
    (YEAR(CONVERT_TZ(`dep_time`,'UTC','America/Los_Angeles'))) AS `flights.dep_year`,
    COUNT(*) AS `flights.count`
FROM
    `demo_db`.`flights` AS `flights`
WHERE ((( `dep_time` ) >= ((CONVERT_TZ(DATE_ADD(TIMESTAMP(DATE_FORMAT(DATE(CONVERT_TZ(NOW(),'UTC','America/Los_Angeles')),'%Y-01-01')),INTERVAL -19 year),\'America/Los_Angeles\',\'UTC\'))) AND ( `dep_time` ) < ((CONVERT_TZ(DATE_ADD(DATE_ADD(TIMESTAMP(DATE_FORMAT(DATE(CONVERT_TZ(NOW(),'UTC','America/Los_Angeles')),'%Y-01-01')),INTERVAL -19 year),INTERVAL 20 year),\'America/Los_Angeles\',\'UTC\')))))
GROUP BY
    1
ORDER BY
    1 DESC
LIMIT 500
```

This is inefficient because:
*   **It prevents index usage**: Applying a function like `CONVERT_TZ` to a column in the `WHERE` clause forces the database to scan the entire table instead of using an index.
*   **It's computationally expensive**: The database has to perform a timezone conversion for every row in the table.

## 3. LookML Recommendation: Optimize the `dep_time` Dimension Group

To resolve this, we need to adjust the `dimension_group` definition for `dep_time` in the `flights.view.lkml` file. By adding `convert_tz: no`, we tell Looker to offload the timezone conversion to the database driver level, which is more efficient. Additionally, we should ensure the `datatype` is set correctly.

**Recommended LookML Change:**

```lookml
# file: views/flights.view.lkml

view: flights {
  sql_table_name: `demo_db.flights` ;;

  dimension_group: dep_time {
    type: time
    timeframes: [
      raw,
      time,
      date,
      week,
      month,
      quarter,
      year
    ]
    sql: ${TABLE}.dep_time ;;
    # Add the following two lines
    datatype: datetime
    convert_tz: no
  }

  # ... other dimensions and measures
}
```

## 4. Expected Outcome

After applying this LookML change, the generated SQL will be much simpler and more efficient. The `WHERE` clause will no longer contain the `CONVERT_TZ` function, allowing the database to use an index on the `dep_time` column. This should result in a significant reduction in query runtime.

**Example of Improved SQL (conceptual):**

```sql
SELECT
    EXTRACT(YEAR FROM `dep_time`) AS `flights.dep_year`,
    COUNT(*) AS `flights.count`
FROM
    `demo_db`.`flights` AS `flights`
WHERE
    `dep_time` >= 'YYYY-MM-DD HH:MI:SS' AND `dep_time` < 'YYYY-MM-DD HH:MI:SS'
GROUP BY 1
ORDER BY 1 DESC
LIMIT 500;

```

This change will improve the performance of all queries that use the `dep_time` dimension group.
