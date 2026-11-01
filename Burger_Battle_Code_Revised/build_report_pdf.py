"""Build the report (summary, Q1-Q3, references) as an A4 PDF from report/sources/*.md.

A4, 11pt body (competition rule: nothing smaller than 11pt), three embedded
vector-quality figures, tables with their captions above and figures with their
captions below.

Run:  <bundled python> build_q1_pdf.py
"""
import os
import re

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (CondPageBreak, Image as RLImage, KeepTogether,
                                PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIRS = [os.path.join(HERE, "..", "report", "sources"), os.path.join(HERE, "report", "sources"),
            os.path.join(HERE, "paper"), HERE, os.path.join(HERE, "..", "paper"), os.path.join(HERE, "..")]
SOURCES = ["summary.md", "q1_section.md", "q2_section.md", "q3_section.md", "references.md"]  # report order
_report_dirs = [os.path.join(HERE, "..", "report"), HERE]
OUT = os.path.join(next((d for d in _report_dirs if os.path.isdir(d)), HERE), "burger_battle_report.pdf")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
LFIGURE = 0.90                      # in-figure text lands at ~8.9 pt on paper
HEADING_SPACE = 70                  # pt that must be left for a heading to start on a page
FRAME_W = PAGE_W - 2 * MARGIN
INK = colors.HexColor("#1a1a1a")
RULE = colors.HexColor("#9a9a9a")
HEAD_BG = colors.HexColor("#f0f0f0")

STY = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=16.5, leading=20,
                            textColor=INK, alignment=TA_CENTER, spaceAfter=6, keepWithNext=True),
    "byline": ParagraphStyle("byline", fontName="Times-Italic", fontSize=11, leading=14,
                             textColor=INK, alignment=TA_CENTER, spaceAfter=14),
    # keepWithNext keeps a heading from being stranded at the foot of a page
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=15, leading=18,
                         textColor=INK, spaceAfter=10, keepWithNext=True),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12.5, leading=14,
                         textColor=INK, spaceBefore=9, spaceAfter=4, keepWithNext=True),
    "body": ParagraphStyle("body", fontName="Times-Roman", fontSize=11, leading=13.5,
                           alignment=TA_JUSTIFY, textColor=INK, spaceAfter=4),
    "formula": ParagraphStyle("formula", fontName="Times-Italic", fontSize=11, leading=13.5,
                              alignment=TA_CENTER, textColor=INK, spaceBefore=3, spaceAfter=4),
    "caption": ParagraphStyle("caption", fontName="Times-Italic", fontSize=11, leading=12.9,
                              alignment=TA_LEFT, textColor=INK, spaceAfter=6),
    "cell": ParagraphStyle("cell", fontName="Times-Roman", fontSize=11, leading=13.5, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Times-Bold", fontSize=11, leading=13.5, textColor=INK),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", s)
    return s


def build_table(rows):
    widths = [0.37 * FRAME_W] + [(0.63 * FRAME_W) / (len(rows[0]) - 1)] * (len(rows[0]) - 1)
    data = []
    for r, row in enumerate(rows):
        style = STY["cellb"] if r == 0 else STY["cell"]
        data.append([Paragraph(inline(c), style) for c in row])
    t = Table(data, colWidths=widths, hAlign="CENTER", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def parse(md_path):
    """markdown subset -> list of (kind, payload)"""
    lines = open(md_path, encoding="utf-8").read().split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("# "):
            out.append(("h1", ln[2:].strip()))
        elif ln.strip() == "---":                      # page break (thematic break in markdown)
            out.append(("pagebreak", None))
        elif ln.startswith("## "):
            out.append(("h2", ln[3:].strip()))
        elif ln.startswith("!["):
            path = ln[ln.index("(") + 1:ln.rindex(")")].strip("<>")
            out.append(("image", path))
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"-{2,}", c) for c in cells):
                    rows.append(cells)
                i += 1
            out.append(("table", rows))
            continue
        elif re.match(r"^Authors?:\s", ln):
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(("#", "|", "![")):
                ln += " " + lines[i].strip()
                i += 1
            out.append(("byline", ln))
            continue
        else:
            buf = [ln.strip()]
            i += 1
            while (i < len(lines) and lines[i].strip()
                   and not lines[i].lstrip().startswith(("#", "|", "!["))
                   and lines[i].strip() != "---"):
                buf.append(lines[i].strip())
                i += 1
            text = " ".join(buf)
            if re.match(r"^\(\d+\)\s", text):
                out.append(("formula", text))
            elif text.startswith("*") and text.endswith("*") and text.count("*") == 2:
                out.append(("caption", text[1:-1]))
            else:
                out.append(("body", text))
            continue
        i += 1
    return out


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 11)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawCentredString(PAGE_W / 2, MARGIN * 0.55, str(doc.page))
    canvas.restoreState()


def main():
    blocks = []
    for n, name in enumerate(SOURCES):
        src = next((os.path.join(d, name) for d in SRC_DIRS if os.path.exists(os.path.join(d, name))), None)
        if src is None:
            raise SystemExit(f"missing source {name!r}: put the paper .md files next to this script")
        part = parse(src)
        if part and part[0][0] == "h1":            # first heading of the report = document title
            kind, payload = part[0]
            part = [("title", payload)] + part[1:]
        blocks += part
    flow = []
    i = 0
    while i < len(blocks):
        kind, payload = blocks[i]
        nxt = blocks[i + 1] if i + 1 < len(blocks) else (None, None)
        if kind == "image":
            if os.path.isabs(payload):
                path = payload
            else:
                path = next((os.path.join(d, payload) for d in
                             (HERE, os.path.join(HERE, ".."), *SRC_DIRS)
                             if os.path.exists(os.path.join(d, payload))), os.path.join(HERE, payload))
            w, h = Image.open(path).size
            width = FRAME_W * LFIGURE
            img = RLImage(path, width=width, height=width * h / w)
            group = [Spacer(1, 3), img]
            if nxt[0] == "caption":                    # figure caption always stays with its figure
                group += [Spacer(1, 4), Paragraph(inline(nxt[1]), STY["caption"])]
                i += 2
            else:
                i += 1
            flow.append(KeepTogether(group))
            continue
        if kind == "caption" and nxt[0] == "table":    # table caption always stays above its table
            flow.append(KeepTogether([Paragraph(inline(payload), STY["caption"]),
                                      build_table(nxt[1]), Spacer(1, 9)]))
            i += 2
            continue
        if kind in ("title", "h1", "h2"):
            head = Paragraph(inline(payload), STY[kind])
            if (nxt[0] == "caption" and i + 2 < len(blocks)
                    and blocks[i + 2][0] == "table"):
                # a heading that introduces a table travels with that table
                flow.append(KeepTogether([head,
                                          Paragraph(inline(nxt[1]), STY["caption"]),
                                          build_table(blocks[i + 2][1]), Spacer(1, 9)]))
                i += 3
                continue
            # otherwise it never starts in the last two or three lines of a page
            flow.append(CondPageBreak(HEADING_SPACE))
            flow.append(head)
            i += 1
            continue
        elif kind == "pagebreak":
            flow.append(PageBreak())
        elif kind == "byline":
            flow.append(Paragraph(inline(payload), STY["byline"]))
        elif kind == "body":
            flow.append(Paragraph(inline(payload), STY["body"]))
        elif kind == "formula":
            flow.append(Paragraph(inline(payload), STY["formula"]))
        elif kind == "caption":
            flow.append(Paragraph(inline(payload), STY["caption"]))
        elif kind == "table":
            flow.append(Spacer(1, 2))
            flow.append(build_table(payload))
            flow.append(Spacer(1, 9))
        i += 1
    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN,
                            title="The Burger Battle",
                            author="HKUST(GZ) 2026 MCM Junior")
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print("wrote", os.path.relpath(OUT, HERE), f"from {SOURCES}")


if __name__ == "__main__":
    main()
