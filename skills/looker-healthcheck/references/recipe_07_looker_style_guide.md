# Recipe 07: Looker Style Guide Best Practices (Component 7)

## 1. Objective & Purpose
Establish consistent, clean, and maintainable LookML modeling standards across all projects, enforcing the DRY (Don't Repeat Yourself) philosophy and self-service clarity.

---

## 2. Universal LookML Style Rules

### Rule 1: Field Naming Conventions
* Dimension and measure names **MUST** be `snake_case`.
* Measures **MUST** include descriptive prefixes matching their aggregation type:
  - `total_[field]` for `type: sum`
  - `average_[field]` for `type: average`
  - `count_[field]` for `type: count` / `type: count_distinct`
  - `is_[condition]` or `has_[condition]` for `type: yesno`

### Rule 2: Descriptions and User Guidance
* Every user-facing measure and business dimension **MUST** include a `description:` parameter explaining business logic and nuances.

### Rule 3: Value Formatting
* Format currency, percentages, and integers using built-in or custom named formats:
  ```lookml
  measure: total_gross_margin {
    type: sum
    sql: ${sale_price} - ${cost} ;;
    value_format_name: usd
    description: "Total revenue minus cost of goods sold (COGS)."
  }
  ```

### Rule 4: Drill Fields & Custom HTML Links
* Every core KPI measure should declare `drill_fields:` to guide business users into granular transaction details:
  ```lookml
  measure: total_order_count {
    type: count
    drill_fields: [order_id, user_id, status, created_date]
  }
  ```
