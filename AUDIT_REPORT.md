# Scoped Looker Healthcheck Audit: ecommerce_analytics
**Target Model:** `ecommerce_analytics` (Project: `retail_lookml`)

## 1. Master Scorecard Matrix
| Pillar | Check No. | Task Name | Status | Observed Value |
| :--- | :---: | :--- | :---: | :--- |
| **Pillar 1** | **01** | Subsystem Status | **PASSED** | 200 OK |
| **Pillar 2** | **12** | Primary Key Validation | **CRITICAL** | `order_id` missing PK |
| **Pillar 3** | **21** | Partition Filters | **WARNING** | Missing conditionally_filter on event_date |

## 2. Executive Remediation Recipe
1. Add `primary_key: yes` to `views/order_items.view.lkml`.
