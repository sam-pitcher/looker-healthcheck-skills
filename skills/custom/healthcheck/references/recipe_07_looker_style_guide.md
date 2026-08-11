# Recipe 07: Looker Style Guide & Modeling Standards (Component 7)

## 1. Objective & Purpose
Establish consistent, clean, and maintainable LookML modeling standards across all projects, enforcing DRY (Don't Repeat Yourself) architecture, uniform naming conventions, and intuitive self-service field pickers.

```
                           THE LOOKER STYLE PYRAMID
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Layer 4: UX Polish: drill_fields, html badges, group_label                │
 ├───────────────────────────────────────────────────────────────────────────┤
 │ Layer 3: Value Formatting: value_format_name, descriptions                │
 ├───────────────────────────────────────────────────────────────────────────┤
 │ Layer 2: Semantic Naming: total_, count_, is_, snake_case                 │
 ├───────────────────────────────────────────────────────────────────────────┤
 │ Layer 1: Core Integrity: primary_key: yes, hidden: yes on FKs             │
 └───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Universal Field Naming Standards

### A. Measure Naming Rules (Mandatory Prefixes)
All measures **MUST** use explicit prefix notation corresponding to their SQL aggregation:

| Aggregation Type | Mandatory Prefix | Good Example | Bad Example (Anti-Pattern) |
| :--- | :--- | :--- | :--- |
| **Sum** | `total_` | `total_revenue`, `total_item_quantity` | `revenue`, `sum_price`, `sales` |
| **Average** | `average_` | `average_order_value`, `average_age` | `avg_order_value`, `aov` |
| **Count / Distinct** | `count_` | `count_orders`, `count_distinct_users` | `orders`, `users`, `num_users` |
| **Percentage / Ratio** | `percent_` / `ratio_` | `percent_of_total_revenue` | `margin_pct`, `pct` |
| **Min / Max** | `min_` / `max_` | `min_order_date`, `max_transaction_amount` | `first_order`, `highest_sale` |

### B. Dimension Naming Rules
* **Identifies Conditions**: Boolean / YesNo dimensions must start with `is_` or `has_` (e.g. `is_active_subscriber`, `has_completed_onboarding`).
* **Date Dimension Groups**: Keep the base name clean (e.g. `created` generates `created_date`, `created_week`, `created_month`).
* **Technical ID Masking**: Foreign keys must be named `[entity]_id` and marked `hidden: yes`.

---

## 3. Formatting, Descriptions & Drill Paths

### A. Number Formatting Standards
Always use standard named formats (`value_format_name:`) rather than raw custom format strings:
* **Currency**: `value_format_name: usd` or `usd_0` (for rounded dollars).
* **Percentages**: `value_format_name: percent_2` (e.g. `12.34%`) or `percent_1`.
* **Large Numbers**: `value_format_name: decimal_0` with thousands separators.

```lookml
measure: total_gross_margin {
  type: sum
  sql: ${sale_price} - ${cost} ;;
  value_format_name: usd
  description: "Total gross merchandise revenue minus cost of goods sold (COGS)."
}
```

---

### B. Drill Fields & Actionable Deep Dives
Every core measure should specify a `drill_fields:` set containing context dimensions:

```lookml
set: order_detail_fields {
  fields: [
    id,
    created_date,
    users.name,
    users.email,
    status,
    total_revenue
  ]
}

measure: count {
  type: count
  drill_fields: [order_detail_fields*]
  description: "Total count of orders with detail drill-down."
}
```

---

### C. Visual HTML Formatting (Status Badges)
Enhance tabular reporting with CSS-styled status badges:

```lookml
dimension: status {
  type: string
  sql: ${TABLE}.status ;;
  html: 
    {% if value == 'complete' %}
      <span style="color: #059669; background-color: #d1fae5; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Complete</span>
    {% elsif value == 'cancelled' %}
      <span style="color: #dc2626; background-color: #fee2e2; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Cancelled</span>
    {% else %}
      <span style="color: #d97706; background-color: #fef3c7; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Pending</span>
    {% endif %} ;;
}
```

---

## 4. DRY Modeling Standards & Group Labels

### A. Dimension Grouping (`group_label`)
Group related dimensions together to avoid cluttering the field picker:

```lookml
dimension: shipping_city {
  type: string
  sql: ${TABLE}.shipping_city ;;
  group_label: "Shipping Address"
}

dimension: shipping_postal_code {
  type: string
  sql: ${TABLE}.shipping_zip ;;
  group_label: "Shipping Address"
}
```

---

## 5. Style Guide Compliance Checklist

- [ ] All dimensions and measures use strict `snake_case`.
- [ ] Measures use required prefixes (`total_`, `average_`, `count_`, `is_`).
- [ ] 100% of user-facing measures declare `description:`.
- [ ] All financial measures declare `value_format_name: usd` or equivalent.
- [ ] All primary measures declare `drill_fields:`.
- [ ] All joined foreign keys declare `hidden: yes`.
- [ ] Explores reside in `/explores/` or `/models/`, never inside `/views/`.
