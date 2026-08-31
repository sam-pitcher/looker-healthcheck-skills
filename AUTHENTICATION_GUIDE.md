# 🔐 Complete Authentication & Identity Guide

> **An authoritative, end-to-end guide explaining how authentication, credentials, and cross-project permissions work across Gemini, Google Cloud (Logging/Firestore), BigQuery, and Looker API.**

---

## 📑 Table of Contents
1. [The 4 Independent Auth Layers](#1-the-4-independent-auth-layers)
2. [Scenario 1: Dual-Identity Setup (Runner vs. Corporate Warehouse)](#2-scenario-1-dual-identity-setup-runner-vs-corporate-warehouse)
3. [Scenario 2: Standard Single-Project Setup](#3-scenario-2-standard-single-project-setup)
4. [Scenario 3: Headless Production & CI/CD (Service Account)](#4-scenario-3-headless-production--cicd-service-account)
5. [Code-Level Mechanics (How Tools Resolve Credentials)](#5-code-level-mechanics-how-tools-resolve-credentials)
6. [Troubleshooting & Verification Matrix](#6-troubleshooting--verification-matrix)

---

## 1. The 4 Independent Auth Layers

When the healthcheck agent runs, it interacts with **4 distinct systems**. Each system authenticates independently:

```
                            YOUR LOCAL WORKSTATION
                                      │
         ┌───────────────────┬────────┴───────────────┬──────────────────────┐
         ▼                   ▼                        ▼                      ▼
  [ 1. GEMINI LLM ]   [ 2. TELEMETRY & DB ]    [ 3. BIGQUERY WAREHOUSE ]  [ 4. LOOKER API 4.0 ]
  • Auth: API Key or  • Auth: Ambient ADC      • Auth: Ambient ADC or     • Auth: User OAuth
    Vertex AI ADC     • Target: Runner GCP       Explicit gcloud Account    (~/.config/looker-cli)
  • Generates text      Project (Logging &     • Target: Customer Data    • Runs System Activity
    & tool reasoning    Firestore DB)            Warehouse Project          queries & validates
```

| # | Subsystem | What It Does | Default Credential Source |
| :-: | :--- | :--- | :--- |
| **1** | **Gemini LLM** | Powers agent reasoning & tool orchestration. | `GEMINI_API_KEY` (AI Studio) **OR** Vertex AI ADC. |
| **2** | **Telemetry & State** | Streams structured logs to Cloud Logging & Firestore. | Ambient ADC (`gcloud auth application-default login`). |
| **3** | **BigQuery Warehouse** | Runs forensic queries (`INFORMATION_SCHEMA`, table DDL). | `TARGET_BIGQUERY_ACCOUNT` via `gcloud` **OR** ADC. |
| **4** | **Looker API 4.0** | Inspects models, explores, and System Activity. | `looker-cli` OAuth token (`~/.config/looker-cli/config.yaml`). |

---

## 2. Scenario 1: Dual-Identity Setup (Runner vs. Corporate Warehouse)

### The Problem This Solves:
* You run the agent, Cloud Logging, and Firestore in your **Personal / Sandbox Project** (e.g. `<YOUR_RUNNER_GCP_PROJECT>` via `admin@yourcompany.com`).
* You need to audit BigQuery tables in a **Corporate / Internal Project** (e.g. `<YOUR_TARGET_BQ_PROJECT>` where only `user@yourcompany.com` has access).
* **The Constraint**: `user@yourcompany.com` has zero permissions in `<YOUR_RUNNER_GCP_PROJECT>`, and `admin@yourcompany.com` has zero permissions in `<YOUR_TARGET_BQ_PROJECT>`.

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 YOUR WORKSTATION                       │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
             ┌───────────────────────────────┴───────────────────────────────┐
             ▼                                                               ▼
  [ Project A: <YOUR_RUNNER_GCP_PROJECT> ]                            [ Project B: <YOUR_TARGET_BQ_PROJECT> ]
  • Identity: admin@yourcompany.com (ADC)                • Identity: user@yourcompany.com (gcloud)
  • Cloud Logging (`looker_healthcheck_telemetry`)                • BigQuery Forensic SQL (`INFORMATION_SCHEMA`)
  • Firestore DB (`looker-healthcheck-db`)                        • Compute Slot & Byte Billing
```

### Step-by-Step Setup:

#### Step 1: Authenticate the Runner Project (ADC)
Log in with the account that has access to your playground/runner project:
```bash
gcloud auth application-default login
# Logs in as: admin@yourcompany.com
```

#### Step 2: Authenticate Your Corporate BigQuery Account in `gcloud`
Log in with your corporate account:
```bash
gcloud auth login user@yourcompany.com
```

Verify both accounts are visible:
```bash
gcloud auth list
# ACTIVE  ACCOUNT
#         admin@yourcompany.com
# *       user@yourcompany.com
```

#### Step 3: Authenticate Looker API
Log in to Looker via user OAuth:
```bash
looker-cli session login --oauth --client-id com.looker.cli
```

#### Step 4: Configure `.env`
```ini
# --- 1. Agent Runner & Telemetry (Project A) ---
GOOGLE_GENAI_USE_VERTEXAI=false
GEMINI_API_KEY=AQ.Ab8...your_google_ai_studio_key...
GOOGLE_CLOUD_PROJECT=<YOUR_RUNNER_GCP_PROJECT>
GOOGLE_CLOUD_LOCATION=us-central1

FIRESTORE_DATABASE=looker-healthcheck-db
FIRESTORE_COLLECTION=looker_healthchecks

# --- 2. BigQuery Data Warehouse (Project B) ---
TARGET_BIGQUERY_PROJECT=<YOUR_TARGET_BQ_PROJECT>
TARGET_BIGQUERY_ACCOUNT=user@yourcompany.com
TARGET_BIGQUERY_DATASET=faa
TARGET_BIGQUERY_LOCATION=US

# --- 3. Looker Instance ---
LOOKERSDK_BASE_URL=https://yourcompany.looker.app
```

### How the Agent Resolves This at Runtime:
1. **Logging & Firestore**: Use the ambient ADC (`admin@yourcompany.com`) to write logs to `<YOUR_RUNNER_GCP_PROJECT>`.
2. **BigQuery Queries**: When `bq_client.py` runs, it sees `TARGET_BIGQUERY_ACCOUNT=user@yourcompany.com`. It runs `gcloud auth print-access-token --account=user@yourcompany.com` to fetch a fresh token for `user@yourcompany.com` and creates the BigQuery client targeting `<YOUR_TARGET_BQ_PROJECT>`.
3. **Gemini LLM**: `GOOGLE_GENAI_USE_VERTEXAI=false` + `GEMINI_API_KEY` calls Google AI Studio directly with zero GCP IAM needed.

---

## 3. Scenario 2: Standard Single-Project Setup

### The Problem This Solves:
A developer or consultant running the agent, Vertex AI, and BigQuery inside a single company GCP project (e.g. `company-analytics-prod`) using one email (`developer@company.com`).

```
                              developer@company.com (ADC)
                                           │
             ┌─────────────────────────────┴─────────────────────────────┐
             ▼                                                           ▼
  [ Vertex AI Gemini & Cloud Logging ]                       [ BigQuery Data Warehouse ]
  Project: company-analytics-prod                            Project: company-analytics-prod
```

### Step-by-Step Setup:

#### Step 1: Authenticate Once
```bash
gcloud auth application-default login
looker-cli session login --oauth --client-id com.looker.cli
```

#### Step 2: Configure `.env`
```ini
# --- Single Project Setup ---
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=company-analytics-prod
GOOGLE_CLOUD_LOCATION=us-central1
AGENT_MODEL=gemini-3.7-flash

FIRESTORE_DATABASE=looker-healthcheck-db
FIRESTORE_COLLECTION=looker_healthchecks

TARGET_BIGQUERY_PROJECT=company-analytics-prod
TARGET_BIGQUERY_DATASET=analytics_marts
TARGET_BIGQUERY_LOCATION=US

LOOKERSDK_BASE_URL=https://company.looker.com
```

#### Step 3: Required IAM Roles on `developer@company.com`
* `roles/aiplatform.user` (to call Vertex AI Gemini)
* `roles/logging.logWriter` (to write audit telemetry)
* `roles/datastore.user` (to read/write Firestore audit logs)
* `roles/bigquery.jobUser` (to execute BigQuery audit queries)
* `roles/bigquery.dataViewer` (to inspect table schemas & metadata)

---

## 4. Scenario 3: Headless Production & CI/CD (Service Account)

### The Problem This Solves:
Deploying the agent into **Cloud Run**, **GKE**, or **GitHub Actions / GitLab CI** where no human is present to log in via browser.

```
                      Service Account / Workload Identity
                  looker-agent-sa@project.iam.gserviceaccount.com
                                           │
             ┌─────────────────────────────┼─────────────────────────────┐
             ▼                             ▼                             ▼
  [ Vertex AI & Logging ]        [ BigQuery Warehouse ]          [ Looker API 4.0 ]
  Project: runner-prod           Project: warehouse-prod         Static API Client Key
```

### Step-by-Step Setup:

#### 1. Cloud Run / GKE:
Attach a service account (`looker-agent-sa@...`) to your Cloud Run service with:
* `roles/aiplatform.user` on the runner project.
* `roles/logging.logWriter` on the runner project.
* `roles/bigquery.jobUser` and `roles/bigquery.dataViewer` on the warehouse project.

#### 2. Configure `.env` with Static Looker SDK Keys:
```ini
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=runner-prod
GOOGLE_CLOUD_LOCATION=us-central1

# Static Looker API 4.0 Service Credentials (No Browser OAuth):
LOOKERSDK_BASE_URL=https://company.looker.com
LOOKERSDK_CLIENT_ID=your_looker_api3_client_id
LOOKERSDK_CLIENT_SECRET=your_looker_api3_client_secret

TARGET_BIGQUERY_PROJECT=warehouse-prod
TARGET_BIGQUERY_DATASET=core
TARGET_BIGQUERY_LOCATION=US
```

---

## 5. Code-Level Mechanics (How Tools Resolve Credentials)

Here is how the Python code dynamically selects and caches credentials:

### A. BigQuery Client ([`agent/tools/bq_client.py`](agent/tools/bq_client.py))
```python
def _get_credentials_for_account(account_email: str):
    """Dynamically extracts an OAuth access token for a specific gcloud identity."""
    token = subprocess.check_output(
        ["gcloud", "auth", "print-access-token", f"--account={account_email}"],
        stderr=subprocess.DEVNULL
    ).decode("utf-8").strip()
    return Credentials(token)

@lru_cache(maxsize=16)
def _get_bq_client(project_id=None, location=None):
    proj = project_id or TARGET_BQ_PROJECT_ID
    loc = location or TARGET_BQ_LOCATION
    
    # 1. If an explicit BigQuery account is configured, fetch its dedicated token:
    if TARGET_BQ_ACCOUNT:
        creds = _get_credentials_for_account(TARGET_BQ_ACCOUNT)
        return bigquery.Client(project=proj, credentials=creds, location=loc)
        
    # 2. Otherwise, fall back to standard ambient Application Default Credentials:
    return bigquery.Client(project=proj, location=loc)
```

### B. Looker API Client ([`agent/tools/looker_api.py`](agent/tools/looker_api.py))
```python
def _load_cli_session(self) -> bool:
    """Dynamically inherits user OAuth token from ~/.config/looker-cli/config.yaml."""
    config_path = os.path.expanduser("~/.config/looker-cli/config.yaml")
    if os.path.exists(config_path):
        # Parses active host, access_token, and refresh_token
        self.token = parsed_access_token
        self.base_url = parsed_host
        self.auth_mode = "looker_cli_oauth"
        return True
    return False
```

### C. Cloud Logging & Firestore ([`agent/telemetry.py`](agent/telemetry.py) & [`agent/tools/storage.py`](agent/tools/storage.py))
```python
# Both clients initialize using standard ambient ADC for the runner project:
logging_client = google.cloud.logging.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
firestore_client = google.cloud.firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
```

---

## 6. Troubleshooting & Verification Matrix

Run these quick terminal commands to verify your credentials:

| Check | Verification Command | Expected Success Output |
| :--- | :--- | :--- |
| **ADC Runner Identity** | `gcloud auth application-default print-access-token` | Prints a `ya29...` bearer token. |
| **BigQuery Identity** | `gcloud auth print-access-token --account=your-email@google.com` | Prints a `ya29...` bearer token. |
| **Looker OAuth Token** | `cat ~/.config/looker-cli/config.yaml` | Displays `access_token:` and `host:`. |
| **Live BigQuery Test** | `.venv/bin/python -c "from agent.tools.bq_client import run_bq_query; print(run_bq_query('SELECT 1'))"` | Returns `### ⚡ BigQuery Query Result (1 rows)`. |
| **Live Looker Test** | `.venv/bin/python -c "from agent.tools.looker_api import list_models; print(list_models())"` | Returns JSON list of models on your Looker instance. |
