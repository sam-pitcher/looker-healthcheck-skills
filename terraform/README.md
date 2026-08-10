# Firestore Infrastructure for Looker Healthcheck Agent

This Terraform module provisions the persistent Firestore database (Native mode) and required composite indexes for storing multi-tenant Looker healthcheck audit snapshots and tracking performance degradation over time.

---

## 📦 Provisioned Resources

1. **Google Cloud APIs**:
   - `firestore.googleapis.com`
   - `aiplatform.googleapis.com`
   - `bigquery.googleapis.com`
2. **Firestore Database**:
   - Native mode (`FIRESTORE_NATIVE`) with optimistic concurrency.
3. **Composite Index**:
   - Collection: `looker_healthchecks`
   - Fields: `instance_url` (ASC) + `timestamp` (DESC) for fast time-series queries.

---

## 🚀 Quick Deployment

1. Initialize Terraform:
   ```bash
   cd terraform
   terraform init
   ```

2. Configure Variables:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your GCP project ID
   ```

3. Review & Apply:
   ```bash
   terraform plan
   terraform apply
   ```

4. Add Outputs to `.env`:
   ```env
   GOOGLE_CLOUD_PROJECT=your-gcp-project
   FIRESTORE_DATABASE=(default)
   FIRESTORE_COLLECTION=looker_healthchecks
   ```
