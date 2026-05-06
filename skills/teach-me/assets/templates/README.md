# 3D Code Map Guide

This directory contains templates and instructions for creating 3D visualizations of codebases.

## Concept

A 3D code map represents a codebase spatially:
- **X-axis**: File/module clustering (files in same directory are close)
- **Y-axis (height)**: Complexity or size (lines of code, function count)
- **Z-axis**: Layer/namespace grouping
- **Color**: Category (core logic, utilities, tests, config)

## Blender Template Structure

When using `blender-mcp`, you can generate 3D code maps with these principles:

1. **Each module/package** = A 3D primitive (cube, sphere)
2. **Size** = Proportional to lines of code or complexity metrics
3. **Position** = Clustered by dependency (highly coupled modules near each other)
4. **Color** = Category coding
   - Blue: Core business logic
   - Green: Utilities/helpers
   - Orange: External integrations
   - Red: Tests
   - Gray: Configuration

## Quick Start

```python
# Example structure for Blender MCP
{
    "modules": [
        {"name": "core", "loc": 5000, "coupling": 0.8},
        {"name": "api", "loc": 2000, "coupling": 0.6},
        {"name": "utils", "loc": 1000, "coupling": 0.3},
    ]
}
```

## Manim Alternative

For mathematical/educational 3D animations, `manim-mcp` is better:
- Great for step-by-step animations showing how code flows
- Can animate data structures
- Good for teaching complex algorithms

## Output Formats

- **BLEND file**: Native Blender format, editable
- **GLTF/GLB**: Web-viewable 3D models
- **STL**: 3D printing (if user wants a physical model!)
- **PNG/MP4**: Static/rendered images or animations