"""Generate the Q1 figures as vector SVG (pure standard library).

Print-legibility target: each figure is placed at 0.90 of the A4 text frame
(493.2 pt with 18 mm margins, so 443.9 pt on paper) and the canvas is 900 units
wide, so an in-figure font of 18 units renders at 18 x 443.9/900 = 8.9 pt on paper.
audit_figures.py checks that ratio, the label collisions and the canvas bounds.

Run:  python3 make_figures.py && python3 audit_figures.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import DAYS, day_expect  # noqa: E402

FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
INK = "#1a1a1a"
MUTED = "#5a5a5a"
GRID = "#dcdcdc"
CANVAS_W = 900.0          # shared width so every figure has the same scale factor
FIG_DIR = next((d for d in (os.path.join(HERE, "figures"), os.path.join(HERE, "..", "figures"))
                if os.path.isdir(d)), os.path.join(HERE, "figures"))
os.makedirs(FIG_DIR, exist_ok=True)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Svg:
    def __init__(self, w, h, bg="#ffffff"):
        self.w, self.h = w, h
        self.parts = [f'<rect x="0" y="0" width="{w}" height="{h}" fill="{bg}"/>']

    def rect(self, x, y, w, h, fill, stroke="none", sw=1, rx=0):
        self.parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=18, anchor="start", fill=INK, weight="normal", rot=None):
        r = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{r}>{esc(s)}</text>')

    def poly(self, pts, stroke=INK, sw=2, fill="none", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.parts.append(
            f'<polyline points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="butt"{d}/>')

    def circle(self, cx, cy, r, fill=INK, stroke="none", sw=0):
        self.parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')

    def save(self, path):
        body = "\n".join("  " + p for p in self.parts)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}">\n{body}\n</svg>\n')
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", os.path.relpath(path, HERE), f"({len(svg)} bytes)")


def profit(p, q, rp, rq, rival_open=True):
    return sum(day_expect(p, q, True, rp, rq, rival_open, D, w)[0]
               for _, D, w in DAYS) / 3.0


def blend(c1, c2, t):
    return "#%02x%02x%02x" % tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))


def cell_color(v, lo, hi):
    if v >= 0:
        return blend((219, 238, 226), (26, 122, 71), min(1.0, v / hi))
    return blend((247, 219, 213), (170, 35, 25), min(1.0, v / lo))


def ink_on(v, lo, hi):
    c = cell_color(v, lo, hi)
    r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
    return "#ffffff" if (0.299 * r + 0.587 * g + 0.114 * b) < 150 else INK


def fig1(path):
    """heat map of expected profit over (stock, price), legible at print size"""
    BQ, BP = 4, 4
    qs = list(range(8, 0, -1))
    ps = list(range(1, 9))
    vals = {(q, p): profit(p, q, BP, BQ) for q in qs for p in ps}
    lo, hi = min(vals.values()), max(vals.values())

    L, T, cw, ch = 104, 128, 62, 34          # grid 496 x 272 units
    GW, GH = cw * len(ps), ch * len(qs)
    s = Svg(CANVAS_W, 546)
    s.text(24, 36, "Expected one-day profit of every (stock, price) plan", size=22, weight="600")
    s.text(24, 62, "against a rival buying 4 @ 4;  coins per day;  outlined column: p = 6",
           size=18, fill=MUTED)
    x6 = L + 5 * cw
    s.rect(x6 + cw / 2 - 36, 76, 72, 26, "#e8f2ea", stroke="#0f5132", sw=1, rx=13)
    s.text(x6 + cw / 2, 94, "p = 6", size=18, anchor="middle", weight="600", fill="#0f5132")

    for i, q in enumerate(qs):
        for j, p in enumerate(ps):
            v = vals[(q, p)]
            x, y = L + j * cw, T + i * ch
            s.rect(x, y, cw, ch, cell_color(v, lo, hi))
            s.text(x + cw / 2, y + ch / 2 + 6, f"{v:+.1f}", size=18,
                   anchor="middle", fill=ink_on(v, lo, hi))
        s.text(L - 16, T + i * ch + ch / 2 + 6, f"{q}", size=18, anchor="end", weight="600")
    for j, p in enumerate(ps):
        s.text(L + j * cw + cw / 2, T + GH + 26, f"{p}", size=18, anchor="middle", weight="600")
    s.text(L + GW / 2, T + GH + 52, "selling price p  (coins)", size=18, anchor="middle")
    s.text(30, T + GH / 2, "stock q", size=18, anchor="middle", rot=-90)

    s.rect(x6, T, cw, GH, "none", stroke="#0f5132", sw=2.5)
    row4 = T + 4 * ch
    s.rect(L + 5 * cw - 3, row4 - 3, cw + 6, ch + 6, "none", stroke=INK, sw=3)
    s.text(L + GW + 26, row4 + ch / 2 - 2, "robust plan:  buy 4 @ 6", size=19, weight="600")
    s.text(L + GW + 26, row4 + ch / 2 + 24, "+4.00, the maximum", size=18, fill=MUTED)

    ly, lw = T + GH + 78, GW / (7 * len(ps))
    for j in range(len(ps)):
        for k in range(7):
            s.rect(L + (j * 7 + k) * lw, ly, lw + 0.6, 18,
                   cell_color(lo + (hi - lo) * ((j + k / 6) / len(ps)), lo, hi))
    s.text(L, ly + 44, f"{lo:+.1f}", size=18, fill=MUTED)
    s.text(L + GW, ly + 44, f"{hi:+.1f}", size=18, anchor="end", fill=MUTED)
    s.text(L + GW / 2, ly + 44, "expected profit (coins)", size=18, anchor="middle", fill=MUTED)
    s.save(path)


def fig3(path, sim=None):
    """two panels: mean final cash, and the share of paths not trading on day 30"""
    rows = ["A", "B", "C", "D", "E"]
    cols = ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]
    if sim is None:
        sim = _q2_results()
    cash = [[sim["cash"][(r, c)] for c in cols] for r in rows]
    dead = [[sim["dead"][(r, c)] for c in cols] for r in rows]
    vmax = 150.0

    CW, CH, XL, XR, TOP = 46, 40, 70, 500, 150
    s = Svg(CANVAS_W, 534)
    s.text(24, 36, "Thirty-day outcome for five strategies against seven rivals", size=22, weight="600")
    s.text(24, 62, "mean final cash (left, coins) and share of paths not trading on day 30 (right, %)",
           size=18, fill=MUTED)
    s.text(XL, TOP - 16, "mean final cash", size=20, weight="600")
    s.text(XR, TOP - 16, "not trading on day 30", size=20, weight="600", fill="#8c2f28")

    for j, c in enumerate(cols):
        s.text(XL + j * CW + CW / 2, TOP + 24, c, size=18, anchor="middle", weight="600")
        s.text(XR + j * CW + CW / 2, TOP + 24, c, size=18, anchor="middle", weight="600")
    for i, r in enumerate(rows):
        y = TOP + 42 + i * CH
        s.text(XL - 14, y + CH / 2 + 6, r, size=18, anchor="end", weight="600")
        for j in range(len(cols)):
            v = cash[i][j]
            s.rect(XL + j * CW, y, CW, CH,
                   blend((247, 214, 208), (26, 122, 71), min(1.0, max(0.0, v) / vmax)))
            s.text(XL + j * CW + CW / 2, y + CH / 2 + 6, f"{v:.0f}", size=18, anchor="middle",
                   fill=ink_on(v, -1, vmax))
            d = dead[i][j]
            s.rect(XR + j * CW, y, CW, CH,
                   blend((250, 246, 244), (150, 30, 25), min(1.0, d / 100.0)))
            s.text(XR + j * CW + CW / 2, y + CH / 2 + 6, f"{d:.0f}", size=18, anchor="middle",
                   fill="#ffffff" if d > 55 else INK)
    ybot = TOP + 42 + len(rows) * CH
    s.text(XL - 14, ybot + 30, "A 4@6 (Q1 optimum)   B 4@4 (cautious)   C 8@4 (volume)",
           size=18, fill="#404040")
    s.text(XL - 14, ybot + 54, "D 4@6 but stop below 12 coins   E 4@6, switching to 4@4 once the rival is seen with 9+ burgers",
           size=18, fill="#404040")
    s.text(XL - 14, ybot + 78, "R1 4@4    R2 4@6    R3 8@4    R4 4@3", size=18, fill="#404040")
    s.text(XL - 14, ybot + 102, "R5 4@8    R6 all-in @4    R7 all-in @6", size=18, fill="#404040")
    s.save(path)


def _q2_results():
    """run the Q2 panel once and return the two matrices used by fig3"""
    sys.path.insert(0, HERE)
    import importlib
    q2 = importlib.import_module("q2_simulation")
    cash, dead = {}, {}
    for rn, mf in q2.MINE.items():
        for cn, rf in q2.RIVALS.items():
            c, _, d, _ = q2.evaluate(mf, rf)
            cash[(rn[0], cn[:2])] = c
            dead[(rn[0], cn[:2])] = d
    return {"cash": cash, "dead": dead}


def staircase(path, sim=None):
    steps = [0, 4, 6, 8, 9, 10, 12]
    worst = {0: profit(6, 4, 0, 0, rival_open=False)}
    for rq in steps[1:]:
        worst[rq] = min(profit(6, 4, rp, rq) for rp in range(1, 9))

    lo, hi = -6, 6
    L, T, W, H = 110, 122, 110, 250
    s = Svg(CANVAS_W, 512)
    s.text(24, 36, "Worst case of the robust plan: buy 4 @ 6", size=22, weight="600")
    s.text(24, 62, "worst-case expected profit against a rival with stock up to q, undercutting to 1 coin",
           size=18, fill=MUTED)

    def X(i):
        return L + W * (i + 0.5)

    def Y(v):
        return T + H * (hi - v) / (hi - lo)

    s.rect(L, Y(4), W * 4, Y(lo) - Y(4), "#eaf3ec")
    s.text(L + 2 * W, Y(4) - 18, "guaranteed +4.00 while the rival's stock <= 8", size=18,
           anchor="middle", weight="600", fill="#1a7a47")
    for v in range(lo, hi + 1, 3):
        s.line(L - 8, Y(v), L + W * len(steps) - 40, Y(v), stroke=GRID, sw=1)
        s.text(L - 16, Y(v) + 6, f"{v:+d}" if v else "0", size=18, anchor="end", fill=MUTED)
    s.line(L - 8, Y(0), L + W * len(steps) - 40, Y(0), stroke="#8a8a8a", sw=1.6)
    s.text(34, T + H / 2, "worst-case profit (coins)", size=18, anchor="middle", rot=-90)

    pts = [(X(i), Y(worst[q])) for i, q in enumerate(steps)]
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        s.poly([(x0, y0), (x1, y0), (x1, y1)], stroke="#b3261e", sw=2.8)
    for (x, y), q in zip(pts, steps):
        s.circle(x, y, 7, fill="#ffffff", stroke="#b3261e", sw=2.8)
        if worst[q] < 4:                      # the +4.00 plateau is labelled once, above the line
            s.text(x, y + 30, f"{worst[q]:+.2f}", size=18, anchor="middle", weight="600",
                   fill="#b3261e")
    s.line(L + W * 4, T - 6, L + W * 4, T + H, stroke="#8a8a8a", sw=1.6, dash="6 5")
    for i, q in enumerate(steps):
        s.text(X(i), T + H + 28, "closed" if q == 0 else f"{q}", size=18,
               anchor="middle", weight="600")
    s.text(L + (W * len(steps) - 40) / 2, T + H + 56, "rival's maximum stock (burgers)",
           size=18, anchor="middle")

    notes = ["Stock 9, 10 and 12 need 32, 36 and 44 coins, so day one cannot afford them.",
             "The umbrella ends where the first-day cash limit stops binding."]
    for i, note in enumerate(notes):
        s.text(L, T + H + 92 + i * 24, note, size=18, fill="#404040")
    s.save(path)


if __name__ == "__main__":
    fig1(os.path.join(FIG_DIR, "fig1_profit_heatmap.svg"))
    staircase(os.path.join(FIG_DIR, "fig2_robustness_staircase.svg"))
    fig3(os.path.join(FIG_DIR, "fig3_q2_grid.svg"))
