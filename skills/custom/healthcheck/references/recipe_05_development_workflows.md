# Recipe 05: Development Workflows & CI/CD Best Practices (Component 5)

## 1. Objective & Purpose
Establish a robust, automated LookML engineering and quality-assurance pipeline across the **3-Tier Maturity Framework** to prevent broken production dashboards, syntax errors, and silent logic regressions.

```
                           THE 3-TIER MATURITY FRAMEWORK
 ┌───────────────────────────┬───────────────────────────┬───────────────────────────┐
 │ Tier 1: Git & Reviews     │ Tier 2: Automated Testing │ Tier 3: Multi-Stage QA    │
 ├───────────────────────────┼───────────────────────────┼───────────────────────────┤
 │ • Protected Main Branch   │ • Native LookML Data Tests│ • Multi-Instance Release: │
 │ • Mandatory Pull Requests │ • CI Content Validation   │   Dev -> QA -> Production │
 │ • Branch Naming Standards │ • Automated LookML Linter │ • Automated Spectacles CI │
 │ • Peer Review Checklists  │ • Pre-Merge Gateways      │ • Zero Downtime Deploys   │
 └───────────────────────────┴───────────────────────────┴───────────────────────────┘
```

---

## 2. The 3-Tier Implementation Playbook

### Tier 1: Git Branching & Peer Review (Foundational)
* **Protected Production Branch**: Direct commits to `production` / `master` are blocked in Git settings.
* **Standardized Branch Naming**:
  - `feature/<ticket_id>-<description>` (e.g. `feature/BI-104-add-gross-margin`)
  - `fix/<ticket_id>-<description>` (e.g. `fix/BI-202-correct-tax-rate`)
* **Pull Request Checklist Requirements**:
  - [ ] LookML syntax validated with zero compiler errors.
  - [ ] Primary keys declared on all new views.
  - [ ] Business descriptions added to all exposed measures and dimensions.
  - [ ] Performance verified in Developer Mode (query runtime < 5s).

---

### Tier 2: Native LookML Data Tests & Automated CI Testing

Create a dedicated `tests/` directory in your LookML project (e.g. `tests/model_integrity.test.lkml`):

#### A. Primary Key Uniqueness & Non-Null Test
```lookml
test: assert_orders_primary_key_unique {
  explore_source: orders {
    column: order_id { field: orders.id }
    column: order_count { field: orders.count }
    sorts: [orders.count: desc]
    limit: 5
  }
  assert: primary_key_has_no_duplicates {
    expression: ${orders.count} = 1 ;;
  }
  assert: primary_key_is_not_null {
    expression: NOT is_null(${orders.id}) ;;
  }
}
```

#### B. Referential Integrity Test (Zero Orphaned Records)
```lookml
test: assert_order_items_have_valid_users {
  explore_source: order_items {
    column: user_id { field: order_items.user_id }
    column: user_name { field: users.name }
    filters: {
      field: users.id
      value: "NULL"
    }
    limit: 10
  }
  assert: zero_orphaned_foreign_keys {
    expression: count(${order_items.user_id}) = 0 ;;
  }
}
```

---

### Tier 3: Complete GitHub Actions CI/CD Pipeline Template

Create `.github/workflows/looker_ci.yml` in your LookML Git repository:

```yaml
name: LookML Quality Assurance & Validation CI

on:
  pull_request:
    branches: [ main, production ]

jobs:
  validate-lookml:
    name: LookML Syntax & Content Validation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Validation Tooling
        run: |
          pip install looker-sdk spectacles

      - name: Run LookML Project Compilation Test
        env:
          LOOKERSDK_BASE_URL: ${{ secrets.LOOKERSDK_BASE_URL }}
          LOOKERSDK_CLIENT_ID: ${{ secrets.LOOKERSDK_CLIENT_ID }}
          LOOKERSDK_CLIENT_SECRET: ${{ secrets.LOOKERSDK_CLIENT_SECRET }}
        run: |
          python -c "
          import looker_sdk
          sdk = looker_sdk.init40()
          project_id = '${{ secrets.LOOKER_PROJECT_ID }}'
          results = sdk.validate_project(project_id)
          if results.errors:
              print(f'❌ LookML Validation Failed with {len(results.errors)} errors:')
              for err in results.errors:
                  print(f'  - [{err.file_path}:{err.line_number}] {err.message}')
              exit(1)
          print('✅ LookML Validation Passed!')
          "

      - name: Run Spectacles SQL & Content Validation Gate
        env:
          LOOKERSDK_BASE_URL: ${{ secrets.LOOKERSDK_BASE_URL }}
          LOOKERSDK_CLIENT_ID: ${{ secrets.LOOKERSDK_CLIENT_ID }}
          LOOKERSDK_CLIENT_SECRET: ${{ secrets.LOOKERSDK_CLIENT_SECRET }}
        run: |
          spectacles sql --project ${{ secrets.LOOKER_PROJECT_ID }} --branch ${{ github.head_ref }}
          spectacles content --project ${{ secrets.LOOKER_PROJECT_ID }} --branch ${{ github.head_ref }}
```

---

## 3. Maturity Assessment Scorecard

| Maturity Tier | Capability | Status Indicator | Action Required |
| :---: | :--- | :---: | :--- |
| **Tier 1** | Git Branching & PR Reviews | ⚠️ / ✅ | Enable GitHub branch protection rules. |
| **Tier 2** | LookML Data Tests | ⚠️ / ✅ | Add `tests/*.test.lkml` for top 3 fact views. |
| **Tier 2** | Automated CI Validation | ⚠️ / ✅ | Deploy `.github/workflows/looker_ci.yml`. |
| **Tier 3** | Content Validator Regression Testing | ⚠️ / ✅ | Integrate Spectacles / Content Validator API. |
| **Tier 3** | Multi-Stage Dev $\rightarrow$ QA $\rightarrow$ Prod Promotion | ⚠️ / ✅ | Implement automated API deployment scripts. |
