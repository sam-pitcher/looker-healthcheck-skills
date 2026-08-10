#!/usr/bin/env python3
"""
Entrypoint for Looker Healthcheck Agent.
Supports:
  1. CLI Audit: `python main.py`
  2. Web UI:    `python main.py --web`
"""

import sys
import os
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
from looker_healthcheck_agent.agent import run_healthcheck_audit
from looker_healthcheck_agent.skills_loader import SkillsLoader

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Looker Healthcheck Agent</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-card: #1e293b;
            --border: #334155;
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
            width: 340px;
            background: #090d16;
            border-right: 1px solid var(--border);
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .logo {
            font-size: 1.1rem;
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
        .recipe-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
            overflow-y: auto;
        }
        .recipe-item {
            padding: 8px 12px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.8rem;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s;
        }
        .recipe-item:hover {
            border-color: var(--accent);
            color: var(--text-main);
        }
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            padding: 32px 48px;
        }
        .header-title {
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .header-sub {
            color: var(--text-muted);
            margin-bottom: 24px;
            font-size: 0.95rem;
        }
        .report-view {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 32px;
            line-height: 1.6;
            white-space: pre-wrap;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: #e2e8f0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-pso {
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent);
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">
            <span>✨</span> Looker Healthcheck Agent
        </div>
        <span class="badge badge-pso">8-Component Healthcheck Suite</span>
        <button class="btn-audit" id="btn-run" onclick="runAudit()">⚡ Run Full Healthcheck</button>
        <hr style="border-color: var(--border);">
        <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase;">8-Component Offerings</div>
        <div class="recipe-list">
            <div class="recipe-item" onclick="loadComponent(1)">1. Instance Walkthrough</div>
            <div class="recipe-item" onclick="loadComponent(2)">2. Performance Audit Review</div>
            <div class="recipe-item" onclick="loadComponent(3)">3. LookML Model Review (0-4)</div>
            <div class="recipe-item" onclick="loadComponent(4)">4. Unused Content Cleanup</div>
            <div class="recipe-item" onclick="loadComponent(5)">5. Development Workflows</div>
            <div class="recipe-item" onclick="loadComponent(6)">6. Security, Roles & Permissions</div>
            <div class="recipe-item" onclick="loadComponent(7)">7. Looker Style Guide</div>
            <div class="recipe-item" onclick="loadComponent(8)">8. Aggregate Awareness & Hub-Spoke</div>
        </div>
    </div>

    <div class="main-content">
        <div class="header-title">Looker Instance Healthcheck & Optimization</div>
        <div class="header-sub">Automated diagnostic engine querying <code>system__activity</code></div>
        <div class="report-view" id="report-box">Click "Run Full Healthcheck" to query live metrics from your Looker instance...</div>
    </div>

    <script>
        async function runAudit() {
            const box = document.getElementById('report-box');
            const btn = document.getElementById('btn-run');
            btn.disabled = true;
            btn.innerText = "⏳ Auditing Instance...";
            box.innerText = "Connecting to Looker API and querying system__activity...";
            try {
                const res = await fetch('/api/audit', { method: 'POST' });
                const data = await res.json();
                box.innerText = data.report;
            } catch (err) {
                box.innerText = "Error running audit: " + err;
            } finally {
                btn.disabled = false;
                btn.innerText = "⚡ Run Full Healthcheck";
            }
        }

        async function loadComponent(num) {
            const box = document.getElementById('report-box');
            box.innerText = "Auditing Component " + num + "...";
            try {
                const res = await fetch('/api/audit?component=' + num, { method: 'POST' });
                const data = await res.json();
                box.innerText = data.report;
            } catch (err) {
                box.innerText = "Error loading component: " + err;
            }
        }
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
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/audit":
            query = urllib.parse.parse_qs(parsed.query)
            comp_param = query.get("component", [None])[0]
            comp_id = int(comp_param) if comp_param else None
            report = run_healthcheck_audit(component_id=comp_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"report": report}).encode("utf-8"))
        else:
            self.send_error(404)

def start_web_server(port=8080):
    server = HTTPServer(("0.0.0.0", port), ADKWebHandler)
    print(f"\n🌐 Looker Healthcheck Web UI running at:\n   http://localhost:{port}\n")
    server.serve_forever()

def main():
    if "--web" in sys.argv or "--server" in sys.argv:
        start_web_server(8080)
    else:
        try:
            print("🚀 Executing Looker Healthcheck Audit...")
            report = run_healthcheck_audit()
            output_file = Path(__file__).parent / "AUDIT_REPORT.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n✅ Audit complete! Report written to:\n{output_file}\n")
            print("Summary Scorecard Preview:\n")
            print("\n".join(report.split("\n")[:30]))
        except Exception as e:
            print(f"❌ Error running healthcheck audit: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
