"""Overlap auditor for the SVG figures.

We cannot eyeball the rendered PNGs in this session, so this script estimates a
bounding box for every <text> element (Helvetica advance widths) and reports
  * text-vs-text overlaps  (the "ghosting" artefact),
  * text that leaves the canvas,
  * text that sits on top of a filled data rectangle (bars / heat-map cells).

Run:  python3 audit_figures.py
"""
import glob
import os
import sys
import xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"
HERE = os.path.dirname(os.path.abspath(__file__))
# Printed width of a figure: A4 (595.28 pt) less two 18 mm margins = 493.2 pt of
# text frame, times LFIGURE = 0.90 in build_report_pdf.py = 443.9 pt.  An in-figure
# font of 18 units therefore lands at 18 x 443.9 / 900 = 8.9 pt on paper.
PLACED_WIDTH_PT = 443.9


def advance(ch, size):
    if ch.isdigit() or ch in ".,:;+-−":
        return 0.556 * size
    if ch == " ":
        return 0.28 * size
    if ch in "()[]":
        return 0.333 * size
    if ch.isupper():
        return 0.66 * size
    if ch in "→≥≤":
        return 0.75 * size
    return 0.53 * size


def text_box(x, y, s, size, anchor, rotated):
    w = sum(advance(c, size) for c in s) * 1.04
    if rotated:
        return (x - 0.78 * size, y - w / 2, x + 0.24 * size, y + w / 2)
    x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
    return (x0, y - 0.78 * size, x0 + w, y + 0.24 * size)


def overlap(a, b, tol=1.5):
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return dx > tol and dy > tol, dx * dy


def audit(path):
    root = ET.parse(path).getroot()
    W, H = float(root.get("width")), float(root.get("height"))
    texts, rects, lines = [], [], []
    smallest = 1e9
    for el in root.iter():
        if el.tag == NS + "text":
            s = (el.text or "").strip()
            if not s:
                continue
            size = float(el.get("font-size"))
            smallest = min(smallest, size)
            box = text_box(float(el.get("x")), float(el.get("y")), s, size,
                           el.get("text-anchor", "start"),
                           bool(el.get("transform")))
            texts.append((s, box))
        elif el.tag == NS + "rect":
            w, h = float(el.get("width")), float(el.get("height"))
            if w * h > 0.02 * W * H or str(el.get("fill", "none")) == "none":
                continue                      # background / borders are fine
            rects.append((float(el.get("x")), float(el.get("y")), w, h))
        elif el.tag == NS + "line":
            x1, y1 = float(el.get("x1")), float(el.get("y1"))
            x2, y2 = float(el.get("x2")), float(el.get("y2"))
            sw = float(el.get("stroke-width", 1)) / 2 + 1
            lines.append((min(x1, x2) - sw, min(y1, y2) - sw, max(x1, x2) + sw, max(y1, y2) + sw))
        elif el.tag == NS + "polyline":
            pts = [tuple(map(float, p.split(","))) for p in el.get("points").split()]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            sw = float(el.get("stroke-width", 1)) / 2 + 1
            if max(ys) - min(ys) < 3:          # flat segments only; steps are drawn in pieces
                lines.append((min(xs) - sw, min(ys) - sw, max(xs) + sw, max(ys) + sw))

    problems = []
    for i, (s1, b1) in enumerate(texts):
        if b1[0] < -1 or b1[1] < -1 or b1[2] > W + 1 or b1[3] > H + 1:
            problems.append(f"  outside canvas: {s1!r}")
        for s2, b2 in texts[i + 1:]:
            hit, area = overlap(b1, b2)
            if hit:
                problems.append(f"  text/text  {s1!r}  x  {s2!r}   (overlap {area:.0f} px²)")
        for r in rects:
            hit, area = overlap(b1, r, tol=3)
            if hit and area > 60:
                problems.append(f"  text/shape {s1!r}   (overlap {area:.0f} px²)")
        for ln in lines:
            hit, area = overlap(b1, ln, tol=1.5)
            if hit and area > 25:
                problems.append(f"  text/line  {s1!r}   (crossed by a line, {area:.0f} px²)")
    on_paper = smallest * PLACED_WIDTH_PT / W
    if on_paper < 8.5:
        problems.append(f"  smallest label renders at {on_paper:.1f} pt on paper "
                        f"(need >= 8.5 pt): raise font sizes or shrink the canvas")
    print(f"{os.path.basename(path)}: {len(texts)} labels, canvas {W:.0f}x{H:.0f}, "
          f"smallest label {smallest:.0f} units = {on_paper:.1f} pt on paper, "
          f"{'CLEAN' if not problems else str(len(problems)) + ' PROBLEMS'}")
    for p in problems:
        print(p)
    return len(problems)


FIG_DIR = next((d for d in (os.path.join(HERE, "figures"), os.path.join(HERE, "..", "figures"), HERE)
                if glob.glob(os.path.join(d, "*.svg"))), HERE)


if __name__ == "__main__":
    print("auditing", FIG_DIR)
    if not glob.glob(os.path.join(FIG_DIR, "*.svg")):
        print("no SVG files found - run make_figures.py first")
        sys.exit(0)
    bad = sum(audit(f) for f in sorted(glob.glob(os.path.join(FIG_DIR, "*.svg"))))
    print("\ntotal problems:", bad)
    sys.exit(1 if bad else 0)
