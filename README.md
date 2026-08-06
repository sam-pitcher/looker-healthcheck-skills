# Looker Healthcheck ADK Agent

An autonomous Looker instance performance auditor and healthcheck agent built with the **Google Agent Development Kit (ADK)** and Google PSO (Professional Services Organization) benchmarks.

---

## Architecture Overview

```
looker-healthcheck-agent/
├── skills/                     # Single source of truth (PSO rules & recipes)
│   └── looker-healthcheck/
│       ├── SKILL.md            # Master skill with 5 optimization recipes
│       └── references/         # Exact PSO benchmark thresholds & queries
├── agent/                      # Python Google ADK Agent
│   ├── app.py                  # Agent orchestrator
│   ├── config.py               # Credentials & environment handler
│   ├── tools/
│   │   ├── looker_client.py    # Looker API query executor
│   │   └── skills_loader.py    # Dynamically ingests SKILL.md into agent context
│   └── reporters/
│       └── markdown_reporter.py# Formats executive scorecards & charts
└── main.py                     # CLI entrypoint
```

---

## Dual Consumption Model

1. **Autonomous Service (Google Cloud Run / CLI)**:
   - Evaluates `system__activity` metrics against PSO benchmarks.
   - Generates executive diagnostic reports (`AUDIT_REPORT.md`).
2. **IDE Assistant Integration (Antigravity with Gemini)**:
   - Ingests `skills/looker-healthcheck/` directly via `skills.json`.
   - Allows developers to apply recipes interactively in LookML files.

---

## Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Set your Looker API credentials:
```bash
export LOOKERSDK_BASE_URL="https://your-instance.looker.app"
export LOOKERSDK_CLIENT_ID="your_client_id"
export LOOKERSDK_CLIENT_SECRET="your_client_secret"
```
*(Or the agent will automatically read credentials from `.vscode/settings.json`).*

### 3. Run the Audit
```bash
python main.py
```

---

## License
Apache-2.0
