# Recipe 06: Security Review: Roles & Permissions (Component 6)

## 1. Objective & Purpose
Audit Looker user roles, group hierarchies, license allocations, and access grants to prevent admin proliferation, duplicate permission sets, and security misconfigurations.

---

## 2. Diagnostic Execution Protocol

### Step 1: User Distribution Across Roles
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "user",
  "fields": ["role.name", "user.count"],
  "filters": {"user.is_disabled": "No"},
  "sorts": ["user.count desc"],
  "limit": "50"
}' --verify-ssl=false
```

### Step 2: Audit Developer Licenses
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "user",
  "fields": ["user.count"],
  "filters": {
    "user.is_disabled": "No",
    "permission_set.permissions": "%develop%"
  },
  "limit": "1"
}' --verify-ssl=false
```

### Step 3: Identify Empty Groups (0 Users)
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "group",
  "fields": ["group.name", "user.count"],
  "filters": {"user.count": "0"},
  "limit": "25"
}' --verify-ssl=false
```

### Step 4: Audit Direct Role Assignments
```bash
looker-cli api query run_inline_query --body '{
  "model": "system__activity",
  "view": "user",
  "fields": ["user.id", "user.name", "role.name", "role.embed"],
  "filters": {"role.embed": "No", "user.is_disabled": "No"},
  "limit": "50"
}' --verify-ssl=false
```

---

## 3. Security Best Practices Playbook

1. **Enforce Group-Based Access Control (GBAC)**:
   - Assign roles strictly to **Groups**, never directly to individual users.
2. **Eliminate Orphaned & Duplicate Sets**:
   - Delete permission sets and model sets that are not attached to any active role.
3. **Access Grants for Row/Column Security**:
   - Implement LookML `access_grant` parameters tied to user attributes (`user_attribute: department`) rather than creating separate explores for each department.
