#!/usr/bin/env python3
"""
Entrypoint for Looker & BigQuery Optimization Orchestrator.
Supports:
  1. CLI Healthcheck: `python main.py [--model=<model_name>]`
  2. Interactive Web Dashboard: `python main.py --web`
"""

import sys
import os
import json
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import urllib.parse
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agent.tools.looker_api import run_healthcheck_audit, execute_complete_healthcheck, _client
from agent.tools.storage import save_audit_report, save_technical_design_document, get_audit_history, get_audit_document
from agent.skills_registry import skill_registry

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
            width: 380px;
            background: #070a12;
            border-right: 1px solid var(--border);
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            overflow-y: auto;
        }
        .logo {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--accent);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .model-select-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .model-select-group label {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        select.model-dropdown {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 0.88rem;
            outline: none;
            cursor: pointer;
        }
        .btn-audit {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: white;
            border: none;
            padding: 12px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.92rem;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3);
        }
        .btn-audit:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(2, 132, 199, 0.4);
        }
        .section-title {
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 4px;
        }
        .history-list, .skills-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
            max-height: 180px;
            overflow-y: auto;
        }
        .history-item, .skill-item {
            padding: 8px 12px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.8rem;
            color: var(--text-main);
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .history-item:hover, .skill-item:hover {
            border-color: var(--accent);
            background: #1c2742;
        }
        .history-meta {
            font-size: 0.7rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }
        .badge-firestore {
            display: inline-block;
            font-size: 0.62rem;
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent);
            padding: 2px 5px;
            border-radius: 4px;
            width: fit-content;
            margin-top: 3px;
        }
        .badge-vendor {
            display: inline-block;
            font-size: 0.62rem;
            background: rgba(16, 185, 129, 0.15);
            color: var(--green);
            padding: 2px 5px;
            border-radius: 4px;
            width: fit-content;
        }
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-primary);
            padding: 28px;
            overflow-y: auto;
            gap: 14px;
        }
        .header-title {
            font-size: 1.5rem;
            font-weight: 700;
        }
        .header-sub {
            color: var(--text-muted);
            font-size: 0.88rem;
        }
        .report-view {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
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
            <span>✨</span> Looker & BQ Optimizer
        </div>

        <div class="model-select-group">
            <label for="model-select">Target Model Scope</label>
            <select id="model-select" class="model-dropdown">
                <option value="">-- All Models (Instance Wide) --</option>
            </select>
        </div>

        <button class="btn-audit" id="btn-run" onclick="runAudit()">⚡ Run Scoped Healthcheck</button>

        <div class="section-title">☁️ Firestore Audit Archive</div>
        <div class="history-list" id="history-box">
            <div style="font-size: 0.8rem; color: var(--text-muted);">Loading Firestore records...</div>
        </div>

        <div class="section-title">📚 Official Looker Skills Playbooks</div>
        <div class="skills-list" id="skills-box">
            <div style="font-size: 0.8rem; color: var(--text-muted);">Loading skills...</div>
        </div>
    </div>

    <div class="main-content">
        <div class="header-title">Looker & BigQuery Instance Healthcheck</div>
        <div class="header-sub">Model-Scoped Diagnostic Engine connected to <code>Firestore: looker-healthcheck-db</code></div>
        <div class="report-view" id="report-box">Loading latest healthcheck report...</div>
    </div>

    <script>
        async function fetchModels() {
            try {
                const res = await fetch('/api/models');
                const models = await res.json();
                const sel = document.getElementById('model-select');
                models.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m.name;
                    opt.innerText = m.name + (m.project_name ? ' (' + m.project_name + ')' : '');
                    sel.appendChild(opt);
                });
            } catch (e) {}
        }

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
                        <span class="badge-firestore">☁️ ${item.target_scope?.model_name || 'all_models'}</span>
                    </div>
                `).join('');
            } catch (e) {
                hBox.innerHTML = '<div style="font-size: 0.8rem; color: var(--red);">Error loading archive.</div>';
            }
        }

        async function fetchSkills() {
            const sBox = document.getElementById('skills-box');
            try {
                const res = await fetch('/api/skills');
                const data = await res.json();
                sBox.innerHTML = data.map(s => `
                    <div class="skill-item" onclick="loadSkill('${s.name}')">
                        <strong>${s.name}</strong>
                        <span class="history-meta">${s.description || 'Looker skill'}</span>
                        <span class="badge-vendor">${s.source}</span>
                    </div>
                `).join('');
            } catch (e) {
                sBox.innerHTML = '<div style="font-size: 0.8rem; color: var(--red);">Error loading skills.</div>';
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

        async function loadSkill(skillName) {
            const box = document.getElementById('report-box');
            box.innerText = "Loading official skill " + skillName + "...";
            try {
                const res = await fetch('/api/skill?name=' + encodeURIComponent(skillName));
                const data = await res.json();
                box.innerText = data.content;
            } catch (err) {
                box.innerText = "Error loading skill: " + err;
            }
        }

        async function runAudit() {
            const box = document.getElementById('report-box');
            const btn = document.getElementById('btn-run');
            const model = document.getElementById('model-select').value;
            btn.disabled = true;
            btn.innerText = "⏳ Auditing...";
            box.innerText = "Executing 30-Check Healthcheck" + (model ? " scoped to model '" + model + "'..." : " across all models...");
            try {
                const res = await fetch('/api/audit' + (model ? '?model=' + encodeURIComponent(model) : ''), { method: 'POST' });
                const data = await res.json();
                box.innerText = data.report;
                fetchHistory();
            } catch (err) {
                box.innerText = "Error running audit: " + err;
            } finally {
                btn.disabled = false;
                btn.innerText = "⚡ Run Scoped Healthcheck";
            }
        }

        // Init
        fetchModels();
        fetchHistory();
        fetchSkills();
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
        elif parsed.path == "/api/models":
            models = []
            try:
                raw = _client.get("lookml_models")
                models = [{"name": m.get("name"), "project_name": m.get("project_name")} for m in raw]
            except Exception:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(models).encode("utf-8"))
        elif parsed.path == "/api/skills":
            skills = skill_registry.list_available_skills()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(skills).encode("utf-8"))
        elif parsed.path == "/api/skill":
            query = urllib.parse.parse_qs(parsed.query)
            sname = query.get("name", [""])[0]
            content = skill_registry.get_skill_prompt(sname)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"name": sname, "content": content}).encode("utf-8"))
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
                            "target_scope": data.get("target_scope", {}),
                            "summary": data.get("summary", {}),
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
                            "target_scope": d.get("target_scope", {}),
                            "summary": d.get("summary", {}),
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
            query = urllib.parse.parse_qs(parsed.query)
            model_name = query.get("model", [None])[0]
            report, structured_findings = execute_complete_healthcheck(model_name=model_name)
            save_audit_report(report, structured_findings, model_name=model_name)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"report": report, "summary": structured_findings}).encode("utf-8"))
        else:
            self.send_error(404)

def start_web_server(port=8080):
    server = ThreadingHTTPServer(("0.0.0.0", port), ADKWebHandler)
    print(f"\n🌐 Looker & BigQuery Healthcheck Hub running at:\n   http://localhost:{port}\n")
    server.serve_forever()

def main():
    if "--web" in sys.argv or "--server" in sys.argv:
        start_web_server(8080)
    else:
        try:
            model_arg = None
            for arg in sys.argv:
                if arg.startswith("--model="):
                    model_arg = arg.split("=", 1)[1]
            print(f"🚀 Executing Complete 30-Check Looker Healthcheck Audit" + (f" for model '{model_arg}'..." if model_arg else "..."))
            report, structured_findings = execute_complete_healthcheck(model_name=model_arg)
            save_result = save_audit_report(report, structured_findings, model_name=model_arg)
            save_technical_design_document(report, model_name=model_arg)
            print(f"\n✅ Audit complete! Score: {structured_findings.get('overall_health_score')}% ({structured_findings.get('passed')} Passed, {structured_findings.get('warning')} Warnings, {structured_findings.get('critical')} Critical).")
            print(f"📄 Publication-grade specification written to TECHNICAL_DESIGN_DOCUMENT.md")
            print(save_result + "\n")
        except Exception as e:
            print(f"❌ Error running healthcheck audit: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
