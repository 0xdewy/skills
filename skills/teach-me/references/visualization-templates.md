# Visualization Templates Reference

When to load: when you need to generate a custom visualization not covered by `visualizer.py`, or when you want to understand the HTML template patterns used by the scripts.

---

## The Self-Contained HTML Pattern

All visualizations are self-contained HTML files — no server needed, no external assets except D3.js from CDN. The structure is always:

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
  <style>/* inline CSS */</style>
</head>
<body>
  <!-- header bar -->
  <div id="header">...</div>
  <!-- main canvas -->
  <div id="canvas">
    <svg id="svg"></svg>
    <div class="tooltip" id="tooltip"></div>
    <div id="legend">...</div>
  </div>
  <script>/* inline D3.js code */</script>
</body>
</html>
```

This works in any browser with no setup.

---

## Color Palette

Always use this palette for consistency:

| Token | Hex | Use |
|-------|-----|-----|
| `bg` | `#0d1117` | Page background |
| `surface` | `#161b22` | Cards, panels, header |
| `border` | `#30363d` | Borders, subtle separators |
| `text` | `#e6edf3` | Primary text |
| `muted` | `#8b949e` | Labels, secondary text |
| `cyan` | `#39d0d8` | Primary accent, Python, JS nodes |
| `purple` | `#a371f7` | Secondary accent, function nodes |
| `green` | `#56d364` | Success, Go nodes |
| `yellow` | `#e3b341` | Warning, Java nodes |
| `blue` | `#58a6ff` | Info, TypeScript nodes |
| `pink` | `#f778ba` | Tests, special nodes |
| `red` | `#f85149` | Danger, errors |

**Node fill convention**: use `color + '33'` (20% opacity) for fill, full color for stroke. Example: `fill: '#39d0d833', stroke: '#39d0d8'`.

---

## Language Colors

Always use these for language-colored nodes:

```javascript
const LANG_COLORS = {
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
  "Solidity": "#AA6746",
};
```

---

## Tooltip Pattern

Every visualization should have a floating tooltip. The CSS:

```css
.tooltip {
  position: absolute;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 12px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
  max-width: 280px;
  z-index: 100;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
```

The D3 event handlers:

```javascript
node.on('mouseover', (event, d) => {
  tooltip.style.opacity = 1;
  tooltip.innerHTML = `
    <div class="name">${d.name}</div>
    <div class="detail">${d.description}</div>`;
}).on('mousemove', event => {
  tooltip.style.left = (event.clientX + 14) + 'px';
  tooltip.style.top  = (event.clientY - 10) + 'px';
}).on('mouseout', () => {
  tooltip.style.opacity = 0;
});
```

---

## Force-Directed Graph Pattern

For any node-link diagram:

```javascript
const sim = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(links).id(d => d.id).distance(60).strength(0.3))
  .force('charge', d3.forceManyBody().strength(-180))
  .force('center', d3.forceCenter(W / 2, H / 2))
  .force('collision', d3.forceCollide(d => d.r + 4));

sim.on('tick', () => {
  linkSelection
    .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  nodeSelection.attr('transform', d => `translate(${d.x},${d.y})`);
});
```

Always add zoom + pan:

```javascript
svg.call(d3.zoom().scaleExtent([0.1, 8]).on('zoom', e => g.attr('transform', e.transform)));
```

---

## Treemap Pattern

For file size / complexity heatmaps:

```javascript
const root = d3.hierarchy(treeData)
  .sum(d => d.value || 0)
  .sort((a, b) => b.value - a.value);

d3.treemap()
  .size([W, H])
  .paddingInner(2)
  .paddingOuter(4)
  .paddingTop(18)(root);

// Each leaf has: d.x0, d.y0, d.x1, d.y1
```

---

## Calling visualizer.py from the Agent

```bash
# Generate dependency graph from explorer output
python $SKILL_DIR/scripts/explorer.py . --json > /tmp/explore.json
python $SKILL_DIR/scripts/visualizer.py /tmp/explore.json \
  --type dependency-graph \
  --output ./teach-me-session/

# Generate overview dashboard from context-infer output
python $SKILL_DIR/scripts/context-infer.py . > /tmp/context.json
python $SKILL_DIR/scripts/visualizer.py /tmp/context.json \
  --type overview \
  --output ./teach-me-session/

# Generate architecture from explorer output
python $SKILL_DIR/scripts/visualizer.py /tmp/explore.json \
  --type architecture \
  --output ./teach-me-session/

# Generate complexity heatmap
python $SKILL_DIR/scripts/visualizer.py /tmp/explore.json \
  --type complexity-heatmap \
  --output ./teach-me-session/

# Generate call graph from code-graph output
python $SKILL_DIR/scripts/code-graph.py . --type call --format json > /tmp/calls.json
python $SKILL_DIR/scripts/visualizer.py /tmp/calls.json \
  --type call-graph \
  --output ./teach-me-session/

# Prevent auto-open (for scripted use)
python $SKILL_DIR/scripts/visualizer.py /tmp/explore.json \
  --type dependency-graph \
  --no-open \
  --output ./teach-me-session/
```

---

## When to Generate Each Type

| User asks about… | Generate |
|-----------------|----------|
| "What does this do?" / first hook | `overview` |
| "How are things connected?" | `dependency-graph` |
| "What's the architecture?" | `architecture` |
| "Where is the most code?" / hotspots | `complexity-heatmap` |
| "What calls what?" | `call-graph` |
| "How has this evolved?" | `timeline` |
| Any concept you're teaching | Any type that illuminates it |

---

## Building Custom One-Off Visualizations

If none of the built-in types fit, write inline HTML directly. Template:

```python
html = f"""<!DOCTYPE html>
<html><head>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>
  body {{ background: #0d1117; color: #e6edf3; font-family: system-ui; margin: 0; }}
  /* your styles */
</style>
</head><body>
<h2 style="padding:16px;color:#39d0d8">{concept_name}</h2>
<svg id="svg"></svg>
<script>
  const data = {json_data};
  // your D3 code
</script>
</body></html>"""

Path("./teach-me-session/custom.html").write_text(html)
subprocess.run(["xdg-open", "./teach-me-session/custom.html"])
```

Always output to `./teach-me-session/` and auto-open.
