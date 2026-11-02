"""Chuyen BaoCao_KiemChung_VVDN_XenKe.md sang .docx (python-docx).

Chi ho tro dung tap Markdown da dung trong bao cao do: tieu de #/##/###,
bang | ... |, danh sach -, danh sach so, blockquote >, in dam **...**,
ma inline `...`, khoi ma ```...```, duong ke ngang ---.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Cm

HERE = Path(__file__).parent
SRC = HERE / "BaoCao_KiemChung_VVDN_XenKe.md"
OUT = HERE / "BaoCao_KiemChung_VVDN_XenKe.docx"


def add_runs(par, text):
    """Xu ly **in dam** va `ma` trong mot doan."""
    for phan in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not phan:
            continue
        if phan.startswith("**") and phan.endswith("**"):
            par.add_run(phan[2:-2]).bold = True
        elif phan.startswith("`") and phan.endswith("`"):
            r = par.add_run(phan[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(9)
        else:
            par.add_run(phan)


def main():
    lines = SRC.read_text(encoding="utf-8").splitlines()
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.0)

    i = 0
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):                       # khoi ma
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            r = p.add_run("\n".join(buf))
            r.font.name = "Consolas"
            r.font.size = Pt(9)
            i += 1
            continue

        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s:\-|]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            nc = max(len(r) for r in rows)
            t = doc.add_table(rows=0, cols=nc)
            t.style = "Light Grid Accent 1"
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for k, row in enumerate(rows):
                cells = t.add_row().cells
                for j in range(nc):
                    cells[j].text = ""
                    p = cells[j].paragraphs[0]
                    add_runs(p, row[j] if j < len(row) else "")
                    for r in p.runs:
                        r.font.size = Pt(9)
                        if k == 0:
                            r.bold = True
            doc.add_paragraph()
            continue

        if re.match(r"^#{1,3} ", ln):
            cap = len(ln) - len(ln.lstrip("#"))
            # Bo dau ** trong tieu de: Word da in dam ca dong roi
            h = doc.add_heading(ln[cap + 1:].strip().replace(chr(42)*2, chr(32)*0), level=cap)
            if cap == 1:
                h.runs[0].font.color.rgb = RGBColor(0x1F, 0x3B, 0x73)
        elif ln.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            add_runs(p, ln[2:])
            for r in p.runs:
                r.italic = True
        elif re.match(r"^\d+\.\s", ln):
            p = doc.add_paragraph(style="List Number")
            add_runs(p, re.sub(r"^\d+\.\s", "", ln))
        elif ln.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_runs(p, ln[2:])
        elif ln.strip() == "---":
            doc.add_paragraph("_" * 78).alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif ln.strip():
            add_runs(doc.add_paragraph(), ln)
        i += 1

    doc.save(OUT)
    print(f"Da ghi {OUT.name}")


if __name__ == "__main__":
    main()
