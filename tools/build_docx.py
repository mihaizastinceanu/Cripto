"""Convert a lab report.md into a .docx with a title page.

usage: python tools/build_docx.py <labdir> [<labdir> ...]
Supports: front matter (lab, title, course, variant), # / ## / ### headings,
paragraphs with **bold**, *italic* and `code`, fenced and 4-space-indented code,
images ![caption](path), pipe tables, - and 1. lists, > quotes.
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

AUTHOR, GROUP = "Zastinceanu Mihai", "FAF-243"
TEXT = {
    "ro": dict(uni="Universitatea Tehnică a Moldovei",
               fac="Facultatea Calculatoare, Informatică și Microelectronică",
               dep="Departamentul Ingineria Software și Automatică",
               report="RAPORT", lab="Lucrarea de laborator nr. {n}", disc="la disciplina „{c}”",
               theme="Tema: {t}", done="A efectuat:", student="st. gr. {g}", checked="A verificat:",
               city="Chișinău, 2026", fig="Figura"),
    "en": dict(uni="Technical University of Moldova",
               fac="Faculty of Computers, Informatics and Microelectronics",
               dep="Department of Software Engineering and Automatics",
               report="REPORT", lab="Laboratory Work No. {n}", disc="Course: {c}",
               theme="Topic: {t}", done="Done by:", student="student, group {g}", checked="Checked by:",
               city="Chișinău, 2026", fig="Figure"),
}
INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*]))")


def set_font(run, name="Times New Roman", size=12, bold=None, italic=None, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)


def add_inline(par, text, size=12):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            set_font(par.add_run(part[2:-2]), size=size, bold=True)
        elif part.startswith("`") and part.endswith("`"):
            set_font(par.add_run(part[1:-1]), "Consolas", size - 1.5)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            set_font(par.add_run(part[1:-1]), size=size, italic=True)
        else:
            set_font(par.add_run(part), size=size)


def shade(cell_or_par, fill):
    el = cell_or_par._tc.get_or_add_tcPr() if hasattr(cell_or_par, "_tc") else cell_or_par._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    el.append(shd)


def para(doc, align=None, before=0, after=6, indent=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.line_spacing = 1.15
    if indent:
        pf.first_line_indent = Cm(1)
    if align:
        p.alignment = align
    return p


def title_page(doc, meta, t):
    c = WD_ALIGN_PARAGRAPH.CENTER
    for key in ("uni", "fac", "dep"):
        set_font(para(doc, c, after=2, indent=False).add_run(t[key]), size=14, bold=(key == "uni"))
    for _ in range(6):
        para(doc, indent=False)
    set_font(para(doc, c, indent=False).add_run(t["report"]), size=26, bold=True)
    set_font(para(doc, c, indent=False).add_run(t["lab"].format(n=meta["lab"])), size=16)
    set_font(para(doc, c, indent=False).add_run(t["disc"].format(c=meta["course"])), size=14)
    p = para(doc, c, before=12, indent=False)
    set_font(p.add_run(t["theme"].format(t=meta["title"])), size=16, bold=True)
    if meta.get("variant"):
        set_font(para(doc, c, indent=False).add_run(f"({meta['variant']})"), size=13, italic=True)
    for _ in range(7):
        para(doc, indent=False)
    tbl = doc.add_table(rows=2, cols=2)
    rows = [(t["done"], f"{t['student'].format(g=GROUP)}\n{AUTHOR}"), (t["checked"], "\n____________________")]
    for r, (a, b) in enumerate(rows):
        set_font(tbl.cell(r, 0).paragraphs[0].add_run(a), size=13, bold=True)
        cp = tbl.cell(r, 1).paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_font(cp.add_run(b), size=13)
    for _ in range(5):
        para(doc, indent=False)
    set_font(para(doc, c, indent=False).add_run(t["city"]), size=14)
    doc.paragraphs[-1].add_run().add_break(WD_BREAK.PAGE)


def code_block(doc, lines):
    p = para(doc, after=8, indent=False)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.left_indent = Cm(0.3)
    shade(p, "F2F2F2")
    for i, line in enumerate(lines):
        r = p.add_run(line)
        set_font(r, "Consolas", 8.5)
        if i < len(lines) - 1:
            r.add_break()


def table(doc, rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
    ncol = max(len(r) for r in cells)
    tbl = doc.add_table(rows=len(cells), cols=ncol)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    size = 8 if ncol > 14 else 10
    for i, r in enumerate(cells):
        for j in range(ncol):
            cell = tbl.cell(i, j)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_inline(p, r[j] if j < len(r) else "", size=size)
            if i == 0:
                shade(cell, "D9E2F3")
                for run in p.runs:
                    run.bold = True
    para(doc, after=2, indent=False)


def build(lab: Path):
    src = (lab / "report.md").read_text(encoding="utf-8")
    meta = {}
    if src.startswith("---"):
        fm, src = src[3:].split("---", 1)
        meta = dict(l.split(":", 1) for l in fm.strip().splitlines())
        meta = {k.strip(): v.strip() for k, v in meta.items()}
    lang = "en" if re.search(r"\b(the|and)\b", meta.get("title", "") + src[:400]) and "ș" not in src[:600] else "ro"
    t = TEXT[lang]
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21)
    sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(2.5), Cm(1.5), Cm(2), Cm(2)
    title_page(doc, meta, t)

    lines = src.strip("\n").split("\n")
    i, fig = 0, 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            code_block(doc, lines[i + 1:j])
            i = j + 1
            continue
        if line.startswith("    ") and (i == 0 or not lines[i - 1].strip()):
            j = i
            while j < len(lines) and (lines[j].startswith("    ") or not lines[j].strip()):
                j += 1
            while j > i and not lines[j - 1].strip():
                j -= 1
            code_block(doc, [l[4:] for l in lines[i:j]])
            i = j
            continue
        m = re.match(r"(#{1,3}) (.*)", line)
        if m:
            level = len(m.group(1))
            h = doc.add_heading(level=level)
            r = h.add_run(m.group(2))
            set_font(r, size={1: 16, 2: 14, 3: 12}[level], bold=True, color=(0, 0, 0))
            h.paragraph_format.space_before = Pt(14 if level == 1 else 10)
            h.paragraph_format.space_after = Pt(6)
            i += 1
            continue
        m = re.match(r"!\[(.*?)\]\((.*?)\)", line.strip())
        if m:
            fig += 1
            p = para(doc, WD_ALIGN_PARAGRAPH.CENTER, before=6, after=2, indent=False)
            img = lab / m.group(2)
            from PIL import Image
            im = Image.open(img)
            w, h = im.size
            width = min(16.5, 16.5 * w / 1100) if w < 1100 else 16.5
            max_h_px = int(21 * w / width)              # slice height that fits on one page
            if h <= max_h_px:
                p.add_run().add_picture(str(img), width=Cm(width))
            else:                                       # tall terminal capture -> page-sized slices
                tmp = lab / ".slices"
                tmp.mkdir(exist_ok=True)
                top, k = 0, 0
                while top < h:
                    bottom = min(h, top + max_h_px)
                    if bottom < h:                      # cut on a dark (empty) row, not through text
                        for y in range(bottom, bottom - 200, -1):
                            row = im.crop((0, y, w, y + 1)).convert("L").getextrema()
                            if row[1] < 60:
                                bottom = y
                                break
                    piece = tmp / f"{img.stem}_{k}.png"
                    im.crop((0, top, w, bottom)).save(piece)
                    pp = p if k == 0 else para(doc, WD_ALIGN_PARAGRAPH.CENTER, after=2, indent=False)
                    pp.add_run().add_picture(str(piece), width=Cm(width))
                    top, k = bottom, k + 1
            cap = para(doc, WD_ALIGN_PARAGRAPH.CENTER, after=10, indent=False)
            set_font(cap.add_run(f"{t['fig']} {fig}. {m.group(1)}"), size=11, italic=True)
            i += 1
            continue
        if line.lstrip().startswith("|"):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            table(doc, lines[i:j])
            i = j
            continue
        m = re.match(r"(\s*)([-*]|\d+\.) (.*)", line)
        if m:
            nested = len(m.group(1)) >= 2
            style = "List Number" if m.group(2)[0].isdigit() else "List Bullet"
            if nested:
                style += " 2"
            p = doc.add_paragraph(style=style)
            p.paragraph_format.space_after = Pt(2)
            text = m.group(3)
            while i + 1 < len(lines) and lines[i + 1].startswith("   ") and lines[i + 1].strip() \
                    and not re.match(r"\s*([-*]|\d+\.) ", lines[i + 1]):
                i += 1
                text += " " + lines[i].strip()
            add_inline(p, text)
            i += 1
            continue
        if line.startswith(">"):
            p = para(doc, indent=False)
            p.paragraph_format.left_indent = Cm(1)
            add_inline(p, line.lstrip("> ").strip())
            for r in p.runs:
                r.italic = True
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        text = line.strip()
        while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"(#|!\[|\||```|>|\s*([-*]|\d+\.) |    )", lines[i + 1]):
            i += 1
            text += " " + lines[i].strip()
        p = para(doc, WD_ALIGN_PARAGRAPH.LEFT if "http" in text else WD_ALIGN_PARAGRAPH.JUSTIFY)
        add_inline(p, text)
        i += 1

    name = f"Lab{meta['lab']}{'_PKI' if lab.name.endswith('pki') else ''}_ZastinceanuMihai_{GROUP}.docx"
    out = lab / name
    doc.save(out)
    print("saved", out)


if __name__ == "__main__":
    for d in sys.argv[1:]:
        build(Path(d))
