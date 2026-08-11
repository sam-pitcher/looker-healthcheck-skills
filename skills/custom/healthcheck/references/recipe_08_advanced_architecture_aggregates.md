# Recipe 08: Advanced Optimization & Aggregate Awareness (Component 8)

## 1. Objective & Purpose
Implement advanced database acceleration architectures including Looker **Aggregate Awareness** (`aggregate_table`) and **Hub & Spoke** modular project dependencies for enterprise scale, sub-second dashboard performance, and massive warehouse cost reductions.

```
                    AGGREGATE AWARENESS ROUTING ENGINE
                                User Query
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │ Looker SQL Compiler                  │
                 │ Checks active aggregate_table list   │
                 └──────────────────┬───────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           │ Matches Rollup Level?                           │
           ▼ (YES)                                           ▼ (NO)
 ┌───────────────────────────────────┐             ┌───────────────────────────────────┐
 │ ⚡ COMPACT AGGREGATE TABLE        │             │ 🐢 FULL RAW FACT TABLE            │
 │ • Scans: 10,000 pre-aggregated rows│             │ • Scans: 100,000,000 raw rows     │
 │ • Latency: < 0.8 seconds          │             │ • Latency: 12 - 25 seconds        │
 │ • Cost: $0.0001                   │             │ • Cost: $0.6250                   │
 └───────────────────────────────────┘             └───────────────────────────────────┘
```

---

## 2. Aggregate Awareness Implementation Playbook

### Step 1: Define Centralized Event Datagroups in the Model File
```lookml
# models/ecommerce.model.lkml
connection: "bigquery_production"

datagroup: warehouse_daily_etl_datagroup {
  sql_trigger_value: SELECT MAX(created_at) FROM `project.dataset.etl_log` WHERE status = 'SUCCESS' ;;
  max_cache_age: "24 hours"
  description: "Triggers cache and PDT/Aggregate rebuilds upon completion of daily warehouse ETL."
}
```

---

### Step 2: Define Aggregate Tables Inside the Explore
Add `aggregate_table:` blocks directly inside your high-traffic explores:

```lookml
# explores/orders.explore.lkml
explore: orders {
  persist_with: warehouse_daily_etl_datagroup
  
  join: users {
    relationship: many_to_one
    sql_on: ${orders.user_id} = ${users.id} ;;
  }

  # Aggregate Rollup: Daily Sales by Category & Region
  aggregate_table: rollup__daily_sales_by_category {
    query: {
      dimensions: [
        orders.created_date,
        users.country,
        products.category
      ]
      measures: [
        orders.total_revenue,
        orders.count,
        orders.average_order_value
      ]
      timezone: "America/New_York"
    }
    materialization: {
      datagroup_trigger: warehouse_daily_etl_datagroup
      partition_keys: ["created_date"]
      cluster_keys: ["country", "category"]
    }
  }
}
```

---

### Step 3: Verify Aggregate Table Utilization in System Activity
Query `system__activity.history` to confirm queries are hitting the aggregate table:

```json
{
  "model": "system__activity",
  "view": "history",
  "fields": [
    "history.query_run_count",
    "history.average_runtime",
    "history.source",
    "query.view"
  ],
  "filters": {
    "history.created_date": "7 days",
    "query.view": "orders"
  },
  "limit": "20"
}
```

---

## 3. Hub & Spoke Enterprise Architecture

For organizations with multiple data teams or domain boundaries, decompose monolithic LookML projects into a **Hub & Spoke** dependency structure:

```
                            HUB & SPOKE ARCHITECTURE
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ CORE HUB REPOSITORY (git@github.com:org/lookml-core-hub.git)              │
 │ • Database connection definitions                                         │
 │ • Physical view models (.view.lkml) mapping raw warehouse schema          │
 │ • Core enterprise dimensions (Primary keys, standardized date logic)      │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │ (Imported via remote_dependency)
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
 ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
 │ Marketing Spoke Repo │    │ Finance Spoke Repo   │    │ Product Analytics    │
 │ • Refined Explores   │    │ • GAAP Measures      │    │ • Clickstream Models │
 │ • Campaign Dashboards│    │ • Financial Models   │    │ • Retention Explores │
 └──────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

### Spoke Project Manifest Definition (`manifest.lkml`):
```lookml
# manifest.lkml in marketing_spoke project
project_name: "marketing_spoke"

remote_dependency: lookml_core_hub {
  url: "git@github.com:company/lookml-core-hub.git"
  ref: "v2.1.0" # Lock to immutable semantic version tag
}
```

### Spoke Model View Refinement:
```lookml
# models/marketing.model.lkml
include: "//lookml_core_hub/views/orders.view.lkml"

# Refine Hub view with marketing-specific business logic
view: +orders {
  dimension: marketing_channel_attribution {
    type: string
    sql: COALESCE(${TABLE}.utm_source, 'Direct') ;;
  }
}
```
