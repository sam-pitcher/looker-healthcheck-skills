# Recipe 03: LookML Model Review & Transcriber Scoring (Component 3)

## 1. Objective & Purpose
Evaluate LookML codebases against the official **Transcriber** framework (0–4 grading scale) to ensure model stability, clarity, and performance-first design.

---

## 2. Transcriber Evaluation Grading Scale (0 to 4)

| Score | Rating | Definition |
| :---: | :--- | :--- |
| **0** | **Unsatisfactory** | Project actively violates best practice (e.g. Raw view files exposed with unmasked ID fields, missing primary keys). |
| **1** | **Needs Improvement** | Partial adherence (e.g. Main fact view cleaned, but dimension views lack formatting or hide rules). |
| **2** | **Meets Expectations** | Project adheres to best practices ~90% of the time (Industry average customer baseline). |
| **3** | **Exceeds Expectations** | Consistent adherence with clear developer intent, documented comments, and logical groupings. |
| **4** | **Exceptional** | Innovative patterns (e.g. LookML sets used strategically per explore, full field masking, visual drill paths). |

---

## 3. Four Core Focus Areas to Audit

### Area 1: Primary Key Declaration
Every view file **MUST** declare exactly one dimension with `primary_key: yes`:
```lookml
# ✅ Best Practice
dimension: id {
  primary_key: yes
  type: number
  sql: ${TABLE}.id ;;
}
```

### Area 2: Key Masking & Field Picker Hygiene
Unimportant ID dimensions and join keys should be hidden from business users:
```lookml
# ✅ Best Practice: Hidden foreign key used strictly for joins
dimension: user_id {
  hidden: yes
  type: number
  sql: ${TABLE}.user_id ;;
}
```

### Area 3: Modular Explore Architecture
Explores must **never** be defined inside `.view.lkml` files. They must live in modular `.explore.lkml` or clean `.model.lkml` files.

### Area 4: Field Count Budgets (40–50 Fields per Explore)
Keep the number of exposed fields in an explore between 40 and 50. Use LookML `fields:` or `access_grants` to prune unneeded dimensions.
