# Recipe 06: Security Review: Roles & Permissions (Component 6)

## 1. Objective & Purpose
Audit Looker user roles, group hierarchies, license allocations, and access grants to prevent admin proliferation, duplicate permission sets, orphaned roles, and insecure direct-user assignments.

```
                  GROUP-BASED ACCESS CONTROL (GBAC) HIERARCHY
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ SAML / Okta / IdP Groups                                                  │
 │ (e.g. 'Looker-Finance-Explorers', 'Looker-Engineering-Developers')        │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │ (Auto-Synchronized via SSO)
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Looker Mirror Groups                                                      │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │ (Role Bound Strictly to Group)
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Looker Role = [ Permission Set ] + [ Model Set ]                          │
 │ (e.g. 'Finance Explorer' = 'Explore + See SQL' + 'Finance Models')        │
 └───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Diagnostic Execution Protocols (System Activity Queries)

### Step 1: User Distribution Across Roles
```json
{
  "model": "system__activity",
  "view": "user",
  "fields": [
    "role.name",
    "user.count",
    "permission_set.name",
    "model_set.name"
  ],
  "filters": {
    "user.is_disabled": "No"
  },
  "sorts": ["user.count desc"],
  "limit": "50"
}
```

### Step 2: Audit Direct User Role Assignments (Anti-Pattern)
Identifies individual users who have been granted roles directly rather than inheriting them from groups:
```json
{
  "model": "system__activity",
  "view": "user",
  "fields": [
    "user.id",
    "user.name",
    "user.email",
    "role.name"
  ],
  "filters": {
    "role.embed": "No",
    "user.is_disabled": "No"
  },
  "limit": "50"
}
```

### Step 3: Identify Orphaned & Empty Groups (0 Users)
```json
{
  "model": "system__activity",
  "view": "group",
  "fields": [
    "group.id",
    "group.name",
    "user.count"
  ],
  "filters": {
    "user.count": "0"
  },
  "limit": "25"
}
```

### Step 4: Developer License Proliferation Audit
```json
{
  "model": "system__activity",
  "view": "user",
  "fields": [
    "user.id",
    "user.name",
    "user_facts.last_ui_login_date"
  ],
  "filters": {
    "user.is_disabled": "No",
    "permission_set.permissions": "%develop%"
  },
  "sorts": ["user_facts.last_ui_login_date asc"],
  "limit": "50"
}
```

---

## 3. Security Best Practices & Governance Rules

### Rule 1: Enforce Group-Based Access Control (GBAC)
* **Never assign roles directly to users**: Individual user assignments create hidden privilege creep.
* **Assign roles exclusively to Groups**: Sync groups from your Identity Provider (SAML 2.0 / Google OAuth / Okta).
* When a user changes departments in the IdP, their Looker model access and permissions update automatically.

---

### Rule 2: LookML Access Grants for Row & Column Security
Instead of creating duplicate Explores (e.g. `orders_all` vs `orders_restricted`), use LookML `access_grant` parameters:

#### Step A: Define the Access Grant in the Model File
```lookml
# models/ecommerce.model.lkml
access_grant: can_view_sensitive_financials {
  user_attribute: department
  allowed_values: ["Finance", "Executive", "Legal"]
}
```

#### Step B: Protect Sensitive Dimensions / Measures
```lookml
# views/orders.view.lkml
dimension: customer_tax_id {
  type: string
  sql: ${TABLE}.tax_id ;;
  required_access_grants: [can_view_sensitive_financials]
}

measure: gross_margin {
  type: sum
  sql: ${sale_price} - ${cost} ;;
  value_format_name: usd
  required_access_grants: [can_view_sensitive_financials]
}
```

* Users without the `Finance` attribute simply do not see these fields in the field picker, and cannot query them via API.

---

### Rule 3: License Reclamation & Role Hygiene
* **Deactivate Inactive Developer Seats**: If a developer has not logged in or used Developer Mode for >60 days, downgrade to a Standard Viewer license.
* **Purge Orphaned Model Sets**: Review Admin $\rightarrow$ **Roles** $\rightarrow$ **Model Sets** and delete any sets referencing deleted LookML projects.
