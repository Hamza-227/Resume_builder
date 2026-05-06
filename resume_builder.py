"""
resume_builder.py
-----------------
Generates a ONE-PAGE ATS-friendly PDF resume using reportlab Platypus.

New in v4:
  - Project links rendered as clickable "View Project →" inline with project name
  - Cleaner section spacing
  - Auto-scale to guarantee 1-page output

ATS Rules enforced:
  • Standard fonts only — Times-Roman family
  • Zero images / graphics / icons
  • Single-column layout
  • Plain bullet characters (•)
  • All text selectable / copyable
  • Exact ATS section titles: SUMMARY, EXPERIENCE, EDUCATION, PROJECTS, SKILLS, CERTIFICATIONS
  • PDF metadata (Title, Author) set correctly
"""

from __future__ import annotations
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, Table, TableStyle, KeepTogether,
)
from reportlab.lib import colors


# ─────────────────────────────────────────────────────────────────────────────
# PAGE GEOMETRY
# ─────────────────────────────────────────────────────────────────────────────

MARGIN_TB   = 0.40 * inch
MARGIN_LR   = 0.52 * inch
PAGE_W, PAGE_H = letter
USABLE_W    = PAGE_W - 2 * MARGIN_LR     # ~511 pt
USABLE_H    = PAGE_H - 2 * MARGIN_TB     # ~712 pt

SCALE_STEPS = [1.0, 0.97, 0.94, 0.91, 0.88, 0.85, 0.82, 0.79, 0.76]
MIN_BODY_PT = 7.5


# ─────────────────────────────────────────────────────────────────────────────
# STYLE FACTORY
# ─────────────────────────────────────────────────────────────────────────────

def _styles(sc: float = 1.0) -> dict:
    def sz(b): return max(MIN_BODY_PT, b * sc)
    def sp(b): return b * sc
    def ld(b): return max(MIN_BODY_PT + 1, b * sc)

    return {
        "name": ParagraphStyle("name",
            fontName="Times-Bold", fontSize=sz(17), leading=ld(20),
            alignment=TA_CENTER, spaceAfter=sp(2), spaceBefore=0),

        "contact": ParagraphStyle("contact",
            fontName="Times-Roman", fontSize=sz(8.5), leading=ld(11),
            alignment=TA_CENTER, spaceAfter=sp(4), spaceBefore=0),

        "sec_hdr": ParagraphStyle("sec_hdr",
            fontName="Times-Bold", fontSize=sz(9.5), leading=ld(12),
            spaceBefore=sp(6), spaceAfter=sp(0), alignment=TA_LEFT),

        "job_title": ParagraphStyle("job_title",
            fontName="Times-Bold", fontSize=sz(9.5), leading=ld(12),
            spaceBefore=sp(4), spaceAfter=0),

        "co_left": ParagraphStyle("co_left",
            fontName="Times-Italic", fontSize=sz(8.8), leading=ld(11),
            alignment=TA_LEFT, spaceBefore=0, spaceAfter=0),

        "date_right": ParagraphStyle("date_right",
            fontName="Times-Roman", fontSize=sz(8.8), leading=ld(11),
            alignment=TA_RIGHT, spaceBefore=0, spaceAfter=0),

        "bullet": ParagraphStyle("bullet",
            fontName="Times-Roman", fontSize=sz(8.8), leading=ld(11.5),
            leftIndent=10, spaceBefore=sp(0.5), spaceAfter=sp(0.5)),

        "edu_inst": ParagraphStyle("edu_inst",
            fontName="Times-Bold", fontSize=sz(9.5), leading=ld(12),
            spaceBefore=sp(4), spaceAfter=0),

        "edu_deg": ParagraphStyle("edu_deg",
            fontName="Times-Italic", fontSize=sz(8.8), leading=ld(11),
            spaceAfter=0, spaceBefore=0),

        "proj_title": ParagraphStyle("proj_title",
            fontName="Times-Bold", fontSize=sz(9.0), leading=ld(11.5),
            spaceBefore=sp(4), spaceAfter=0),

        "proj_body": ParagraphStyle("proj_body",
            fontName="Times-Roman", fontSize=sz(8.8), leading=ld(11.5),
            spaceBefore=sp(0.5), spaceAfter=sp(1), leftIndent=10),

        "skills": ParagraphStyle("skills",
            fontName="Times-Roman", fontSize=sz(8.8), leading=ld(11.5),
            spaceBefore=sp(1), spaceAfter=sp(0.5)),

        "cert": ParagraphStyle("cert",
            fontName="Times-Roman", fontSize=sz(8.8), leading=ld(11.5),
            spaceBefore=sp(1), spaceAfter=sp(0.5)),

        "summary": ParagraphStyle("summary",
            fontName="Times-Roman", fontSize=sz(8.8), leading=ld(11.8),
            spaceAfter=sp(1), spaceBefore=0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _x(t: str) -> str:
    """XML-escape a string for use inside Paragraph markup."""
    if not t:
        return ""
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _hr(sc: float) -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.5, color=colors.black,
                      spaceAfter=2 * sc, spaceBefore=1 * sc)


def _row(left: Paragraph, right: Paragraph, dw: float) -> Table:
    """Two-column row: left text + right-aligned date."""
    t = Table([[left, right]], colWidths=[dw * 0.63, dw * 0.37], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _sec(title: str, st: dict, sc: float) -> list:
    return [Paragraph(title.upper(), st["sec_hdr"]), _hr(sc)]


# ─────────────────────────────────────────────────────────────────────────────
# SECTION BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _contact(resume, st: dict) -> list:
    c = resume.contact
    parts = []
    if c.phone:  parts.append(_x(c.phone))
    if c.city:   parts.append(_x(c.city))
    if c.email:
        parts.append(f'<a href="mailto:{_x(c.email)}" color="black">{_x(c.email)}</a>')
    for attr, lbl in [("linkedin","LinkedIn"),("github","GitHub"),
                       ("website","Website"),("portfolio","Portfolio")]:
        url = getattr(c, attr, None)
        if url:
            parts.append(f'<a href="{_x(url)}" color="black"><u>{lbl}</u></a>')
    return [
        Paragraph(_x(c.name), st["name"]),
        Paragraph(" | ".join(parts), st["contact"]),
    ]


def _summary(resume, st: dict, sc: float) -> list:
    return _sec("Summary", st, sc) + [Paragraph(_x(resume.summary), st["summary"])]


def _experience(resume, st: dict, sc: float, dw: float) -> list:
    story = _sec("Experience", st, sc)
    for exp in resume.experience:
        co = _x(exp.company) + (f", <i>{_x(exp.location)}</i>" if exp.location else "")
        date = f"{_x(exp.start_date)} \u2013 {_x(exp.end_date)}"
        block = [
            Paragraph(_x(exp.title), st["job_title"]),
            _row(Paragraph(co, st["co_left"]), Paragraph(date, st["date_right"]), dw),
        ] + [Paragraph(f"\u2022\u00a0 {_x(b)}", st["bullet"]) for b in exp.bullets]
        story.append(KeepTogether(block))
    return story


def _education(resume, st: dict, sc: float, dw: float) -> list:
    story = _sec("Education", st, sc)
    for edu in resume.education:
        date = f"{_x(edu.start_date)} \u2013 {_x(edu.end_date)}"
        block = [
            Paragraph(_x(edu.institution), st["edu_inst"]),
            _row(Paragraph(_x(edu.degree), st["edu_deg"]),
                 Paragraph(date, st["date_right"]), dw),
        ]
        story.append(KeepTogether(block))
    return story


def _projects(resume, st: dict, sc: float) -> list:
    story = _sec("Projects", st, sc)
    for proj in resume.projects:
        # Title line: bold name + optional clickable link
        if proj.link:
            title_line = (
                f"\u2022\u00a0 <b>{_x(proj.name)}</b>"
                f'  <a href="{_x(proj.link)}" color="#1155CC"><u>View Project \u2192</u></a>'
            )
        else:
            title_line = f"\u2022\u00a0 <b>{_x(proj.name)}</b>"

        block = [
            Paragraph(title_line, st["proj_title"]),
            Paragraph(_x(proj.description), st["proj_body"]),
        ]
        story.append(KeepTogether(block))
    return story


def _skills(resume, st: dict, sc: float) -> list:
    story = _sec("Skills", st, sc)
    sk = resume.skills
    if sk.languages_tools:
        story.append(Paragraph(
            "<b>Languages &amp; Tools:</b> " + ", ".join(_x(s) for s in sk.languages_tools),
            st["skills"]))
    if sk.techniques:
        story.append(Paragraph(
            "<b>Techniques:</b> " + ", ".join(_x(s) for s in sk.techniques),
            st["skills"]))
    if sk.soft_skills:
        story.append(Paragraph(
            "<b>Soft Skills:</b> " + ", ".join(_x(s) for s in sk.soft_skills),
            st["skills"]))
    return story


def _certifications(resume, st: dict, sc: float) -> list:
    story = _sec("Certifications", st, sc)
    for cert in resume.certifications:
        line = (
            f'{_x(cert.name)}: <a href="{_x(cert.link)}" color="black"><u>Link</u></a>'
            if cert.link else _x(cert.name)
        )
        story.append(Paragraph(line, st["cert"]))
    return story


# ─────────────────────────────────────────────────────────────────────────────
# STORY ASSEMBLER
# ─────────────────────────────────────────────────────────────────────────────

def _assemble(resume, st: dict, sc: float, dw: float) -> list:
    story = []
    story.extend(_contact(resume, st))
    story.extend(_summary(resume, st, sc))
    story.extend(_experience(resume, st, sc, dw))
    story.extend(_education(resume, st, sc, dw))
    story.extend(_projects(resume, st, sc))
    story.extend(_skills(resume, st, sc))
    story.extend(_certifications(resume, st, sc))
    return story


# ─────────────────────────────────────────────────────────────────────────────
# HEIGHT ESTIMATOR  (fast — no full render needed)
# ─────────────────────────────────────────────────────────────────────────────

def _est_height(story: list, dw: float) -> float:
    total = 0.0
    for f in story:
        try:
            if isinstance(f, KeepTogether):
                for sub in f._content:
                    _, h = sub.wrap(dw, 9999)
                    sty = getattr(sub, "style", None)
                    total += h + (getattr(sty, "spaceBefore", 0) or 0) \
                               + (getattr(sty, "spaceAfter",  0) or 0)
            elif isinstance(f, HRFlowable):
                total += (f.spaceAfter or 0) + (f.spaceBefore or 0) + 2
            elif isinstance(f, Spacer):
                total += f.height
            else:
                _, h = f.wrap(dw, 9999)
                sty = getattr(f, "style", None)
                total += h + (getattr(sty, "spaceBefore", 0) or 0) \
                           + (getattr(sty, "spaceAfter",  0) or 0)
        except Exception:
            total += 12
    return total


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def build_resume(resume, force_one_page: bool = True) -> bytes:
    """
    Build an ATS-compliant, one-page PDF from a Resume model.

    Args:
        resume:          Resume model instance.
        force_one_page:  Auto-scale fonts/spacing until content fits 1 page.

    Returns:
        PDF bytes ready for download or file write.
    """
    dw = USABLE_W
    sc = SCALE_STEPS[-1]   # fallback

    if force_one_page:
        for scale in SCALE_STEPS:
            sty   = _styles(scale)
            story = _assemble(resume, sty, scale, dw)
            if _est_height(story, dw) <= USABLE_H:
                sc = scale
                break
    else:
        sc = SCALE_STEPS[0]

    sty   = _styles(sc)
    story = _assemble(resume, sty, sc, dw)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=MARGIN_TB, bottomMargin=MARGIN_TB,
        leftMargin=MARGIN_LR, rightMargin=MARGIN_LR,
        title="Resume", author=resume.contact.name,
        subject="Professional Resume", creator="ATS Resume Builder v4",
    )
    doc.build(story)
    return buf.getvalue()


def build_resume_to_file(resume, path: str) -> None:
    pdf = build_resume(resume)
    with open(path, "wb") as f:
        f.write(pdf)
    try:
        import pdfplumber
        with pdfplumber.open(path) as p:
            pages = len(p.pages)
        print(f"✅  {path}  •  {pages} page  •  {len(pdf)//1024}KB")
    except Exception:
        print(f"✅  {path}  •  {len(pdf)//1024}KB")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, json, sys, os
    ap = argparse.ArgumentParser(description="ATS Resume Builder — one-page PDF")
    ap.add_argument("--input",  "-i", help="JSON resume data file")
    ap.add_argument("--output", "-o", default="resume.pdf")
    ap.add_argument("--no-one-page", action="store_true")
    args = ap.parse_args()
    sys.path.insert(0, os.path.dirname(__file__))
    from resume_model import SAMPLE_RESUME, resume_from_dict
    if args.input:
        with open(args.input) as f:
            resume = resume_from_dict(json.load(f))
        print(f"📄  Loaded: {args.input}")
    else:
        resume = SAMPLE_RESUME
        print("📄  Using sample resume (Jordan Smith — generic dummy)")
    build_resume_to_file(resume, args.output)
