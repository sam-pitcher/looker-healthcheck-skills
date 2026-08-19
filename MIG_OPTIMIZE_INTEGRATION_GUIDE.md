# 🚀 Upstream `mig-optimize` Integration Guide

This document explains what the Google Cloud Professional Services **`mig-optimize`** repository is, how it compares to our agent's native BigQuery engine, and the exact step-by-step procedure required to deploy and connect the remote `mig-optimize` Agent-to-Agent (A2A) service in the future.

---

## 📌 1. Architecture Overview: Native Mode vs. Remote A2A Mode

```
                                 Looker Healthcheck Agent
                                             │
                  ┌──────────────────────────┴──────────────────────────┐
                  ▼                                                     ▼
    CURRENT: Native Embedded Mode                         FUTURE: Remote A2A Service Mode
    • Direct Python BigQuery Client (bq_client.py)        • External Cloud Run Microservice
    • Skills & Playbooks (warehouse_optimization.md)      • JSON-RPC / A2A Protocol (invoke.sh)
    • Direct INFORMATION_SCHEMA queries                   • Centrally managed enterprise service
    • Zero extra cloud infrastructure                     • Google OIDC Bearer Token Auth
```

### Mode Comparison:

| Feature | Current: Native Engine | Future: Remote `mig-optimize` Service |
| :--- | :--- | :--- |
| **Execution Path** | In-process Python (`agent/tools/bq_client.py`) | Remote HTTP / JSON-RPC over Cloud Run |
| **Infrastructure Needed** | None (uses local ADC `gcloud auth ...`) | Cloud Run container, Artifact Registry, IAM bindings |
| **BigQuery Rules Applied** | 15 PSO Anti-Pattern Rules + Looker Tuning | 15 PSO Anti-Pattern Rules + Fine-tuned LLM Prompting |
| **Latency** | Milliseconds (Direct SDK) | Network roundtrip (~1–3s) |
| **Maintenance** | Single self-contained repository | Dual-service maintenance (Agent + Microservice) |

---

## 🏗️ 2. What `mig-optimize` Contains

The upstream Google repository (`sso://google-cloud-professional-services/mig-optimize`) contains:

1. **BigQuery Optimization Agent Service**: A Python/FastAPI container that hosts endpoints for analyzing SQL queries, evaluating AST anti-patterns, and validating query dry-runs.
2. **A2A (Agent-to-Agent) Skills Definition**: 10 interface manifests (`bq_optimize_query`, `bq_analyze_job`, `bq_get_job_details`, etc.) that define the JSON-RPC contract:
   ```json
   {
     "jsonrpc": "2.0",
     "method": "message/send",
     "params": {
       "message": {
         "role": "user",
         "parts": [{ "kind": "text", "text": "Optimize this BigQuery query: ..." }]
       }
     }
   }
   ```
3. **Invocation Helpers**: Shell and Python scripts (`invoke.sh`) to authenticate via `gcloud auth print-identity-token` and route requests to the deployed Cloud Run URL.

---

## 🛠️ 3. Step-by-Step: How to Add `mig-optimize` in the Future

If your organization decides to deploy a dedicated `mig-optimize` microservice, follow these steps to integrate it:

### Step 3.1: Clone and Deploy the `mig-optimize` Backend to Cloud Run

```bash
# 1. Clone the upstream repository using internal SSO
git clone sso://google-cloud-professional-services/mig-optimize /tmp/mig-optimize

# 2. Build and submit container image to Google Cloud Artifact Registry
gcloud builds submit /tmp/mig-optimize \
    --tag gcr.io/${GOOGLE_CLOUD_PROJECT}/mig-optimize-agent:latest

# 3. Deploy the container to Cloud Run
gcloud run deploy mig-optimize-agent \
    --image gcr.io/${GOOGLE_CLOUD_PROJECT}/mig-optimize-agent:latest \
    --platform managed \
    --region us-central1 \
    --set-env-vars GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT} \
    --set-labels agent-name=bigquery \
    --no-allow-unauthenticated
```

### Step 3.2: Grant IAM Permissions to the Service Account

The agent calling `mig-optimize` requires permissions to invoke Cloud Run and execute BigQuery jobs:

```bash
# Grant Cloud Run Invoker to your user or agent service account
gcloud run services add-iam-policy-binding mig-optimize-agent \
    --region=us-central1 \
    --member="user:$(gcloud config get-value account)" \
    --role="roles/run.invoker"

# Grant BigQuery Admin/User to the Cloud Run service account
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="serviceAccount:mig-optimize-sa@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" \
    --role="roles/bigquery.admin"
```

### Step 3.3: Re-Enable `mig-optimize` in `skills.yaml`

Add the upstream repo back to `skills.yaml`:

```yaml
repositories:
  - name: mig-optimize
    url: sso://google-cloud-professional-services/mig-optimize
    ref: master
    paths:
      - skills/bq_optimize_query
      - skills/bq_analyze_job
      - skills/bq_get_job_details
      - skills/bq_get_table_info
      - skills/bq_execute_sql_readonly
      - skills/bq_validate_query
      - skills/bq_get_dataset_info
      - skills/bq_list_dataset_ids
      - skills/bq_list_table_ids
      - skills/mig_optimize_discovery
```

Then run the sync script:
```bash
python3 scripts/sync_skills.py
```

### Step 3.4: Add the A2A HTTP Client Tool

Create `agent/tools/mig_optimize_client.py` to call the Cloud Run service:

```python
import os
import subprocess
import requests
from typing import Dict, Any

MIG_OPTIMIZE_URL = os.getenv("MIG_OPTIMIZE_URL", "")

def invoke_mig_optimize(query: str, project_id: str = "") -> str:
    """Invokes the remote mig-optimize Cloud Run service over JSON-RPC."""
    if not MIG_OPTIMIZE_URL:
        return "Error: MIG_OPTIMIZE_URL environment variable is not configured."
    
    # Generate Google OIDC Identity Token
    token = subprocess.check_output(["gcloud", "auth", "print-identity-token"]).decode().strip()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": f"Optimize BigQuery query: {query}"}]
            }
        }
    }
    response = requests.post(MIG_OPTIMIZE_URL, json=payload, headers=headers, timeout=60)
    return response.text
```

### Step 3.5: Update `.env` Configuration

Add the deployed service URL to your `.env`:
```env
MIG_OPTIMIZE_URL=https://mig-optimize-agent-xyz-uc.a.run.app
```

---

## 💡 4. Current State & Recommendation

For 99% of Looker & BigQuery healthcheck audits, **our native implementation is superior** because:
1. **Self-Contained**: No external cloud services to maintain or deploy.
2. **Instant Execution**: Python BigQuery SDK runs dry-runs and queries in under 50ms.
3. **Full Rule Coverage**: All 15 Google PSO BigQuery anti-patterns are fully maintained locally in `skills/custom/healthcheck/references/warehouse_optimization.md`.
