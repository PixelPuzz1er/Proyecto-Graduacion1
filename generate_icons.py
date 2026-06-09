#!/usr/bin/env python3
import os

icons_dir = "assets/icons"
os.makedirs(icons_dir, exist_ok=True)

# AutoCAD 2026 style colors
C_LINE = "#FFFFFF"
C_DIM = "#888888"
C_BLUE = "#0078D4"
C_RED = "#FF4500"
C_GREEN = "#00FF00"
C_YELLOW = "#FFD700"

def svg_header(w=32, h=32):
    return f'<svg width="{w}" height="{h}" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" shape-rendering="geometricPrecision">\n'

def svg_footer():
    return '</svg>'

def make_grip(x, y):
    return f'<rect x="{x-2}" y="{y-2}" width="4" height="4" fill="{C_BLUE}" stroke="white" stroke-width="0.5"/>\n'

SVGS = {}

# ── DRAW PANEL ──

SVGS["line.svg"] = (
    svg_header() +
    f'<line x1="6" y1="26" x2="26" y2="6" stroke="{C_LINE}" stroke-width="2.5" stroke-linecap="round"/>\n' +
    make_grip(6, 26) + make_grip(16, 16) + make_grip(26, 6) +
    svg_footer()
)

SVGS["polyline.svg"] = (
    svg_header() +
    f'<path d="M4,28 L10,12 L22,22 L28,4" fill="none" stroke="{C_LINE}" stroke-width="2.5" stroke-linejoin="round"/>\n' +
    make_grip(4, 28) + make_grip(10, 12) + make_grip(22, 22) + make_grip(28, 4) +
    svg_footer()
)

SVGS["circle.svg"] = (
    svg_header() +
    f'<circle cx="16" cy="16" r="12" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<line x1="16" y1="2" x2="16" y2="30" stroke="{C_DIM}" stroke-width="1" stroke-dasharray="2,2"/>\n' +
    f'<line x1="2" y1="16" x2="30" y2="16" stroke="{C_DIM}" stroke-width="1" stroke-dasharray="2,2"/>\n' +
    f'<circle cx="16" cy="16" r="2" fill="{C_BLUE}"/>\n' +
    svg_footer()
)

SVGS["arc.svg"] = (
    svg_header() +
    f'<path d="M4,24 A12,12 0 0,1 28,24" fill="none" stroke="{C_LINE}" stroke-width="2.5" stroke-linecap="round"/>\n' +
    make_grip(4, 24) + make_grip(16, 12) + make_grip(28, 24) +
    svg_footer()
)

SVGS["rectangle.svg"] = (
    svg_header() +
    f'<rect x="4" y="8" width="24" height="16" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    make_grip(4, 8) + make_grip(28, 24) +
    svg_footer()
)

SVGS["polygon.svg"] = (
    svg_header() +
    f'<polygon points="16,4 28,12 24,26 8,26 4,12" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    svg_footer()
)

SVGS["ellipse.svg"] = (
    svg_header() +
    f'<ellipse cx="16" cy="16" rx="14" ry="8" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<line x1="2" y1="16" x2="30" y2="16" stroke="{C_DIM}" stroke-width="1" stroke-dasharray="2,2"/>\n' +
    make_grip(16, 16) + make_grip(30, 16) + make_grip(16, 8) +
    svg_footer()
)

SVGS["hatch.svg"] = (
    svg_header() +
    f'<rect x="4" y="4" width="24" height="24" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<line x1="4" y1="20" x2="20" y2="4" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<line x1="4" y1="28" x2="28" y2="4" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<line x1="12" y1="28" x2="28" y2="12" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    svg_footer()
)

# ── MODIFY PANEL ──

SVGS["move.svg"] = (
    svg_header() +
    f'<line x1="4" y1="16" x2="28" y2="16" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<line x1="16" y1="4" x2="16" y2="28" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<polygon points="28,16 22,12 22,20" fill="{C_LINE}"/>\n' +
    f'<polygon points="4,16 10,12 10,20" fill="{C_LINE}"/>\n' +
    f'<polygon points="16,4 12,10 20,10" fill="{C_LINE}"/>\n' +
    f'<polygon points="16,28 12,22 20,22" fill="{C_LINE}"/>\n' +
    svg_footer()
)

SVGS["copy.svg"] = (
    svg_header() +
    f'<circle cx="10" cy="22" r="7" fill="none" stroke="{C_DIM}" stroke-width="1.5" stroke-dasharray="2,2"/>\n' +
    f'<circle cx="22" cy="10" r="7" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<line x1="10" y1="22" x2="22" y2="10" stroke="{C_DIM}" stroke-width="1" stroke-dasharray="2,2"/>\n' +
    svg_footer()
)

SVGS["stretch.svg"] = (
    svg_header() +
    f'<rect x="4" y="10" width="10" height="12" fill="none" stroke="{C_DIM}" stroke-width="2"/>\n' +
    f'<rect x="18" y="6" width="10" height="20" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<line x1="14" y1="16" x2="18" y2="16" stroke="{C_DIM}" stroke-width="2" stroke-dasharray="2,2"/>\n' +
    svg_footer()
)

SVGS["rotate.svg"] = (
    svg_header() +
    f'<path d="M16,4 A12,12 0 1,1 4,16" fill="none" stroke="{C_LINE}" stroke-width="2.5"/>\n' +
    f'<polygon points="4,16 0,10 8,10" fill="{C_LINE}"/>\n' +
    f'<circle cx="16" cy="16" r="3" fill="{C_BLUE}"/>\n' +
    svg_footer()
)

SVGS["mirror.svg"] = (
    svg_header() +
    f'<line x1="16" y1="2" x2="16" y2="30" stroke="{C_DIM}" stroke-width="1.5" stroke-dasharray="3,3"/>\n' +
    f'<polygon points="12,6 2,26 12,26" fill="none" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<polygon points="20,6 30,26 20,26" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    svg_footer()
)

SVGS["scale.svg"] = (
    svg_header() +
    f'<rect x="4" y="20" width="8" height="8" fill="none" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<rect x="4" y="4" width="24" height="24" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<line x1="4" y1="28" x2="28" y2="4" stroke="{C_DIM}" stroke-width="1" stroke-dasharray="2,2"/>\n' +
    svg_footer()
)

SVGS["trim.svg"] = (
    svg_header() +
    f'<line x1="16" y1="2" x2="16" y2="30" stroke="{C_DIM}" stroke-width="2"/>\n' +
    f'<line x1="2" y1="16" x2="16" y2="16" stroke="{C_LINE}" stroke-width="2.5"/>\n' +
    f'<line x1="16" y1="16" x2="30" y2="16" stroke="{C_RED}" stroke-width="2" stroke-dasharray="2,2"/>\n' +
    f'<path d="M20,12 L26,20 M26,12 L20,20" fill="none" stroke="{C_RED}" stroke-width="2"/>\n' +
    svg_footer()
)

SVGS["extend.svg"] = (
    svg_header() +
    f'<line x1="28" y1="2" x2="28" y2="30" stroke="{C_DIM}" stroke-width="2"/>\n' +
    f'<line x1="2" y1="16" x2="16" y2="16" stroke="{C_LINE}" stroke-width="2.5"/>\n' +
    f'<line x1="16" y1="16" x2="28" y2="16" stroke="{C_BLUE}" stroke-width="2" stroke-dasharray="2,2"/>\n' +
    f'<path d="M22,12 L26,16 L22,20" fill="none" stroke="{C_BLUE}" stroke-width="2"/>\n' +
    svg_footer()
)

SVGS["fillet.svg"] = (
    svg_header() +
    f'<path d="M4,28 L4,12 Q4,4 12,4 L28,4" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    svg_footer()
)

SVGS["array.svg"] = (
    svg_header() +
    f'<rect x="4" y="4" width="6" height="6" fill="none" stroke="{C_LINE}" stroke-width="1.5"/>\n' +
    f'<rect x="14" y="4" width="6" height="6" fill="none" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<rect x="24" y="4" width="6" height="6" fill="none" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<rect x="4" y="14" width="6" height="6" fill="none" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<rect x="14" y="14" width="6" height="6" fill="none" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<rect x="24" y="14" width="6" height="6" fill="none" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<rect x="4" y="24" width="6" height="6" fill="none" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<rect x="14" y="24" width="6" height="6" fill="none" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    f'<rect x="24" y="24" width="6" height="6" fill="none" stroke="{C_DIM}" stroke-width="1.5"/>\n' +
    svg_footer()
)

SVGS["erase.svg"] = (
    svg_header() +
    f'<path d="M8,22 L14,28 L28,14 L22,8 Z" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<line x1="13" y1="27" x2="27" y2="13" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<line x1="2" y1="28" x2="30" y2="28" stroke="{C_RED}" stroke-width="1.5" stroke-dasharray="3,3"/>\n' +
    svg_footer()
)

SVGS["explode.svg"] = (
    svg_header() +
    f'<rect x="10" y="10" width="12" height="12" fill="none" stroke="{C_DIM}" stroke-width="1"/>\n' +
    f'<line x1="8" y1="8" x2="2" y2="2" stroke="{C_RED}" stroke-width="2"/>\n' +
    f'<line x1="24" y1="8" x2="30" y2="2" stroke="{C_RED}" stroke-width="2"/>\n' +
    f'<line x1="8" y1="24" x2="2" y2="30" stroke="{C_RED}" stroke-width="2"/>\n' +
    f'<line x1="24" y1="24" x2="30" y2="30" stroke="{C_RED}" stroke-width="2"/>\n' +
    svg_footer()
)

SVGS["offset.svg"] = (
    svg_header() +
    f'<path d="M4,28 C8,12 24,12 28,4" fill="none" stroke="{C_LINE}" stroke-width="2"/>\n' +
    f'<path d="M10,32 C14,16 30,16 34,8" fill="none" stroke="{C_DIM}" stroke-width="1.5" stroke-dasharray="2,2"/>\n' +
    svg_footer()
)

SVGS["dropdown.svg"] = (
    f'<svg width="10" height="10" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg">\n' +
    f'<polygon points="1,3 9,3 5,8" fill="{C_DIM}"/>\n' +
    svg_footer()
)

for name, content in SVGS.items():
    with open(os.path.join(icons_dir, name), "w", encoding="utf-8") as f:
        f.write(content)

print(f"Generated {len(SVGS)} icons in {icons_dir}")
