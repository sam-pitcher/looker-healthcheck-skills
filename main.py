#!/usr/bin/env python3
"""
Entrypoint for Looker & BigQuery Optimization Orchestrator.
Supports:
  1. CLI Healthcheck: `python main.py`
  2. Interactive Web Dashboard: `python main.py --web`
"""

import sys
import os
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

from agent.tools.looker_api import run_healthcheck_audit
from agent.tools.storage import save_audit_report, get_audit_history, get_audit_document

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Looker & BigQuery Healthcheck Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0b0f19;
            --bg-card: #151e32;
            --border: #24324f;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --accent-hover: #0284c7;
            --green: #10b981;
            --yellow: #f59e0b;
            --red: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        .sidebar {
            width: 360px;
            background: #070a12;
            border-right: 1px solid var(--border);
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            overflow-y: auto;
        }
        .logo {
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--accent);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .btn-audit {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: white;
            border: none;
            padding: 14px 18px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3);
        }
        .btn-audit:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(2, 132, 199, 0.4);
        }
        .section-title {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 8px;
        }
        .history-list, .pillar-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .history-item, .pillar-item {
            padding: 10px 14px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.85rem;
            color: var(--text-main);
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        .history-item:hover, .pillar-item:hover {
            border-color: var(--accent);
            background: #1c2742;
        }
        .history-meta {
            font-size: 0.75rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }
        .badge-firestore {
            display: inline-block;
            font-size: 0.65rem;
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent);
            padding: 2px 6px;
            border-radius: 4px;
            width: fit-content;
            margin-top: 4px;
        }
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-primary);
            padding: 32px;
            overflow-y: auto;
            gap: 16px;
        }
        .header-title {
            font-size: 1.6rem;
            font-weight: 700;
        }
        .header-sub {
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        .report-view {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.88rem;
            line-height: 1.6;
            white-space: pre-wrap;
            color: #cbd5e1;
            flex: 1;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">
            <span>✨</span> Looker & BQ Healthcheck
        </div>
        <button class="btn-audit" id="btn-run" onclick="runAudit()">⚡ Run Full 30-Check Audit</button>

        <div class="section-title">☁️ Firestore Audit Archive</div>
        <div class="history-list" id="history-box">
            <div style="font-size: 0.8rem; color: var(--text-muted);">Loading Firestore records...</div>
        </div>

        <div class="section-title">🏛️ 3 Pillars of Health</div>
        <div class="pillar-list">
            <div class="pillar-item" onclick="loadPillar(1)">
                <strong>Pillar 1: Instance & Content</strong>
                <span class="history-meta">Tasks 01 to 10</span>
            </div>
            <div class="pillar-item" onclick="loadPillar(2)">
                <strong>Pillar 2: LookML & Modeling</strong>
                <span class="history-meta">Tasks 11 to 20</span>
            </div>
            <div class="pillar-item" onclick="loadPillar(3)">
                <strong>Pillar 3: BigQuery & Compute</strong>
                <span class="history-meta">Tasks 21 to 30</span>
            </div>
        </div>
    </div>

    <div class="main-content">
        <div class="header-title">Looker & BigQuery Instance Healthcheck</div>
        <div class="header-sub">Persistent multi-tenant diagnostic engine connected to <code>Firestore: looker-healthcheck-db</code></div>
        <div class="report-view" id="report-box">Loading latest healthcheck report...</div>
    </div>

    <script>
        async function fetchHistory() {
            const hBox = document.getElementById('history-box');
            try {
                const res = await fetch('/api/history');
                const data = await res.json();
                if (!data || data.length === 0) {
                    hBox.innerHTML = '<div style="font-size: 0.8rem; color: var(--text-muted);">No records in Firestore.</div>';
                    return;
                }
                hBox.innerHTML = data.map(item => `
                    <div class="history-item" onclick="loadDoc('${item.audit_id}')">
                        <strong>${item.audit_id}</strong>
                        <span class="history-meta">${item.timestamp || 'Recent'}</span>
                        <span class="badge-firestore">☁️ ${item.source || 'firestore'}</span>
                    </div>
                `).join('');
            } catch (e) {
                hBox.innerHTML = '<div style="font-size: 0.8rem; color: var(--red);">Error loading Firestore archive.</div>';
            }
        }

        async function loadDoc(auditId) {
            const box = document.getElementById('report-box');
            box.innerText = "Fetching document " + auditId + " from Firestore...";
            try {
                const res = await fetch('/api/document?id=' + encodeURIComponent(auditId));
                const data = await res.json();
                box.innerText = data.document;
            } catch (err) {
                box.innerText = "Error loading document: " + err;
            }
        }

        async function runAudit() {
            const box = document.getElementById('report-box');
            const btn = document.getElementById('btn-run');
            btn.disabled = true;
            btn.innerText = "⏳ Auditing Instance...";
            box.innerText = "Executing complete 30-Check Healthcheck across Instance, LookML, and BigQuery...";
            try {
                const res = await fetch('/api/audit', { method: 'POST' });
                const data = await res.json();
                box.innerText = data.report;
                fetchHistory();
            } catch (err) {
                box.innerText = "Error running audit: " + err;
            } finally {
                btn.disabled = false;
                btn.innerText = "⚡ Run Full 30-Check Audit";
            }
        }

        async function loadPillar(pillarNum) {
            const box = document.getElementById('report-box');
            box.innerText = "Auditing Pillar " + pillarNum + "...";
            try {
                const res = await fetch('/api/audit?pillar=' + pillarNum, { method: 'POST' });
                const data = await res.json();
                box.innerText = data.report;
            } catch (err) {
                box.innerText = "Error loading pillar: " + err;
            }
        }

        // Init
        fetchHistory();
        loadDoc('latest');
    </script>
</body>
</html>
"""

class ADKWebHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/history":
            from agent.tools.storage import _get_firestore_client, FIRESTORE_COLLECTION, REPORTS_DIR
            history = []
            client = _get_firestore_client()
            if client:
                try:
                    docs = client.collection(FIRESTORE_COLLECTION).order_by("timestamp", direction="DESCENDING").limit(10).stream()
                    for d in docs:
                        data = d.to_dict()
                        history.append({
                            "audit_id": data.get("audit_id", d.id),
                            "timestamp": data.get("timestamp", ""),
                            "instance_url": data.get("instance_url", ""),
                            "source": "Firestore"
                        })
                except Exception:
                    pass
            if not history and REPORTS_DIR.exists():
                for f in sorted(REPORTS_DIR.glob("*.json"), reverse=True)[:10]:
                    try:
                        d = json.loads(f.read_text(encoding="utf-8"))
                        history.append({
                            "audit_id": d.get("audit_id", f.stem),
                            "timestamp": d.get("timestamp", ""),
                            "instance_url": d.get("instance_url", ""),
                            "source": "Local Snapshot"
                        })
                    except Exception:
                        continue
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(history).encode("utf-8"))
        elif parsed.path == "/api/document":
            query = urllib.parse.parse_qs(parsed.query)
            audit_id = query.get("id", [None])[0]
            target_id = None if audit_id == "latest" else audit_id
            doc_content = get_audit_document(target_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"document": doc_content}).encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/audit":
            report = run_healthcheck_audit()
            save_audit_report(report, {"status": "success"})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"report": report}).encode("utf-8"))
        else:
            self.send_error(404)

def start_web_server(port=8080):
    server = HTTPServer(("0.0.0.0", port), ADKWebHandler)
    print(f"\n🌐 Looker & BigQuery Healthcheck Hub running at:\n   http://localhost:{port}\n")
    server.serve_forever()

def main():
    if "--web" in sys.argv or "--server" in sys.argv:
        start_web_server(8080)
    else:
        try:
            print("🚀 Executing Looker Healthcheck Audit...")
            report = run_healthcheck_audit()
            save_audit_report(report, {"status": "success"})
            output_file = Path(__file__).parent / "AUDIT_REPORT.md"
            print(f"\n✅ Audit complete! Report written to:\n{output_file}\n")
        except Exception as e:
            print(f"❌ Error running healthcheck audit: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
