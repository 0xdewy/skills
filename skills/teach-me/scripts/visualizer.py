#!/usr/bin/env python3
"""
visualizer.py — Generate beautiful self-contained HTML visualizations from JSON data.

Accepts output from explorer.py, code-graph.py, or context-infer.py.
Produces interactive D3.js HTML files saved to an output directory.
Auto-opens the generated file after creation.

Usage:
    python visualizer.py <input.json> --type dependency-graph --output ./teach-me-session/
    python visualizer.py <input.json> --type architecture --output ./teach-me-session/
    python visualizer.py <input.json> --type complexity-heatmap --output ./teach-me-session/
    python visualizer.py <input.json> --type call-graph --output ./teach-me-session/
    python visualizer.py <input.json> --type timeline --output ./teach-me-session/
    python visualizer.py <input.json> --type overview --title "My Project" --output ./teach-me-session/

Types:
    dependency-graph    Interactive force-directed module/file graph
    architecture        Layered hierarchy diagram
    complexity-heatmap  Treemap of file sizes and complexity
    call-graph          Directed call graph with arrows
    timeline            Git activity timeline
    overview            Multi-panel synthesis dashboard
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime


# ─── Color palette ────────────────────────────────────────────────────────────
COLORS = {
    "bg": "#0d1117",
    "surface": "#161b22",
    "border": "#30363d",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "cyan": "#39d0d8",
    "purple": "#a371f7",
    "green": "#56d364",
    "yellow": "#e3b341",
    "red": "#f85149",
    "orange": "#d29922",
    "blue": "#58a6ff",
    "pink": "#f778ba",
}

LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Java": "#b07219",
    "Kotlin": "#A97BFF",
    "Ruby": "#701516",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Swift": "#ffac45",
    "PHP": "#4F5D95",
    "Solidity": "#AA6746",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
}


def open_file(path: str):
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", path], check=False)
        else:
            os.startfile(path)
    except Exception:
        print(f"Could not auto-open {path}. Open it manually in your browser.", file=sys.stderr)


def save_and_open(html: str, output_dir: str, filename: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    out_path = str(Path(output_dir) / filename)
    Path(out_path).write_text(html, encoding="utf-8")
    print(f"Generated: {out_path}", file=sys.stderr)
    open_file(out_path)
    return out_path


def html_wrapper(title: str, body: str, extra_head: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
{extra_head}
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    height: 100vh;
    overflow: hidden;
  }}
  #header {{
    padding: 12px 20px;
    background: {COLORS['surface']};
    border-bottom: 1px solid {COLORS['border']};
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  #header h1 {{
    font-size: 15px;
    font-weight: 600;
    color: {COLORS['text']};
    letter-spacing: -0.3px;
  }}
  #header .subtitle {{
    font-size: 12px;
    color: {COLORS['muted']};
  }}
  #header .badge {{
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 12px;
    background: {COLORS['border']};
    color: {COLORS['muted']};
    margin-left: auto;
  }}
  #canvas {{
    width: 100vw;
    height: calc(100vh - 49px);
    position: relative;
  }}
  .tooltip {{
    position: absolute;
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s;
    max-width: 280px;
    z-index: 100;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  }}
  .tooltip .name {{ font-weight: 600; color: {COLORS['text']}; margin-bottom: 4px; font-size: 13px; }}
  .tooltip .detail {{ color: {COLORS['muted']}; line-height: 1.5; }}
  .tooltip .tag {{
    display: inline-block; margin-top: 6px;
    padding: 1px 6px; border-radius: 4px;
    font-size: 10px; font-weight: 600;
    background: {COLORS['border']}; color: {COLORS['cyan']};
  }}
  #legend {{
    position: absolute;
    bottom: 20px;
    right: 20px;
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 12px;
    z-index: 10;
  }}
  #legend h3 {{ font-size: 11px; color: {COLORS['muted']}; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; color: {COLORS['muted']}; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
  #instructions {{
    position: absolute;
    bottom: 20px;
    left: 20px;
    font-size: 11px;
    color: {COLORS['muted']};
  }}
  .link {{ stroke: {COLORS['border']}; stroke-opacity: 0.6; fill: none; }}
  .link.highlighted {{ stroke: {COLORS['cyan']}; stroke-opacity: 1; }}
  .node circle {{ stroke-width: 2; cursor: pointer; transition: r 0.2s; }}
  .node circle:hover {{ filter: brightness(1.3); }}
  .node text {{
    font-size: 10px;
    fill: {COLORS['text']};
    pointer-events: none;
    text-shadow: 0 1px 3px {COLORS['bg']};
  }}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ─── Dependency Graph ─────────────────────────────────────────────────────────

def build_dependency_graph(data: dict, title: str) -> str:
    # Parse explorer.py output or context-infer.py output
    files = []
    links = []

    if "files" in data and isinstance(data["files"], list):
        raw_files = data["files"]
        if raw_files and isinstance(raw_files[0], str):
            # context-infer.py format: list of paths
            files = [{"id": f, "lines": 100, "lang": "Unknown"} for f in raw_files[:60]]
        else:
            # explorer.py format: list of dicts
            for f in raw_files[:60]:
                files.append({
                    "id": f.get("path", f.get("id", "?")),
                    "lines": f.get("lines", 50),
                    "lang": f.get("lang", "Unknown"),
                })
    elif "nodes" in data:
        # graph format
        files = data["nodes"][:60]
        links = data.get("edges", data.get("links", []))[:200]

    if not files:
        files = [{"id": "no data", "lines": 1, "lang": "Unknown"}]

    # build directory-based clusters for links if none provided
    if not links:
        dir_groups: dict = {}
        for f in files:
            d = str(Path(f["id"]).parent)
            dir_groups.setdefault(d, []).append(f["id"])
        for members in dir_groups.values():
            for i in range(len(members) - 1):
                links.append({"source": members[i], "target": members[i + 1]})

    nodes_js = json.dumps(files)
    links_js = json.dumps(links)
    lang_colors_js = json.dumps(LANG_COLORS)

    body = f"""
<div id="header">
  <h1>{title}</h1>
  <span class="subtitle">Dependency Graph</span>
  <span class="badge" id="stats">Loading…</span>
</div>
<div id="canvas">
  <svg id="svg" width="100%" height="100%">
    <defs>
      <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
        <path d="M0,0 L0,6 L8,3 z" fill="{COLORS['muted']}"/>
      </marker>
    </defs>
    <g id="zoom-group"></g>
  </svg>
  <div class="tooltip" id="tooltip"></div>
  <div id="legend">
    <h3>Languages</h3>
    <div id="legend-items"></div>
  </div>
  <div id="instructions">Scroll to zoom · Drag to pan · Click node to highlight</div>
</div>

<script>
const rawNodes = {nodes_js};
const rawLinks = {links_js};
const LANG_COLORS = {lang_colors_js};
const DEFAULT_COLOR = "{COLORS['cyan']}";

const nodeMap = {{}};
rawNodes.forEach(n => {{ nodeMap[n.id] = n; }});

const nodes = rawNodes.map(n => ({{
  ...n,
  r: Math.max(5, Math.min(22, Math.sqrt(n.lines || 50) * 1.4)),
  color: LANG_COLORS[n.lang] || DEFAULT_COLOR,
}}));

const links = rawLinks.map(l => ({{
  source: l.source,
  target: l.target,
}})). filter(l => nodeMap[l.source] && nodeMap[l.target]);

// Legend
const langs = [...new Set(nodes.map(n => n.lang))].filter(l => l !== 'Unknown');
const legendEl = document.getElementById('legend-items');
langs.forEach(lang => {{
  const c = LANG_COLORS[lang] || DEFAULT_COLOR;
  legendEl.innerHTML += `<div class="legend-item"><div class="legend-dot" style="background:${{c}}"></div>${{lang}}</div>`;
}});

document.getElementById('stats').textContent = `${{nodes.length}} files · ${{links.length}} links`;

const svg = d3.select('#svg');
const g = svg.select('#zoom-group');
const W = document.getElementById('canvas').clientWidth;
const H = document.getElementById('canvas').clientHeight;

svg.call(d3.zoom().scaleExtent([0.1, 8]).on('zoom', e => g.attr('transform', e.transform)));

const sim = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(links).id(d => d.id).distance(60).strength(0.3))
  .force('charge', d3.forceManyBody().strength(-180))
  .force('center', d3.forceCenter(W / 2, H / 2))
  .force('collision', d3.forceCollide(d => d.r + 4));

const link = g.append('g').selectAll('line')
  .data(links).join('line')
  .attr('class', 'link')
  .attr('stroke-width', 1);

const node = g.append('g').selectAll('g')
  .data(nodes).join('g')
  .attr('class', 'node')
  .call(d3.drag()
    .on('start', (e, d) => {{ if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
    .on('drag', (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
    .on('end', (e, d) => {{ if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }}));

node.append('circle')
  .attr('r', d => d.r)
  .attr('fill', d => d.color + '33')
  .attr('stroke', d => d.color);

node.append('text')
  .attr('dy', d => d.r + 12)
  .attr('text-anchor', 'middle')
  .text(d => d.id.split('/').pop().replace(/\\.(py|js|ts|go|rs|java|rb|cpp|c|h)$/, ''))
  .style('font-size', d => d.r > 14 ? '11px' : '9px');

const tooltip = document.getElementById('tooltip');

node.on('mouseover', (e, d) => {{
  tooltip.style.opacity = 1;
  tooltip.innerHTML = `
    <div class="name">${{d.id.split('/').pop()}}</div>
    <div class="detail">${{d.id}}</div>
    <div class="detail">${{(d.lines || 0).toLocaleString()}} lines</div>
    <span class="tag">${{d.lang}}</span>`;
}}).on('mousemove', e => {{
  tooltip.style.left = (e.clientX + 14) + 'px';
  tooltip.style.top = (e.clientY - 10) + 'px';
}}).on('mouseout', () => {{ tooltip.style.opacity = 0; }});

let selected = null;
node.on('click', (e, d) => {{
  if (selected === d.id) {{
    selected = null;
    link.attr('class', 'link');
    node.style('opacity', 1);
  }} else {{
    selected = d.id;
    const connected = new Set([d.id]);
    links.forEach(l => {{
      if (l.source.id === d.id) connected.add(l.target.id);
      if (l.target.id === d.id) connected.add(l.source.id);
    }});
    link.attr('class', l =>
      (l.source.id === d.id || l.target.id === d.id) ? 'link highlighted' : 'link');
    node.style('opacity', n => connected.has(n.id) ? 1 : 0.15);
  }}
}});

sim.on('tick', () => {{
  link
    .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
}});
</script>"""

    return html_wrapper(title, body)


# ─── Complexity Heatmap (Treemap) ─────────────────────────────────────────────

def build_complexity_heatmap(data: dict, title: str) -> str:
    files = []
    if "files" in data:
        raw = data["files"]
        if raw and isinstance(raw[0], str):
            files = [{"id": f, "lines": 100, "lang": "Unknown"} for f in raw[:80]]
        else:
            for f in raw[:80]:
                files.append({"id": f.get("path", "?"), "lines": f.get("lines", 50), "lang": f.get("lang", "Unknown")})

    if not files:
        files = [{"id": "no data", "lines": 1, "lang": "Unknown"}]

    # build tree structure by directory
    tree: dict = {"name": "root", "children": {}}
    for f in files:
        parts = Path(f["id"]).parts
        node = tree["children"]
        for part in parts[:-1]:
            node = node.setdefault(part, {"name": part, "children": {}})["children"]  # type: ignore
        leaf = parts[-1]
        node[leaf] = {"name": leaf, "value": max(1, f["lines"]), "lang": f["lang"], "path": f["id"]}

    def dictify(d, name):
        children = []
        for k, v in d.items():
            if "children" in v:
                child = dictify(v["children"], k)
                if child:
                    children.append(child)
            else:
                children.append({"name": v["name"], "value": v["value"], "lang": v.get("lang", "Unknown"), "path": v.get("path", k)})
        if not children:
            return None
        return {"name": name, "children": children}

    tree_data = dictify(tree["children"], title or "root")
    tree_js = json.dumps(tree_data)
    lang_colors_js = json.dumps(LANG_COLORS)

    body = f"""
<div id="header">
  <h1>{title}</h1>
  <span class="subtitle">Complexity Heatmap</span>
  <span class="badge">Node size = lines of code</span>
</div>
<div id="canvas">
  <svg id="svg" width="100%" height="100%"></svg>
  <div class="tooltip" id="tooltip"></div>
  <div id="legend">
    <h3>Languages</h3>
    <div id="legend-items"></div>
  </div>
  <div id="instructions">Hover for details</div>
</div>

<script>
const treeData = {tree_js};
const LANG_COLORS = {lang_colors_js};
const DEFAULT_COLOR = "{COLORS['purple']}";

const W = document.getElementById('canvas').clientWidth;
const H = document.getElementById('canvas').clientHeight;

const svg = d3.select('#svg').attr('width', W).attr('height', H);

const root = d3.hierarchy(treeData).sum(d => d.value || 0).sort((a, b) => b.value - a.value);
d3.treemap().size([W, H]).paddingInner(2).paddingOuter(4).paddingTop(18)(root);

const langs = [...new Set(root.leaves().map(d => d.data.lang))];
const legendEl = document.getElementById('legend-items');
langs.forEach(lang => {{
  const c = LANG_COLORS[lang] || DEFAULT_COLOR;
  legendEl.innerHTML += `<div class="legend-item"><div class="legend-dot" style="background:${{c}}"></div>${{lang}}</div>`;
}});

const cell = svg.selectAll('g').data(root.leaves()).join('g')
  .attr('transform', d => `translate(${{d.x0}},${{d.y0}})`);

cell.append('rect')
  .attr('width', d => Math.max(0, d.x1 - d.x0))
  .attr('height', d => Math.max(0, d.y1 - d.y0))
  .attr('fill', d => (LANG_COLORS[d.data.lang] || DEFAULT_COLOR) + '44')
  .attr('stroke', d => LANG_COLORS[d.data.lang] || DEFAULT_COLOR)
  .attr('stroke-width', 1)
  .style('cursor', 'pointer');

cell.append('clipPath').attr('id', (d, i) => `clip-${{i}}`).append('rect')
  .attr('width', d => Math.max(0, d.x1 - d.x0))
  .attr('height', d => Math.max(0, d.y1 - d.y0));

cell.append('text')
  .attr('clip-path', (d, i) => `url(#clip-${{i}})`)
  .attr('x', 4).attr('y', 13)
  .style('font-size', '10px')
  .style('fill', '{COLORS['text']}')
  .text(d => d.data.name);

const tooltip = document.getElementById('tooltip');
cell.on('mouseover', (e, d) => {{
  tooltip.style.opacity = 1;
  tooltip.innerHTML = `
    <div class="name">${{d.data.name}}</div>
    <div class="detail">${{d.data.path || d.data.name}}</div>
    <div class="detail">${{(d.data.value || 0).toLocaleString()}} lines</div>
    <span class="tag">${{d.data.lang || 'Unknown'}}</span>`;
}}).on('mousemove', e => {{
  tooltip.style.left = (e.clientX + 14) + 'px';
  tooltip.style.top = (e.clientY - 10) + 'px';
}}).on('mouseout', () => {{ tooltip.style.opacity = 0; }});

// Directory labels
const dirs = root.descendants().filter(d => d.depth === 1 && d.children);
svg.selectAll('.dir-label').data(dirs).join('text')
  .attr('class', 'dir-label')
  .attr('x', d => d.x0 + 4)
  .attr('y', d => d.y0 + 13)
  .style('font-size', '11px')
  .style('font-weight', '600')
  .style('fill', '{COLORS['muted']}')
  .text(d => d.data.name + '/');
</script>"""

    return html_wrapper(title, body)


# ─── Architecture Diagram ─────────────────────────────────────────────────────

def build_architecture(data: dict, title: str) -> str:
    # Build a layer-based diagram from file structure
    files = []
    if "files" in data:
        raw = data["files"]
        if raw and isinstance(raw[0], str):
            files = [{"id": f, "lines": 100} for f in raw[:60]]
        else:
            files = [{"id": f.get("path", "?"), "lines": f.get("lines", 50)} for f in raw[:60]]

    # Group files into layers based on directory name heuristics
    layer_patterns = [
        ("API / Interface", ["api", "routes", "handler", "controller", "endpoint", "view", "http"]),
        ("Service / Logic", ["service", "business", "logic", "processor", "worker", "job"]),
        ("Data / Storage", ["db", "database", "model", "repo", "repository", "store", "dao", "schema"]),
        ("Utilities", ["util", "helper", "lib", "common", "shared", "tool"]),
        ("Config / Init", ["config", "setting", "env", "init", "setup", "main", "app", "cmd"]),
        ("Tests", ["test", "spec", "mock", "fixture"]),
    ]

    layers: dict = {name: [] for name, _ in layer_patterns}
    layers["Other"] = []

    for f in files:
        path_lower = f["id"].lower()
        placed = False
        for name, keywords in layer_patterns:
            if any(k in path_lower for k in keywords):
                layers[name].append(f)
                placed = True
                break
        if not placed:
            layers["Other"].append(f)

    # Build D3 hierarchical data
    layer_data = [
        {"name": name, "count": len(items), "files": [i["id"].split("/")[-1] for i in items[:5]]}
        for name, items in layers.items()
        if items
    ]

    layer_js = json.dumps(layer_data)
    layer_colors = [COLORS["cyan"], COLORS["purple"], COLORS["green"], COLORS["yellow"], COLORS["blue"], COLORS["pink"], COLORS["muted"]]

    body = f"""
<div id="header">
  <h1>{title}</h1>
  <span class="subtitle">Architecture Overview</span>
  <span class="badge">{len(files)} files</span>
</div>
<div id="canvas">
  <svg id="svg" width="100%" height="100%"></svg>
  <div class="tooltip" id="tooltip"></div>
  <div id="instructions">Hover for details</div>
</div>

<script>
const layers = {layer_js};
const COLORS = {json.dumps(layer_colors)};

const W = document.getElementById('canvas').clientWidth;
const H = document.getElementById('canvas').clientHeight;
const svg = d3.select('#svg');
const margin = {{ top: 40, right: 60, bottom: 40, left: 60 }};
const gW = W - margin.left - margin.right;
const gH = H - margin.top - margin.bottom;

const g = svg.append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);

const boxH = Math.min(90, (gH - (layers.length - 1) * 20) / layers.length);
const boxW = Math.min(500, gW * 0.7);
const startX = (gW - boxW) / 2;

// Draw connecting arrows
for (let i = 0; i < layers.length - 1; i++) {{
  const y1 = i * (boxH + 20) + boxH;
  const y2 = (i + 1) * (boxH + 20);
  g.append('line')
    .attr('x1', startX + boxW / 2).attr('y1', y1)
    .attr('x2', startX + boxW / 2).attr('y2', y2)
    .attr('stroke', '{COLORS['border']}')
    .attr('stroke-width', 2)
    .attr('marker-end', 'url(#arrow-arch)');
}}

svg.append('defs').append('marker')
  .attr('id', 'arrow-arch')
  .attr('markerWidth', 8).attr('markerHeight', 8)
  .attr('refX', 4).attr('refY', 3)
  .attr('orient', 'auto')
  .append('path').attr('d', 'M0,0 L0,6 L8,3 z')
  .attr('fill', '{COLORS['border']}');

const tooltip = document.getElementById('tooltip');

layers.forEach((layer, i) => {{
  const y = i * (boxH + 20);
  const color = COLORS[i % COLORS.length];

  const box = g.append('g').attr('transform', `translate(${{startX}},${{y}})`).style('cursor', 'pointer');

  box.append('rect')
    .attr('width', boxW).attr('height', boxH)
    .attr('rx', 8)
    .attr('fill', color + '22')
    .attr('stroke', color)
    .attr('stroke-width', 1.5);

  box.append('text')
    .attr('x', 16).attr('y', 26)
    .style('font-size', '14px').style('font-weight', '600')
    .style('fill', color)
    .text(layer.name);

  box.append('text')
    .attr('x', 16).attr('y', 44)
    .style('font-size', '11px').style('fill', '{COLORS['muted']}')
    .text(layer.files.join('  ·  ').substring(0, 60) + (layer.files.length > 5 ? ' …' : ''));

  box.append('text')
    .attr('x', boxW - 12).attr('y', 26)
    .attr('text-anchor', 'end')
    .style('font-size', '20px').style('font-weight', '700')
    .style('fill', color + 'aa')
    .text(layer.count);

  box.on('mouseover', e => {{
    tooltip.style.opacity = 1;
    tooltip.innerHTML = `
      <div class="name">${{layer.name}}</div>
      <div class="detail">${{layer.count}} file${{layer.count !== 1 ? 's' : ''}}</div>
      <div class="detail">${{layer.files.join(', ')}}</div>`;
  }}).on('mousemove', e => {{
    tooltip.style.left = (e.clientX + 14) + 'px';
    tooltip.style.top = (e.clientY - 10) + 'px';
  }}).on('mouseout', () => {{ tooltip.style.opacity = 0; }});
}});
</script>"""

    return html_wrapper(title, body)


# ─── Overview / Dashboard ─────────────────────────────────────────────────────

def build_overview(data: dict, title: str) -> str:
    topic = data.get("topic", title)
    hook = data.get("hook_sentence", "")
    facts = data.get("interesting_facts", [])
    lang_breakdown = data.get("lang_breakdown", {})
    file_count = data.get("file_count", 0)
    total_lines = data.get("total_lines", 0)
    readme = data.get("readme_summary", "")
    git = data.get("git_activity", "")
    files = data.get("files", [])[:20]

    facts_html = "".join(f"<li>{f}</li>" for f in facts)
    breakdown_js = json.dumps(list(lang_breakdown.items())[:8])
    files_html = "".join(f"<div class='file-item'>{f}</div>" for f in files)
    commits = [l for l in git.splitlines() if l.strip()][:6]
    commits_html = "".join(f"<div class='commit'>{c}</div>" for c in commits)

    lang_colors_js = json.dumps(LANG_COLORS)

    body = f"""
<div id="header">
  <h1>{title}</h1>
  <span class="subtitle">Overview Dashboard</span>
  <span class="badge">{file_count} files · {total_lines:,} lines</span>
</div>
<div id="canvas" style="overflow-y:auto; padding: 24px; display:grid; grid-template-columns: 1fr 1fr; grid-template-rows: auto auto; gap: 20px;">

  <div class="panel" style="grid-column: 1 / -1;">
    <div class="panel-title">Hook</div>
    <div style="font-size:15px; color:{COLORS['text']}; font-style:italic; line-height:1.6;">"{hook}"</div>
    {f'<div style="font-size:12px; color:{COLORS["muted"]}; margin-top:10px; line-height:1.6;">{readme}</div>' if readme else ''}
  </div>

  <div class="panel">
    <div class="panel-title">Key Facts</div>
    <ul style="list-style:none; padding:0;">
      {facts_html}
    </ul>
  </div>

  <div class="panel">
    <div class="panel-title">Language Breakdown</div>
    <svg id="lang-chart" width="100%" height="180"></svg>
  </div>

  {f'<div class="panel"><div class="panel-title">Recent Commits</div><div class="commits">{commits_html}</div></div>' if commits else ''}

  <div class="panel" style="{'' if commits else 'grid-column: 1 / -1;'}">
    <div class="panel-title">Top Files by Size</div>
    <div class="file-list">{files_html}</div>
  </div>

</div>

<style>
  #canvas {{ background: {COLORS['bg']}; }}
  .panel {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 18px 20px;
  }}
  .panel-title {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: {COLORS['muted']};
    margin-bottom: 12px;
  }}
  ul li {{
    font-size: 13px;
    color: {COLORS['text']};
    padding: 4px 0;
    border-bottom: 1px solid {COLORS['border']};
    line-height: 1.4;
  }}
  ul li:last-child {{ border-bottom: none; }}
  .commit {{
    font-size: 12px;
    color: {COLORS['muted']};
    padding: 4px 0;
    font-family: monospace;
    border-bottom: 1px solid {COLORS['border']};
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .file-item {{
    font-size: 11px;
    color: {COLORS['cyan']};
    padding: 3px 0;
    font-family: monospace;
  }}
</style>

<script>
const breakdown = {breakdown_js};
const LANG_COLORS = {lang_colors_js};
const DEFAULT_COLOR = "{COLORS['cyan']}";

const svg = d3.select('#lang-chart');
const W = document.getElementById('lang-chart').parentElement.clientWidth - 40;
const H = 170;
svg.attr('width', W).attr('height', H);

if (breakdown.length > 0) {{
  const total = breakdown.reduce((s, [,v]) => s + v, 0);
  const x = d3.scaleLinear().domain([0, total]).range([0, W - 100]);
  const barH = Math.min(22, (H - 10) / breakdown.length - 4);

  breakdown.forEach(([lang, lines], i) => {{
    const y = i * (barH + 6);
    const color = LANG_COLORS[lang] || DEFAULT_COLOR;
    const pct = Math.round(lines / total * 100);
    svg.append('rect').attr('x', 0).attr('y', y).attr('width', x(lines)).attr('height', barH)
      .attr('fill', color + '66').attr('stroke', color).attr('rx', 3);
    svg.append('text').attr('x', 6).attr('y', y + barH / 2 + 4)
      .style('font-size', '11px').style('fill', color).text(lang);
    svg.append('text').attr('x', x(lines) + 6).attr('y', y + barH / 2 + 4)
      .style('font-size', '11px').style('fill', '{COLORS['muted']}')
      .text(`${{lines.toLocaleString()}} (${{pct}}%)`);
  }});
}}
</script>"""

    return html_wrapper(title, body)


# ─── Call Graph ───────────────────────────────────────────────────────────────

def build_call_graph(data: dict, title: str) -> str:
    # Expects output from code-graph.py (nodes/edges or similar)
    nodes = []
    links = []

    if "nodes" in data:
        for n in data["nodes"][:50]:
            nodes.append({"id": str(n.get("id", n)) , "label": str(n.get("label", n.get("id", n)))})
        for e in data.get("edges", [])[:150]:
            links.append({"source": str(e.get("source", e.get("from", ""))), "target": str(e.get("target", e.get("to", "")))})
    elif "calls" in data:
        call_set = set()
        for c in data["calls"][:150]:
            caller = c.get("caller", "")
            callee = c.get("callee", "")
            if caller and callee:
                call_set.add(caller)
                call_set.add(callee)
                links.append({"source": caller, "target": callee})
        nodes = [{"id": n, "label": n.split(".")[-1]} for n in call_set]

    if not nodes:
        nodes = [{"id": "no data", "label": "no data"}]

    nodes_js = json.dumps(nodes)
    links_js = json.dumps(links)

    body = f"""
<div id="header">
  <h1>{title}</h1>
  <span class="subtitle">Call Graph</span>
  <span class="badge" id="stats">{len(nodes)} functions · {len(links)} calls</span>
</div>
<div id="canvas">
  <svg id="svg" width="100%" height="100%">
    <defs>
      <marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
        <path d="M0,0 L0,6 L8,3 z" fill="{COLORS['cyan']}88"/>
      </marker>
    </defs>
    <g id="zoom-group"></g>
  </svg>
  <div class="tooltip" id="tooltip"></div>
  <div id="instructions">Scroll to zoom · Drag to pan · Click to highlight</div>
</div>

<script>
const rawNodes = {nodes_js};
const rawLinks = {links_js};

const nodeMap = {{}};
rawNodes.forEach(n => {{ nodeMap[n.id] = n; }});
const validLinks = rawLinks.filter(l => nodeMap[l.source] && nodeMap[l.target]);

const W = document.getElementById('canvas').clientWidth;
const H = document.getElementById('canvas').clientHeight;
const svg = d3.select('#svg');
const g = svg.select('#zoom-group');

svg.call(d3.zoom().scaleExtent([0.05, 8]).on('zoom', e => g.attr('transform', e.transform)));

const sim = d3.forceSimulation(rawNodes)
  .force('link', d3.forceLink(validLinks).id(d => d.id).distance(80).strength(0.5))
  .force('charge', d3.forceManyBody().strength(-200))
  .force('center', d3.forceCenter(W / 2, H / 2))
  .force('collision', d3.forceCollide(14));

const link = g.append('g').selectAll('line')
  .data(validLinks).join('line')
  .attr('class', 'link')
  .attr('stroke', '{COLORS['purple']}66')
  .attr('stroke-width', 1.5)
  .attr('marker-end', 'url(#arrow)');

const node = g.append('g').selectAll('g')
  .data(rawNodes).join('g').attr('class', 'node')
  .call(d3.drag()
    .on('start', (e, d) => {{ if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
    .on('drag', (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
    .on('end', (e, d) => {{ if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }}));

node.append('circle').attr('r', 8)
  .attr('fill', '{COLORS['purple']}33').attr('stroke', '{COLORS['purple']}');

node.append('text').attr('dy', 20).attr('text-anchor', 'middle')
  .style('font-size', '9px').text(d => d.label || d.id);

const tooltip = document.getElementById('tooltip');
node.on('mouseover', (e, d) => {{
  tooltip.style.opacity = 1;
  tooltip.innerHTML = `<div class="name">${{d.label || d.id}}</div><div class="detail">${{d.id}}</div>`;
}}).on('mousemove', e => {{
  tooltip.style.left = (e.clientX + 14) + 'px';
  tooltip.style.top = (e.clientY - 10) + 'px';
}}).on('mouseout', () => {{ tooltip.style.opacity = 0; }});

sim.on('tick', () => {{
  link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
}});
</script>"""

    return html_wrapper(title, body)


# ─── Timeline ─────────────────────────────────────────────────────────────────

def build_timeline(data: dict, title: str) -> str:
    git_activity = data.get("git_activity", "")
    commits = []
    for line in git_activity.splitlines():
        parts = line.strip().split(" ", 1)
        if len(parts) == 2:
            commits.append({"hash": parts[0], "message": parts[1]})

    if not commits:
        commits = [{"hash": "abc1234", "message": "No git history found"}]

    commits_js = json.dumps(commits[:20])

    body = f"""
<div id="header">
  <h1>{title}</h1>
  <span class="subtitle">Git Timeline</span>
  <span class="badge">{len(commits)} recent commits</span>
</div>
<div id="canvas" style="overflow-y: auto; padding: 40px 80px;">
  <div id="timeline"></div>
</div>

<style>
  .commit-row {{
    display: flex;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 24px;
    position: relative;
  }}
  .commit-row::before {{
    content: '';
    position: absolute;
    left: 19px;
    top: 24px;
    width: 2px;
    height: calc(100% + 8px);
    background: {COLORS['border']};
  }}
  .commit-row:last-child::before {{ display: none; }}
  .commit-dot {{
    width: 14px; height: 14px;
    border-radius: 50%;
    background: {COLORS['cyan']};
    border: 3px solid {COLORS['bg']};
    flex-shrink: 0;
    margin-top: 3px;
    position: relative;
    z-index: 1;
  }}
  .commit-hash {{
    font-family: monospace;
    font-size: 11px;
    color: {COLORS['muted']};
    background: {COLORS['border']};
    padding: 1px 6px;
    border-radius: 4px;
    margin-bottom: 4px;
    display: inline-block;
  }}
  .commit-message {{
    font-size: 14px;
    color: {COLORS['text']};
    line-height: 1.4;
  }}
</style>

<script>
const commits = {commits_js};
const container = document.getElementById('timeline');
commits.forEach(c => {{
  container.innerHTML += `
    <div class="commit-row">
      <div class="commit-dot"></div>
      <div>
        <span class="commit-hash">${{c.hash}}</span>
        <div class="commit-message">${{c.message}}</div>
      </div>
    </div>`;
}});
</script>"""

    return html_wrapper(title, body)


# ─── Main ─────────────────────────────────────────────────────────────────────

BUILDERS = {
    "dependency-graph": (build_dependency_graph, "dependency-graph.html"),
    "complexity-heatmap": (build_complexity_heatmap, "complexity-heatmap.html"),
    "architecture": (build_architecture, "architecture.html"),
    "call-graph": (build_call_graph, "call-graph.html"),
    "timeline": (build_timeline, "timeline.html"),
    "overview": (build_overview, "overview.html"),
}


def main():
    parser = argparse.ArgumentParser(description="Generate D3.js HTML visualizations")
    parser.add_argument("input", help="JSON input file (from explorer.py, code-graph.py, or context-infer.py)")
    parser.add_argument("--type", choices=list(BUILDERS.keys()), default="dependency-graph")
    parser.add_argument("--output", default="./teach-me-session/", help="Output directory")
    parser.add_argument("--title", default="", help="Title override")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open the file")
    args = parser.parse_args()

    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    title = args.title or data.get("topic", data.get("name", Path(args.input).stem))
    builder_fn, filename = BUILDERS[args.type]
    html = builder_fn(data, title)

    os.makedirs(args.output, exist_ok=True)
    out_path = str(Path(args.output) / filename)
    Path(out_path).write_text(html, encoding="utf-8")
    print(f"Generated: {out_path}", file=sys.stderr)

    if not args.no_open:
        open_file(out_path)

    print(out_path)  # stdout for callers


if __name__ == "__main__":
    main()
