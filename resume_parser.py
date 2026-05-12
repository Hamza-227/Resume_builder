"""
resume_parser.py
----------------
Extracts structured resume data from an existing PDF file using pdfplumber.
Returns a Resume model instance (partially filled) that the user can review
and edit in the Streamlit UI before generating a new PDF.

Heuristics used:
  • Name  → first non-empty line (usually largest font, always first)
  • Contact → lines 2–4 containing @, +, LinkedIn, etc.
  • Sections → lines that are ALL-CAPS and match known section keywords
  • Dates → regex  r'(\w+ \d{4})\s*[–\-–]\s*(\w+ \d{4}|Present)'
  • Bullets → lines starting with •, -, *, or similar unicode dashes
"""

from __future__ import annotations

import re
import sys
import os
from typing import Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # type: ignore

sys.path.insert(0, os.path.dirname(__file__))

from resume_model import (
    Resume, ContactInfo, ExperienceEntry, EducationEntry,
    Project, Skills, Certification, resume_from_dict
)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

SECTION_KEYWORDS = {
    "summary":          ["SUMMARY", "PROFESSIONAL SUMMARY", "OBJECTIVE", "PROFILE"],
    "experience":       ["EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT", "WORK HISTORY", "PROFESSIONAL EXPERIENCE"],
    "education":        ["EDUCATION", "ACADEMIC BACKGROUND", "QUALIFICATIONS"],
    "projects":         ["PROJECTS", "PROJECT EXPERIENCE", "KEY PROJECTS"],
    "skills":           ["SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES", "COMPETENCIES"],
    "certifications":   ["CERTIFICATIONS", "CERTIFICATES", "LICENSES", "CREDENTIALS"],
}

DATE_PATTERN = re.compile(
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
    r'\.?\s+\d{4}\s*[–\-\u2013\u2014]\s*'
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
    r'\.?\s+\d{4}|Present|Current|Now)',
    re.IGNORECASE,
)

DATE_PART = re.compile(
    r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
    r'\.?\s+\d{4})|Present|Current|Now)',
    re.IGNORECASE,
)

BULLET_RE = re.compile(r'^[\u2022\u2023\u25aa\u25cf\u27a2\-\*•]\s+')
EMAIL_RE  = re.compile(r'[\w.\-+]+@[\w\-]+\.[a-zA-Z]{2,}')
PHONE_RE  = re.compile(r'(\+?\d[\d\s\-().]{7,}\d)')
URL_RE    = re.compile(r'https?://[^\s|,]+')


# ─────────────────────────────────────────────────────────────────────────────
# LOW-LEVEL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _detect_section(line: str) -> Optional[str]:
    """Return the canonical section key if the line is a section header, else None."""
    stripped = line.strip().upper()
    # Remove trailing punctuation / colons
    stripped = re.sub(r'[:\-]+$', '', stripped).strip()

    for key, variants in SECTION_KEYWORDS.items():
        if stripped in variants:
            return key
    return None


def _split_date_range(text: str):
    """Return (start_date, end_date) strings or ('', '') if no date found."""
    parts = DATE_PART.findall(text)
    if len(parts) >= 2:
        return parts[0].strip(), parts[1].strip()
    if len(parts) == 1:
        return parts[0].strip(), ""
    return "", ""


def _is_bullet(line: str) -> bool:
    return bool(BULLET_RE.match(line.strip()))


def _clean_bullet(line: str) -> str:
    return BULLET_RE.sub("", line.strip()).strip()


def _extract_urls_labeled(line: str) -> dict:
    """Try to pull LinkedIn / GitHub / Website from a contact line."""
    result = {}
    lower = line.lower()
    for url in URL_RE.findall(line):
        if "linkedin" in url.lower():
            result["linkedin"] = url
        elif "github" in url.lower():
            result["github"] = url
        elif "portfolio" in lower or "portfolio" in url.lower():
            result["portfolio"] = url
        else:
            result.setdefault("website", url)
    # Also detect bare words like "LinkedIn" followed by a URL hint
    if "linkedin" in lower and "linkedin" not in result:
        result["linkedin"] = None  # present but URL not found
    if "github" in lower and "github" not in result:
        result["github"] = None
    return result


# ─────────────────────────────────────────────────────────────────────────────
# SECTION PARSERS
# ─────────────────────────────────────────────────────────────────────────────

def _parse_contact(header_lines: list[str]) -> ContactInfo:
    """Parse name + contact info from the first few lines of the resume."""
    name = ""
    phone = ""
    city = ""
    email = ""
    linkedin = None
    github = None
    website = None
    portfolio = None

    for i, line in enumerate(header_lines[:6]):
        line = line.strip()
        if not line:
            continue

        if i == 0 and not name:
            name = line
            continue

        # Email
        email_match = EMAIL_RE.search(line)
        if email_match and not email:
            email = email_match.group()

        # Phone
        phone_match = PHONE_RE.search(line)
        if phone_match and not phone:
            phone = phone_match.group()

        # URLs
        urls = _extract_urls_labeled(line)
        linkedin = linkedin or urls.get("linkedin")
        github = github or urls.get("github")
        website = website or urls.get("website")
        portfolio = portfolio or urls.get("portfolio")

        # City — heuristic: short chunk between pipes that has no @ or digits
        pipe_parts = re.split(r'\|', line)
        for part in pipe_parts:
            part = part.strip()
            if (
                part
                and "@" not in part
                and not PHONE_RE.search(part)
                and not URL_RE.search(part)
                and len(part.split()) <= 4
                and not city
            ):
                city = part

    return ContactInfo(
        name=name,
        phone=phone,
        city=city,
        email=email,
        linkedin=linkedin,
        github=github,
        website=website,
        portfolio=portfolio,
    )


def _parse_experience(lines: list[str]) -> list[ExperienceEntry]:
    """Parse one or more experience entries from a list of lines."""
    entries = []
    current: dict | None = None

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        date_match = DATE_PATTERN.search(line_s)
        if date_match:
            # Start a new experience block
            if current is not None:
                entries.append(ExperienceEntry(**current))

            start, end = _split_date_range(line_s)
            # Title is everything before the date match on the same line
            title_part = line_s[:date_match.start()].strip().rstrip(",|–-").strip()

            current = {
                "title": title_part or "Role",
                "company": "",
                "start_date": start,
                "end_date": end,
                "location": "",
                "bullets": [],
            }
            continue

        if current is None:
            continue

        if _is_bullet(line_s):
            current["bullets"].append(_clean_bullet(line_s))
        elif not current["company"]:
            # First non-bullet non-date line after a date → company / location
            parts = re.split(r'[,|]', line_s, maxsplit=1)
            current["company"] = parts[0].strip()
            if len(parts) > 1:
                current["location"] = parts[1].strip()
        # else: could be additional context; we skip to keep it clean

    if current is not None:
        entries.append(ExperienceEntry(**current))

    return entries


def _parse_education(lines: list[str]) -> list[EducationEntry]:
    entries = []
    current: dict | None = None

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        date_match = DATE_PATTERN.search(line_s)
        if date_match:
            if current:
                entries.append(EducationEntry(**current))
            start, end = _split_date_range(line_s)
            institution_part = line_s[:date_match.start()].strip().rstrip(",|–-").strip()
            current = {
                "institution": institution_part or "Institution",
                "degree": "",
                "start_date": start,
                "end_date": end,
            }
            continue

        if current is None:
            continue

        if not current["degree"] and not _is_bullet(line_s):
            current["degree"] = line_s

    if current:
        entries.append(EducationEntry(**current))

    return entries


def _parse_projects(lines: list[str]) -> list[Project]:
    projects = []
    current_name = ""
    current_desc_lines: list[str] = []

    def flush():
        if current_name:
            projects.append(Project(
                name=current_name,
                description=" ".join(current_desc_lines).strip(),
            ))

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        if _is_bullet(line_s):
            # Treat the bullet text as a project name
            flush()
            current_name = _clean_bullet(line_s)
            current_desc_lines = []
        elif current_name:
            current_desc_lines.append(line_s)
        else:
            current_name = line_s

    flush()
    return projects


def _parse_skills(lines: list[str]) -> Skills:
    languages_tools: list[str] = []
    techniques: list[str] = []
    soft_skills: list[str] = []

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        lower = line_s.lower()
        # Split on colon to get label: values
        if ":" in line_s:
            label, _, value = line_s.partition(":")
            items = [v.strip() for v in re.split(r'[,;]', value) if v.strip()]
            label_l = label.lower()
            if any(k in label_l for k in ["language", "tool", "technology", "platform"]):
                languages_tools.extend(items)
            elif any(k in label_l for k in ["technique", "method", "ml", "ai", "skill", "competency"]):
                techniques.extend(items)
            elif any(k in label_l for k in ["soft", "interpersonal", "communication"]):
                soft_skills.extend(items)
            else:
                # Default: put into techniques
                techniques.extend(items)
        else:
            # Bare list of comma-separated items
            items = [v.strip() for v in re.split(r'[,;]', line_s) if v.strip()]
            if items:
                techniques.extend(items)

    return Skills(
        languages_tools=languages_tools or [],
        techniques=techniques or [],
        soft_skills=soft_skills or [],
    )


def _parse_certifications(lines: list[str]) -> list[Certification]:
    certs = []
    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        # Strip bullets
        if _is_bullet(line_s):
            line_s = _clean_bullet(line_s)
        # Try to find embedded URL
        url_match = URL_RE.search(line_s)
        link = url_match.group() if url_match else None
        # Remove the URL from the name
        name = URL_RE.sub("", line_s).strip().rstrip(":,|").strip()
        if name:
            certs.append(Certification(name=name, link=link))
    return certs


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PARSER
# ─────────────────────────────────────────────────────────────────────────────

def parse_resume_pdf(pdf_path_or_bytes) -> Resume:
    """
    Parse a PDF resume (file path string or bytes) and return a Resume model.

    Args:
        pdf_path_or_bytes: Path to a PDF file (str/Path) or raw bytes.

    Returns:
        Resume instance with best-effort parsed fields.
        All fields are editable before PDF generation.
    """
    if pdfplumber is None:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    import io as _io

    if isinstance(pdf_path_or_bytes, (bytes, bytearray)):
        source = _io.BytesIO(pdf_path_or_bytes)
    else:
        source = pdf_path_or_bytes

    with pdfplumber.open(source) as pdf:
        full_text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )

    lines = full_text.splitlines()

    # ── Split lines into sections ─────────────────────────────────────────────
    sections: dict[str, list[str]] = {key: [] for key in SECTION_KEYWORDS}
    header_lines: list[str] = []
    current_section: Optional[str] = None

    for line in lines:
        detected = _detect_section(line)
        if detected:
            current_section = detected
            continue

        if current_section is None:
            header_lines.append(line)
        else:
            sections[current_section].append(line)

    # ── Parse each section ────────────────────────────────────────────────────
    contact  = _parse_contact(header_lines)
    summary  = " ".join(l.strip() for l in sections["summary"] if l.strip())
    exp      = _parse_experience(sections["experience"])
    edu      = _parse_education(sections["education"])
    projects = _parse_projects(sections["projects"])
    skills   = _parse_skills(sections["skills"])
    certs    = _parse_certifications(sections["certifications"])

    return Resume(
        contact=contact,
        summary=summary,
        experience=exp if exp else [
            ExperienceEntry(
                title="Role", company="Company", start_date="", end_date="Present",
                location="", bullets=["Achievement 1"]
            )
        ],
        education=edu,
        projects=projects,
        skills=skills,
        certifications=certs,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRY
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, json

    ap = argparse.ArgumentParser(description="Parse a PDF resume and output JSON")
    ap.add_argument("pdf", help="Path to the resume PDF")
    ap.add_argument("--output", "-o", default=None, help="Output JSON file (default: print to stdout)")
    args = ap.parse_args()

    resume = parse_resume_pdf(args.pdf)

    from resume_model import resume_to_dict
    data = resume_to_dict(resume)
    out = json.dumps(data, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(out)
        print(f"✅  Parsed resume saved to: {args.output}")
    else:
        print(out)
