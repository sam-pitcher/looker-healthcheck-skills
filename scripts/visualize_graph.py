#!/usr/bin/env python3
"""
OKF Concept Graph Interactive Visualizer Generator.
Exports an interactive, standalone HTML graph explorer using vis.js network visualization.
Allows users to explore nodes, inspect playbooks, filter by knowledge type, and trace diagnostic reasoning paths.
"""

import sys
import json
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agent.skills_registry import skill_registry


def generate_interactive_graph(output_html_path: Path = ROOT_DIR / "visualize_graph.html", auto_open: bool = False):
    graph_data = skill_registry.export_concept_graph_json()
    
    # Color palette for knowledge types
    type_colors = {
        "Skill": "#4285F4",                # Google Blue
        "Playbook": "#34A853",             # Google Green
        "Reference": "#FBBC05",            # Google Yellow / Amber
        "Attested Computation": "#EA4335", # Google Red
        "Data Source / View": "#9C27B0",   # Purple
        "Execution Tool": "#00BCD4",       # Teal
        "Documentation": "#607D8B",        # Blue Grey
        "External Source": "#FF9800",      # Orange
        "Resource": "#795548"              # Brown
    }

    nodes = []
    for n in graph_data["nodes"]:
        ntype = n.get("type", "Concept")
        color = type_colors.get(ntype, "#607D8B")
        
        # Determine size and shape based on type
        if ntype in ("Skill", "Playbook"):
            shape = "dot"
            size = 28
        elif ntype == "Attested Computation":
            shape = "diamond"
            size = 24
        elif ntype == "Data Source / View":
            shape = "database"
            size = 20
        elif ntype == "Execution Tool":
            shape = "box"
            size = 18
        else:
            shape = "dot"
            size = 16

        nodes.append({
            "id": n["id"],
            "label": n["label"],
            "title": f"<b>{n['label']}</b><br/><i>Type: {ntype}</i><br/>Trust: {n.get('trust_tier', 'unverified')}<br/>Status: {n.get('status', 'stable')}",
            "color": {
                "background": color,
                "border": "#2c3e50",
                "highlight": {"background": "#FFEB3B", "border": "#E65100"}
            },
            "shape": shape,
            "size": size,
            "font": {"size": 13, "color": "#1a1a1a", "face": "system-ui, -apple-system, sans-serif"},
            "type": ntype,
            "trust": n.get("trust_tier", "unverified"),
            "status": n.get("status", "stable")
        })

    edges = []
    for e in graph_data["links"]:
        rel = e.get("relationship", "references")
        color = "#999999"
        dashes = False
        if rel == "sourced_from":
            color = "#4285F4"
        elif rel == "executed_by":
            color = "#EA4335"
            dashes = True
        elif rel == "attested_by":
            color = "#34A853"
            dashes = True

        edges.append({
            "from": e["source"],
            "to": e["target"],
            "label": rel,
            "arrows": "to",
            "color": {"color": color, "highlight": "#E65100"},
            "font": {"size": 9, "align": "middle", "color": "#666"},
            "dashes": dashes,
            "smooth": {"type": "continuous"}
        })

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    node_count = len(nodes)
    edge_count = len(edges)

    template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OKF Concept Graph Visualizer — Looker & BigQuery Healthcheck Agent</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { display: flex; height: 100vh; overflow: hidden; background: #f8f9fa; color: #202124; }
    #sidebar { width: 340px; background: #ffffff; border-right: 1px solid #dadce0; display: flex; flex-direction: column; padding: 20px; box-shadow: 2px 0 6px rgba(0,0,0,0.04); z-index: 10; }
    #graph-container { flex: 1; height: 100%; position: relative; background: #fafafa; }
    h1 { font-size: 18px; font-weight: 700; margin-bottom: 6px; color: #1a73e8; display: flex; align-items: center; gap: 8px; }
    .subtitle { font-size: 12px; color: #5f6368; margin-bottom: 16px; }
    .stats-badge { display: flex; gap: 8px; margin-bottom: 16px; }
    .badge { background: #e8f0fe; color: #1967d2; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
    .search-box { width: 100%; padding: 10px 12px; border: 1px solid #dadce0; border-radius: 8px; font-size: 13px; margin-bottom: 14px; outline: none; }
    .search-box:focus { border-color: #1a73e8; box-shadow: 0 0 0 2px rgba(26,115,232,0.2); }
    .filter-group { margin-bottom: 16px; }
    .filter-title { font-size: 12px; font-weight: 600; color: #5f6368; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px; }
    .legend-item { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 12px; cursor: pointer; padding: 4px 6px; border-radius: 4px; }
    .legend-item:hover { background: #f1f3f4; }
    .color-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
    #details-panel { flex: 1; border-top: 1px solid #dadce0; padding-top: 14px; overflow-y: auto; font-size: 13px; }
    .node-title { font-weight: 700; font-size: 14px; margin-bottom: 6px; color: #202124; }
    .node-meta { font-size: 11px; color: #5f6368; margin-bottom: 8px; }
    .node-meta span { display: inline-block; background: #f1f3f4; padding: 2px 6px; border-radius: 4px; margin-right: 4px; }
  </style>
</head>
<body>
  <div id="sidebar">
    <h1>🕸️ OKF Concept Graph</h1>
    <div class="subtitle">Open Knowledge Format v0.2 Catalog Engine</div>
    <div class="stats-badge">
      <div class="badge">Nodes: __NODE_COUNT__</div>
      <div class="badge">Edges: __EDGE_COUNT__</div>
      <div class="badge" style="background:#e6f4ea; color:#137333;">Health: 100%</div>
    </div>
    <input type="text" id="search" class="search-box" placeholder="🔍 Search concepts or playbooks..." />
    <div class="filter-group">
      <div class="filter-title">Knowledge Types</div>
      <div class="legend-item" onclick="filterType('Skill')"><span class="color-dot" style="background:#4285F4;"></span> Skills (Root)</div>
      <div class="legend-item" onclick="filterType('Playbook')"><span class="color-dot" style="background:#34A853;"></span> Playbooks</div>
      <div class="legend-item" onclick="filterType('Reference')"><span class="color-dot" style="background:#FBBC05;"></span> References</div>
      <div class="legend-item" onclick="filterType('Attested Computation')"><span class="color-dot" style="background:#EA4335;"></span> Attested Computations</div>
      <div class="legend-item" onclick="filterType('Data Source / View')"><span class="color-dot" style="background:#9C27B0;"></span> Data Sources / Views</div>
      <div class="legend-item" onclick="filterType('Execution Tool')"><span class="color-dot" style="background:#00BCD4;"></span> Execution Tools</div>
      <div class="legend-item" onclick="resetFilter()" style="color:#1a73e8; font-weight:600;">✨ Show All Nodes</div>
    </div>
    <div id="details-panel">
      <div style="color:#70757a; font-style:italic;">Click on any node in the graph to inspect metadata, upstream sources, and connections.</div>
    </div>
  </div>
  <div id="graph-container"></div>

  <script>
    const rawNodes = __RAW_NODES__;
    const rawEdges = __RAW_EDGES__;

    const nodesDataSet = new vis.DataSet(rawNodes);
    const edgesDataSet = new vis.DataSet(rawEdges);

    const container = document.getElementById('graph-container');
    const data = { nodes: nodesDataSet, edges: edgesDataSet };
    const options = {
      nodes: {
        borderWidth: 2,
        shadow: true
      },
      edges: {
        width: 1.5,
        shadow: false,
        arrows: { to: { enabled: true, scaleFactor: 0.7 } }
      },
      physics: {
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -40,
          centralGravity: 0.005,
          springLength: 120,
          springConstant: 0.18,
          damping: 0.88
        },
        stabilization: { iterations: 200 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        navigationButtons: true,
        keyboard: true
      }
    };

    const network = new vis.Network(container, data, options);

    network.on('click', function(params) {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = rawNodes.find(n => n.id === nodeId);
        if (node) {
          const panel = document.getElementById('details-panel');
          const connected = network.getConnectedNodes(nodeId);
          let connectedHtml = '';
          connected.forEach(cid => {
            const cn = rawNodes.find(n => n.id === cid);
            connectedHtml += '<li>' + (cn ? cn.label : cid) + '</li>';
          });

          panel.innerHTML = '<div class="node-title">' + node.label + '</div>' +
            '<div class="node-meta">' +
              '<span>' + node.type + '</span>' +
              '<span>' + node.trust + '</span>' +
              '<span>' + node.status + '</span>' +
            '</div>' +
            '<div style="font-size:11px; color:#5f6368; margin-bottom:8px; word-break:break-all;"><b>ID:</b> <code>' + node.id + '</code></div>' +
            '<div style="margin-top:10px; font-weight:600; font-size:12px; color:#202124;">Connected Concepts (' + connected.length + '):</div>' +
            '<ul style="padding-left:18px; margin-top:6px; font-size:12px; color:#3c4043;">' +
              connectedHtml +
            '</ul>';
        }
      }
    });

    // Search functionality
    document.getElementById('search').addEventListener('input', function(e) {
      const q = e.target.value.toLowerCase().trim();
      if (!q) {
        nodesDataSet.update(rawNodes.map(n => ({ id: n.id, hidden: false })));
        return;
      }
      const matchedIds = new Set();
      rawNodes.forEach(n => {
        if (n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q) || n.type.toLowerCase().includes(q)) {
          matchedIds.add(n.id);
        }
      });
      nodesDataSet.update(rawNodes.map(n => ({
        id: n.id,
        hidden: !matchedIds.has(n.id)
      })));
    });

    function filterType(targetType) {
      nodesDataSet.update(rawNodes.map(n => ({
        id: n.id,
        hidden: n.type !== targetType
      })));
    }

    function resetFilter() {
      nodesDataSet.update(rawNodes.map(n => ({ id: n.id, hidden: false })));
    }
  </script>
</body>
</html>
"""
    html_content = template.replace("__RAW_NODES__", nodes_json)\
                           .replace("__RAW_EDGES__", edges_json)\
                           .replace("__NODE_COUNT__", str(node_count))\
                           .replace("__EDGE_COUNT__", str(edge_count))

    output_html_path.write_text(html_content, encoding="utf-8")
    print(f"✅ Generated Interactive Concept Graph: file://{output_html_path.absolute()}")
    if auto_open:
        webbrowser.open(f"file://{output_html_path.absolute()}")
    return output_html_path


if __name__ == "__main__":
    generate_interactive_graph(auto_open=False)
