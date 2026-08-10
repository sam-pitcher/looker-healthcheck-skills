# Recipe 08: Advanced Optimization & Aggregate Awareness (Component 8)

## 1. Objective & Purpose
Implement advanced database acceleration architectures including Looker **Aggregate Awareness** (`aggregate_table`) and **Hub & Spoke** modular project structures for enterprise scale.

---

## 2. Aggregate Awareness Implementation Playbook

When an Explore queries fact tables with tens of millions of rows, define pre-computed aggregate tables directly inside the LookML explore:

```lookml
explore: order_items {
  aggregate_table: rollup__order_created_date {
    query: {
      dimensions: [order_items.created_date, users.country]
      measures: [order_items.total_gross_revenue, order_items.count]
    }
    materialization: {
      datagroup_trigger: ecommerce_daily_datagroup
    }
  }
}
```

### Benefits:
* Looker's compiler automatically intercepts user queries matching the rollup level and routes them to the compact aggregate table instead of scanning the full raw table.
* Accelerates dashboard load times from 15s to < 1s.

---

## 3. Hub & Spoke Project Architecture

For multi-department instances:
1. **Core Hub Project**: Contains database connections and raw physical `.view.lkml` files.
2. **Spoke Projects**: Departmental projects (`marketing`, `finance`, `operations`) that import the Hub via `local_dependency` or `remote_dependency` and refine views with domain-specific measures.
