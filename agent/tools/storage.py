"""
Dual-Layer Storage Engine: Firestore & Local Markdown Deliverables.
Persists human-readable Markdown reports to AUDIT_REPORT.md and structured scoped telemetry to Firestore.
"""

import os
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional, List
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GCP_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
FIRESTORE_DATABASE = os.getenv("FIRESTORE_DATABASE", "looker-healthcheck-db")
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "looker_healthchecks")
REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"

@lru_cache(maxsize=1)
def _get_firestore_client():
    try:
        from google.cloud import firestore
        proj = GCP_PROJECT_ID or None
        return firestore.Client(project=proj, database=FIRESTORE_DATABASE)
    except Exception:
        return None

def save_audit_report(
    report_markdown: str,
    structured_findings: Optional[Dict[str, Any]] = None,
    model_name: Optional[str] = None,
    project_id: Optional[str] = None
) -> str:
    """
    Saves the healthcheck audit results into Firestore with model scoping:
    1. Structured Datastore: Persists timestamped JSON to Firestore (collection: `looker_healthchecks`).
    2. Local Diagnostics Archive: Saves timestamped snapshot in `/reports/`.
    
    Args:
        report_markdown (str): The complete formatted Markdown audit report.
        structured_findings (dict, optional): Structured dictionary with pillar, check scores, and findings array.
        model_name (str, optional): Target LookML model name scope.
        project_id (str, optional): Target Looker/LookML project ID scope.
    """
    now = datetime.now(timezone.utc)
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    file_timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    model_slug = model_name.replace("-", "_").lower() if model_name else "instance"
    audit_id = f"audit_{model_slug}_{file_timestamp}"

    # Extract or calculate summary metrics
    sf = structured_findings or {}
    total_checks = int(sf.get("total_checks", 30))
    passed = int(sf.get("passed", 0))
    warning = int(sf.get("warning", 0))
    critical = int(sf.get("critical", 0))
    
    if total_checks > 0 and "overall_health_score" not in sf:
        health_score = round(((passed + (warning * 0.5)) / total_checks) * 100, 1)
    else:
        health_score = float(sf.get("overall_health_score", 100.0))

    summary = {
        "total_checks": total_checks,
        "passed": passed,
        "warning": warning,
        "critical": critical,
        "overall_health_score": health_score
    }

    # 2. Prepare structured record conforming to Developer Directive contract
    record = {
        "audit_id": audit_id,
        "timestamp": timestamp_str,
        "instance_url": os.getenv("LOOKERSDK_BASE_URL", ""),
        "target_scope": {
            "project_id": project_id or os.getenv("LOOKER_PROJECT_ID") or "unscoped",
            "model_name": model_name or "all_models"
        },
        "summary": summary,
        "findings": sf.get("findings", []),
        "markdown_report": report_markdown
    }

    # Save local JSON snapshot in /reports/
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_file = REPORTS_DIR / f"{audit_id}.json"
        snapshot_file.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
        local_json_saved = True
    except Exception:
        local_json_saved = False

    # Save Markdown report deliverable to repository root
    try:
        root_report = Path(__file__).resolve().parent.parent.parent / "AUDIT_REPORT.md"
        root_report.write_text(report_markdown, encoding="utf-8")
    except Exception:
        pass

    # 3. Persist to Firestore & Cloud Logging
    try:
        from agent.telemetry import log_cloud_event
        log_cloud_event("healthcheck_audit_saved", {
            "audit_id": audit_id,
            "target_scope": record["target_scope"],
            "summary": summary,
            "health_score": health_score,
            "findings_count": len(sf.get("findings", []))
        })
    except Exception:
        pass

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
        "target_scope": record["target_scope"],
        "health_score": f"{health_score}%",
        "firestore_status": firestore_status,
        "local_snapshot": str(snapshot_file) if local_json_saved else "None"
    }
    
    return f"### 💾 Healthcheck Audit State Persisted to Firestore:\n```json\n{json.dumps(output, indent=2)}\n```"

def get_audit_history(limit: int = 5, model_name: Optional[str] = None) -> str:
    """
    Retrieves past audit runs from Firestore (or local `/reports/` archive) to track degradation or improvements over time.
    
    Args:
        limit (int): Number of historical audit records to return (default: 5).
        model_name (str, optional): Filter history strictly for a specific model.
    """
    client = _get_firestore_client()
    history = []
    
    if client:
        try:
            query = client.collection(FIRESTORE_COLLECTION).order_by("timestamp", direction="DESCENDING")
            docs = query.limit(limit * 2 if model_name else limit).stream()
            for d in docs:
                data = d.to_dict()
                scope = data.get("target_scope", {})
                if model_name and scope.get("model_name") not in [model_name, "all_models"]:
                    continue
                history.append({
                    "audit_id": data.get("audit_id", d.id),
                    "timestamp": data.get("timestamp"),
                    "target_scope": scope,
                    "summary": data.get("summary", {}),
                    "source": "firestore"
                })
                if len(history) >= limit:
                    break
            if history:
                return f"### 📜 Historical Healthchecks (from Firestore):\n```json\n{json.dumps(history, indent=2)}\n```"
        except Exception:
            pass

    # Fallback to local /reports/ directory
    if REPORTS_DIR.exists():
        files = sorted(REPORTS_DIR.glob("*.json"), reverse=True)
        for f in files:
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                scope = d.get("target_scope", {})
                if model_name and scope.get("model_name") not in [model_name, "all_models"]:
                    continue
                history.append({
                    "audit_id": d.get("audit_id", f.stem),
                    "timestamp": d.get("timestamp"),
                    "target_scope": scope,
                    "summary": d.get("summary", {}),
                    "source": "local_reports_dir"
                })
                if len(history) >= limit:
                    break
            except Exception:
                continue

    if history:
        return f"### 📜 Historical Healthchecks (from Local Snapshots):\n```json\n{json.dumps(history, indent=2)}\n```"
    return f"No previous healthcheck audits found for model: {model_name or 'all'}."

def get_audit_document(audit_id: Optional[str] = None) -> str:
    """
    Retrieves the complete structured document and report for a specific audit (or the latest audit) from Firestore.
    
    Args:
        audit_id (str, optional): The specific audit ID (e.g. 'audit_ecommerce_analytics_20260810_174500'). If omitted, fetches latest.
    """
    client = _get_firestore_client()
    data = None
    
    if client:
        try:
            if audit_id and audit_id != "latest":
                doc = client.collection(FIRESTORE_COLLECTION).document(audit_id).get()
                if doc.exists:
                    data = doc.to_dict()
            else:
                docs = list(client.collection(FIRESTORE_COLLECTION).order_by("timestamp", direction="DESCENDING").limit(1).stream())
                if docs:
                    data = docs[0].to_dict()
        except Exception:
            pass

    if not data and REPORTS_DIR.exists():
        if audit_id and audit_id != "latest":
            f = REPORTS_DIR / f"{audit_id}.json"
            if f.exists():
                data = json.loads(f.read_text(encoding="utf-8"))
        else:
            files = sorted(REPORTS_DIR.glob("*.json"), reverse=True)
            if files:
                data = json.loads(files[0].read_text(encoding="utf-8"))

    if not data:
        return f"No audit document found for ID: {audit_id or 'latest'}."

    scope = data.get("target_scope", {})
    summary = data.get("summary", {})
    findings = data.get("findings", [])

    return (
        f"### 📄 Firestore Scoped Audit Document (`{data.get('audit_id')}`)\n"
        f"- **Timestamp:** `{data.get('timestamp')}`\n"
        f"- **Target Model:** `{scope.get('model_name', 'all_models')}` (Project: `{scope.get('project_id', 'default')}`)\n"
        f"- **Overall Health Score:** **{summary.get('overall_health_score', 'N/A')}%** (Passed: {summary.get('passed', 0)}, Warnings: {summary.get('warning', 0)}, Critical: {summary.get('critical', 0)})\n\n"
        f"#### 🔍 Key Structured Findings ({len(findings)} Total):\n"
        f"```json\n{json.dumps(findings[:5], indent=2)}\n```\n\n"
        f"#### 📝 Full Markdown Report Preview:\n\n{data.get('markdown_report', 'No markdown report attached.')[:3000]}"
    )
