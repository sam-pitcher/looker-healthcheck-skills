# Recipe 05: Development Workflows & CI/CD Best Practices (Component 5)

## 1. Objective & Purpose
Assess and advance the organization's LookML review, testing, and promotion processes across a 3-tier maturity framework.

---

## 2. The 3-Tier Workflow Maturity Framework

```
                          DEVELOPMENT WORKFLOW TIERS
 ┌───────────────────────────┬───────────────────────────┬───────────────────────────┐
 │ Tier 1: Pull Requests     │ Tier 2: Automated Testing │ Tier 3: Multi-Stage QA    │
 ├───────────────────────────┼───────────────────────────┼───────────────────────────┤
 │ • Mandatory Git branches  │ • LookML Data Tests       │ • Multi-Instance:         │
 │ • At least 1 peer review  │ • Content Validator API   │   Dev -> Staging -> Prod  │
 │ • Conventional commits    │ • CI/CD Integration       │ • Strict SLA verification │
 └───────────────────────────┴───────────────────────────┴───────────────────────────┘
```

---

## 3. Tier Implementation Playbook

### Tier 1: Pull Requests & Git Strategy (For all multi-developer teams)
* Require Pull Requests before merging to `production` branch.
* Enforce branch naming: `feature/<feature_name>` or `bugfix/<ticket_id>`.
* Use PR templates requiring description of business impact and model testing notes.

### Tier 2: Automated LookML Testing & CI/CD (For teams with business-critical reports)
* Define LookML Data Tests in `tests/*.test.lkml`:
  ```lookml
  test: view_primary_key_is_unique {
    explore_source: base_explore {
      column: id {}
      column: count {}
      sorts: [base_explore.count: desc]
      limit: 5
    }
    assert: primary_key_is_unique {
      expression: ${base_explore.count} = 1 ;;
    }
  }
  ```
* Integrate `looker-cli project validate <project_id>` into CI pipeline (GitHub Actions).

### Tier 3: Multi-Stage Environment Promotion (For embedded or enterprise instances)
* Separate development from production instances.
* Automated release promotion using Looker API / Spectacles.
