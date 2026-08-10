# Recipe 08: Advanced Optimization & Aggregate Awareness (Component 8)

## 1. Objective & Purpose
Implement advanced database acceleration architectures including Looker **Aggregate Awareness** (`aggregate_table`) and **Hub & Spoke** modular project structures for enterprise scale across any business domain.

---

## 2. Aggregate Awareness Implementation Playbook

When an Explore queries fact tables with tens of millions of rows, define pre-computed aggregate tables directly inside the LookML explore:

```lookml
explore: fact_explore_name {
  aggregate_table: rollup__event_daily {
    query: {
      dimensions: [fact_view.event_date, dimension_view.category]
      measures: [fact_view.total_amount, fact_view.count]
    }
    materialization: {
      datagroup_trigger: warehouse_daily_datagroup
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
