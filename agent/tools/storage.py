"""
Dual-Layer Storage Engine: Firestore & Local Markdown Deliverables.
Persists human-readable Markdown reports to AUDIT_REPORT.md and structured telemetry to Firestore.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
FIRESTORE_DATABASE = os.getenv("FIRESTORE_DATABASE", "(default)")
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "looker_healthchecks")
REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"
ROOT_AUDIT_FILE = Path(__file__).resolve().parent.parent.parent / "AUDIT_REPORT.md"

def _get_firestore_client():
    try:
        from google.cloud import firestore
        proj = GCP_PROJECT_ID or None
        return firestore.Client(project=proj, database=FIRESTORE_DATABASE)
    except Exception:
        return None

def save_audit_report(report_markdown: str, structured_findings: Optional[Dict[str, Any]] = None) -> str:
    """
    Saves the healthcheck audit results into both storage layers:
    1. Human-Readable Markdown: Writes directly to `AUDIT_REPORT.md` in repository root.
    2. Structured Datastore: Persists timestamped JSON to Firestore (collection: `looker_healthchecks`) and local `/reports/`.
    
    Args:
        report_markdown (str): The complete formatted Markdown audit report.
        structured_findings (dict, optional): Structured dictionary with pillar and check scores.
    """
    now = datetime.now(timezone.utc)
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    file_timestamp = now.strftime("%Y%m%d_%H%M%S")
    audit_id = f"audit_{file_timestamp}"
    
    # 1. Write to AUDIT_REPORT.md in repo root
    try:
        ROOT_AUDIT_FILE.write_text(report_markdown, encoding="utf-8")
        markdown_saved = True
    except Exception as e:
        markdown_saved = False

    # 2. Prepare structured record
    record = {
        "audit_id": audit_id,
        "timestamp": timestamp_str,
        "instance_url": os.getenv("LOOKERSDK_BASE_URL", ""),
        "findings": structured_findings or {},
        "markdown_report_preview": report_markdown[:1500]
    }

    # Save local JSON snapshot in /reports/
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_file = REPORTS_DIR / f"{audit_id}.json"
        snapshot_file.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
        local_json_saved = True
    except Exception:
        local_json_saved = False

    # 3. Persist to Firestore
    firestore_client = _get_firestore_client()
    firestore_status = "Skipped (Firestore client unavailable or unconfigured)"
    if firestore_client:
        try:
            doc_ref = firestore_client.collection(FIRESTORE_COLLECTION).document(audit_id)
            doc_ref.set(record)
            firestore_status = f"✅ Saved to Firestore (`{FIRESTORE_COLLECTION}/{audit_id}`)"
        except Exception as e:
            firestore_status = f"❌ Firestore write failed: {str(e)}"

    output = {
        "audit_id": audit_id,
        "timestamp": timestamp_str,
        "markdown_file": str(ROOT_AUDIT_FILE) if markdown_saved else "Failed to write AUDIT_REPORT.md",
        "local_snapshot": str(snapshot_file) if local_json_saved else "None",
        "firestore_status": firestore_status
    }
    
    return f"### 💾 Healthcheck Audit State Persisted:\n```json\n{json.dumps(output, indent=2)}\n```"

def get_audit_history(limit: int = 5) -> str:
    """
    Retrieves past audit runs from Firestore (or local `/reports/` archive) to track degradation or improvements over time.
    
    Args:
        limit (int): Number of historical audit records to return (default: 5).
    """
    client = _get_firestore_client()
    history = []
    
    if client:
        try:
            docs = client.collection(FIRESTORE_COLLECTION).order_by("timestamp", direction="DESCENDING").limit(limit).stream()
            for d in docs:
                data = d.to_dict()
                history.append({
                    "audit_id": data.get("audit_id"),
                    "timestamp": data.get("timestamp"),
                    "instance_url": data.get("instance_url"),
                    "source": "firestore"
                })
            if history:
                return f"### 📜 Historical Healthchecks (from Firestore):\n```json\n{json.dumps(history, indent=2)}\n```"
        except Exception:
            pass

    # Fallback to local /reports/ directory
    if REPORTS_DIR.exists():
        files = sorted(REPORTS_DIR.glob("*.json"), reverse=True)[:limit]
        for f in files:
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                history.append({
                    "audit_id": d.get("audit_id"),
                    "timestamp": d.get("timestamp"),
                    "instance_url": d.get("instance_url"),
                    "source": "local_reports_dir"
                })
            except Exception:
                continue

    if history:
        return f"### 📜 Historical Healthchecks (from Local Snapshots):\n```json\n{json.dumps(history, indent=2)}\n```"
    return "No previous healthcheck audits found in Firestore or local archives."
