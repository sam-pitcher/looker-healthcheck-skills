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
    <script src="https://d3js.org/d3.v7.min.js"></script>
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
            --purple: #a855f7;
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
        .badge-comp {
            display: inline-block;
            font-size: 0.62rem;
            background: rgba(245, 158, 11, 0.15);
            color: var(--yellow);
            padding: 2px 5px;
            border-radius: 4px;
            width: fit-content;
        }
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-primary);
            padding: 24px;
            overflow: hidden;
            gap: 12px;
        }
        .nav-tabs {
            display: flex;
            gap: 8px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
        }
        .nav-tab {
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-muted);
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.88rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .nav-tab.active {
            background: var(--bg-card);
            border-color: var(--border);
            color: var(--accent);
        }
        .nav-tab:hover:not(.active) {
            color: var(--text-main);
        }
        .view-pane {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            gap: 12px;
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
        /* Graph Visualizer Styles */
        .graph-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 8px 14px;
            border-radius: 8px;
            gap: 10px;
        }
        .graph-search {
            background: #0b0f19;
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.82rem;
            width: 320px;
            outline: none;
        }
        .graph-search:focus {
            border-color: var(--accent);
        }
        .graph-legend {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        .legend-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 4px;
        }
        .graph-canvas-container {
            flex: 1;
            background: #060911;
            border: 1px solid var(--border);
            border-radius: 10px;
            position: relative;
            overflow: hidden;
        }
        #graph-svg {
            width: 100%;
            height: 100%;
            display: block;
        }
        .graph-drawer {
            position: absolute;
            top: 12px;
            right: 12px;
            width: 320px;
            max-height: calc(100% - 24px);
            background: rgba(21, 30, 50, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            font-size: 0.8rem;
            display: none;
            flex-direction: column;
            gap: 8px;
            overflow-y: auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            z-index: 10;
        }
        .graph-drawer-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--accent);
        }
        .node circle {
            cursor: pointer;
            transition: stroke 0.2s, stroke-width 0.2s;
        }
        .node:hover circle {
            stroke: #fff !important;
            stroke-width: 3px !important;
        }
        .node text {
            font-family: 'Inter', sans-serif;
            font-size: 9px;
            fill: #94a3b8;
            pointer-events: none;
        }
        .link {
            stroke: #334155;
            stroke-opacity: 0.6;
            stroke-width: 1.2px;
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
        <div class="nav-tabs">
            <button class="nav-tab active" id="tab-report" onclick="switchView('report')">📄 Specification & Reports</button>
            <button class="nav-tab" id="tab-graph" onclick="switchView('graph')">🕸️ OKF Concept Graph Explorer</button>
        </div>

        <!-- View 1: Report Text -->
        <div class="view-pane" id="pane-report">
            <div class="header-sub">Model-Scoped Diagnostic Engine connected to <code>Firestore: looker-healthcheck-db</code></div>
            <div class="report-view" id="report-box">Loading latest healthcheck report...</div>
        </div>

        <!-- View 2: D3.js Force-Directed Concept Graph -->
        <div class="view-pane" id="pane-graph" style="display: none;">
            <div class="graph-toolbar">
                <input type="text" class="graph-search" id="graph-search-input" placeholder="🔍 Search concept (e.g. slot, latency, primary_key)..." oninput="filterGraph()">
                <div class="graph-legend">
                    <span><span class="legend-dot" style="background:#f59e0b;"></span>Attested Computation</span>
                    <span><span class="legend-dot" style="background:#38bdf8;"></span>Playbook</span>
                    <span><span class="legend-dot" style="background:#a855f7;"></span>Reference</span>
                    <span><span class="legend-dot" style="background:#10b981;"></span>Skill</span>
                    <span><span class="legend-dot" style="background:#64748b;"></span>Source / Tool</span>
                </div>
                <button class="nav-tab" style="padding: 4px 10px; font-size: 0.75rem;" onclick="resetGraphZoom()">⟲ Reset Zoom</button>
            </div>

            <div class="graph-canvas-container" id="graph-container">
                <svg id="graph-svg"></svg>
                <div class="graph-drawer" id="graph-drawer">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span id="drawer-type-badge" class="badge-comp">Type</span>
                        <button onclick="closeDrawer()" style="background:transparent; border:none; color:#94a3b8; cursor:pointer;">✕</button>
                    </div>
                    <div class="graph-drawer-title" id="drawer-title">Concept Title</div>
                    <div style="font-size:0.72rem; color:var(--text-muted);" id="drawer-id">id</div>
                    <div style="font-size:0.75rem; color:#cbd5e1;" id="drawer-desc">Description</div>
                    <div id="drawer-details" style="font-size:0.72rem; color:var(--text-muted); line-height:1.5;"></div>
                    <button class="btn-audit" style="padding: 6px 10px; font-size: 0.75rem; margin-top: 6px;" onclick="loadDrawerConcept()">📖 View Full Content</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let graphData = null;
        let simulation = null;
        let svgGroup = null;
        let zoomBehavior = null;
        let activeConcept = null;

        function switchView(view) {
            document.getElementById('tab-report').classList.toggle('active', view === 'report');
            document.getElementById('tab-graph').classList.toggle('active', view === 'graph');
            document.getElementById('pane-report').style.display = view === 'report' ? 'flex' : 'none';
            document.getElementById('pane-graph').style.display = view === 'graph' ? 'flex' : 'none';

            if (view === 'graph' && !graphData) {
                renderConceptGraph();
            }
        }

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
                sBox.innerHTML = data.map(s => {
                    let badgeClass = 'badge-vendor';
                    if (s.type === 'Attested Computation') badgeClass = 'badge-comp';
                    return `
                        <div class="skill-item" onclick="loadSkill('${s.name || s.id}')">
                            <strong>${s.title || s.name}</strong>
                            <span class="history-meta">${s.description || 'Looker concept'}</span>
                            <span class="${badgeClass}">${s.type}</span>
                        </div>
                    `;
                }).join('');
            } catch (e) {
                sBox.innerHTML = '<div style="font-size: 0.8rem; color: var(--red);">Error loading skills.</div>';
            }
        }

        async function loadDoc(auditId) {
            switchView('report');
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
            switchView('report');
            const box = document.getElementById('report-box');
            box.innerText = "Loading OKF concept " + skillName + "...";
            try {
                const res = await fetch('/api/skill?name=' + encodeURIComponent(skillName));
                const data = await res.json();
                box.innerText = data.content;
            } catch (err) {
                box.innerText = "Error loading skill: " + err;
            }
        }

        async function runAudit() {
            switchView('report');
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

        // =====================================================================
        // D3.js Interactive Concept Graph Renderer
        // =====================================================================
        function getNodeColor(type) {
            switch(type) {
                case 'Attested Computation': return '#f59e0b'; // Gold / Amber
                case 'Playbook': return '#38bdf8';            // Sky Blue
                case 'Reference': return '#a855f7';           // Purple
                case 'Skill': return '#10b981';               // Emerald Green
                case 'Technical Design Document': return '#ec4899'; // Pink
                case 'Data Source / View': return '#3b82f6';
                case 'Execution Tool': return '#06b6d4';
                default: return '#64748b';                    // Slate Slate
            }
        }

        async function renderConceptGraph() {
            try {
                const res = await fetch('/api/graph');
                graphData = await res.json();
                if (!graphData || !graphData.nodes) return;

                const container = document.getElementById('graph-container');
                const width = container.clientWidth || 900;
                const height = container.clientHeight || 600;

                const svg = d3.select('#graph-svg')
                    .attr('viewBox', [0, 0, width, height]);
                svg.selectAll('*').remove();

                // Arrow marker definition
                svg.append('defs').append('marker')
                    .attr('id', 'arrow')
                    .attr('viewBox', '0 -5 10 10')
                    .attr('refX', 20)
                    .attr('refY', 0)
                    .attr('markerWidth', 6)
                    .attr('markerHeight', 6)
                    .attr('orient', 'auto')
                    .append('path')
                    .attr('d', 'M0,-5L10,0L0,5')
                    .attr('fill', '#475569');

                svgGroup = svg.append('g');

                zoomBehavior = d3.zoom()
                    .scaleExtent([0.15, 4])
                    .on('zoom', (event) => {
                        svgGroup.attr('transform', event.transform);
                    });

                svg.call(zoomBehavior);

                simulation = d3.forceSimulation(graphData.nodes)
                    .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(90))
                    .force('charge', d3.forceManyBody().strength(-280))
                    .force('center', d3.forceCenter(width / 2, height / 2))
                    .force('collision', d3.forceCollide().radius(25));

                const link = svgGroup.append('g')
                    .attr('class', 'links')
                    .selectAll('line')
                    .data(graphData.links)
                    .join('line')
                    .attr('class', 'link')
                    .attr('marker-end', 'url(#arrow)');

                const node = svgGroup.append('g')
                    .attr('class', 'nodes')
                    .selectAll('g')
                    .data(graphData.nodes)
                    .join('g')
                    .attr('class', 'node')
                    .call(d3.drag()
                        .on('start', dragstarted)
                        .on('drag', dragged)
                        .on('end', dragended))
                    .on('click', (event, d) => inspectNode(d));

                node.append('circle')
                    .attr('r', d => (d.type === 'Attested Computation' || d.type === 'Playbook') ? 11 : 7)
                    .attr('fill', d => getNodeColor(d.type))
                    .attr('stroke', '#1e293b')
                    .attr('stroke-width', 2);

                node.append('text')
                    .attr('x', 14)
                    .attr('y', 3)
                    .text(d => d.label.length > 28 ? d.label.substring(0, 26) + '...' : d.label);

                simulation.on('tick', () => {
                    link
                        .attr('x1', d => d.source.x)
                        .attr('y1', d => d.source.y)
                        .attr('x2', d => d.target.x)
                        .attr('y2', d => d.target.y);

                    node
                        .attr('transform', d => `translate(${d.x},${d.y})`);
                });

            } catch (err) {
                console.error("Error rendering graph:", err);
            }
        }

        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        function resetGraphZoom() {
            if (svgGroup && zoomBehavior) {
                d3.select('#graph-svg').transition().duration(500).call(
                    zoomBehavior.transform,
                    d3.zoomIdentity
                );
            }
        }

        function filterGraph() {
            const query = document.getElementById('graph-search-input').value.toLowerCase().trim();
            d3.selectAll('.node circle').each(function(d) {
                const match = !query || d.label.toLowerCase().includes(query) || (d.type && d.type.toLowerCase().includes(query)) || d.id.toLowerCase().includes(query);
                d3.select(this)
                    .attr('opacity', match ? 1 : 0.15)
                    .attr('stroke', match && query ? '#38bdf8' : '#1e293b')
                    .attr('stroke-width', match && query ? 4 : 2);
            });
            d3.selectAll('.node text').attr('opacity', function(d) {
                return (!query || d.label.toLowerCase().includes(query) || d.id.toLowerCase().includes(query)) ? 1 : 0.15;
            });
            d3.selectAll('.link').attr('stroke-opacity', query ? 0.1 : 0.6);
        }

        function inspectNode(nodeData) {
            activeConcept = nodeData;
            const drawer = document.getElementById('graph-drawer');
            drawer.style.display = 'flex';
            document.getElementById('drawer-title').innerText = nodeData.label;
            document.getElementById('drawer-type-badge').innerText = nodeData.type || 'Concept';
            document.getElementById('drawer-type-badge').style.background = getNodeColor(nodeData.type) + '25';
            document.getElementById('drawer-type-badge').style.color = getNodeColor(nodeData.type);
            document.getElementById('drawer-id').innerText = nodeData.id;
            document.getElementById('drawer-desc').innerText = "Trust Tier: " + (nodeData.trust_tier || 'unverified') + (nodeData.runtime ? " | Runtime: " + nodeData.runtime : "");

            // Find neighbors
            const neighbors = graphData.links
                .filter(l => l.source.id === nodeData.id || l.target.id === nodeData.id)
                .map(l => (l.source.id === nodeData.id ? '➔ ' + l.relationship + ' : ' + l.target.label : '⬅ ' + l.relationship + ' : ' + l.source.label));

            document.getElementById('drawer-details').innerHTML = "<strong>Semantic Connections (" + neighbors.length + "):</strong><br/>" +
                (neighbors.length ? neighbors.slice(0, 6).join('<br/>') : 'No direct neighbors');
        }

        function closeDrawer() {
            document.getElementById('graph-drawer').style.display = 'none';
        }

        function loadDrawerConcept() {
            if (activeConcept) {
                loadSkill(activeConcept.id);
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
        elif parsed.path == "/api/graph":
            query = urllib.parse.parse_qs(parsed.query)
            cid = query.get("concept", [None])[0]
            if cid:
                related = skill_registry.get_related_concepts(cid)
                mermaid = skill_registry.export_concept_graph_mermaid(root_concept=cid)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"concept_id": cid, "related": related, "mermaid": mermaid}).encode("utf-8"))
            else:
                graph_data = skill_registry.export_concept_graph_json()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(graph_data).encode("utf-8"))
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
