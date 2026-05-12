"""
ats_checker.py
--------------
Honest, rule-based ATS resume scorer.
No fake inflated scores. Real criteria recruiters and ATS systems use.

Scoring breakdown (100 pts total):
  text_extraction  20  — Can ATS read the text at all?
  sections         20  — Are all 6 required section headers present?
  format           20  — Page count, file size, density
  keywords         20  — Action verbs, numbers/metrics, keyword density
  contact          10  — Email, phone, LinkedIn presence
  red_flags        10  — Tables, images, columns, problematic characters
"""

from __future__ import annotations
import io, re
from dataclasses import dataclass, field
from typing import List

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_SECTIONS = ["SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS"]
PREFERRED_SECTIONS = ["PROJECTS", "CERTIFICATIONS"]

ACTION_VERBS = [
    "led", "built", "designed", "developed", "created", "managed", "improved",
    "reduced", "increased", "achieved", "delivered", "implemented", "deployed",
    "automated", "optimized", "launched", "scaled", "grew", "generated",
    "collaborated", "mentored", "trained", "analyzed", "architected", "migrated",
    "engineered", "streamlined", "spearheaded", "oversaw", "coordinated",
    "established", "executed", "drove", "maintained", "resolved", "integrated",
]

METRIC_PATTERNS = [
    r'\d+%',                    # percentages: 40%
    r'\$[\d,]+[kKmMbB]?',       # money: $2M, $180K
    r'\d+[kKmMbB]\+?',          # big numbers: 2M, 10K+
    r'\d+\s*x\b',               # multipliers: 3x
    r'#\s*\d+',                 # rankings: #1
    r'\b\d{1,3}(?:,\d{3})+',   # comma-numbers: 1,200
    r'\b\d+\s*(?:days?|weeks?|months?|years?|hours?|seconds?)\b',
    r'\b(?:zero|first|second|third|100%)\b',
]

FONT_ISSUES = ["arial", "calibri", "helvetica neue", "gill sans", "futura", "avenir"]

ATS_KILLER_WORDS = [
    "header", "footer", "text box", "table of contents",
    "graph", "chart", "image", "photo", "picture",
]


# ─────────────────────────────────────────────────────────────────────────────
# RESULT STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CategoryScore:
    score: int
    max: int
    notes: List[str] = field(default_factory=list)


@dataclass
class Recommendation:
    title: str
    description: str
    priority: str  # "high" | "medium" | "low"
    points_impact: int


@dataclass
class ATSResult:
    total_score: int
    categories: dict
    recommendations: List[dict]
    text_preview: str
    pages: int
    file_size_kb: float


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCORER
# ─────────────────────────────────────────────────────────────────────────────

def score_resume(pdf_bytes: bytes) -> dict:
    """
    Analyze PDF resume and return honest ATS score.
    Returns a dict ready for JSON serialization.
    """
    if not HAS_PDFPLUMBER:
        raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        pages = len(pdf.pages)
        all_text = "\n".join(pg.extract_text() or "" for pg in pdf.pages)
        all_images = sum(len(pg.images) for pg in pdf.pages)
        # Detect tables (multi-column layouts)
        all_tables = sum(len(pg.extract_tables() or []) for pg in pdf.pages)

    file_size_kb = len(pdf_bytes) / 1024
    text_upper = all_text.upper()
    text_lower = all_text.lower()
    words = all_text.split()
    word_count = len(words)

    # ── 1. TEXT EXTRACTION (20 pts) ──────────────────────────────
    text_score = 0
    text_notes = []

    if word_count >= 200:
        text_score += 10
    elif word_count >= 100:
        text_score += 6
        text_notes.append(f"Only {word_count} words extracted — may have parsing issues")
    elif word_count > 0:
        text_score += 3
        text_notes.append(f"Very little text found ({word_count} words) — ATS may fail to parse")
    else:
        text_notes.append("NO text extracted — this is likely a scanned image PDF. ATS cannot read it.")

    if word_count >= 200:
        text_score += 5  # good density
    if all_images == 0:
        text_score += 5
    else:
        text_notes.append(f"{all_images} image(s) detected in PDF — ATS ignores images entirely")

    text_cat = CategoryScore(min(text_score, 20), 20, text_notes)

    # ── 2. SECTION HEADERS (20 pts) ──────────────────────────────
    sec_score = 0
    sec_notes = []
    found_required = []
    missing_required = []
    found_preferred = []

    for sec in REQUIRED_SECTIONS:
        if sec in text_upper:
            sec_score += 4
            found_required.append(sec)
        else:
            missing_required.append(sec)
            sec_notes.append(f"Missing required section: {sec}")

    for sec in PREFERRED_SECTIONS:
        if sec in text_upper:
            sec_score += 2
            found_preferred.append(sec)

    if missing_required:
        sec_notes.insert(0, f"Required sections found: {len(found_required)}/4")

    sec_cat = CategoryScore(min(sec_score, 20), 20, sec_notes)

    # ── 3. FORMAT (20 pts) ───────────────────────────────────────
    fmt_score = 0
    fmt_notes = []

    # Page count (most important format factor)
    if pages == 1:
        fmt_score += 10
    elif pages == 2:
        fmt_score += 6
        fmt_notes.append("2-page resume — single page is preferred for <10 years experience")
    else:
        fmt_score += 2
        fmt_notes.append(f"{pages} pages — ATS and recruiters strongly prefer 1 page")

    # File size (too small = image-only, too large = bloated)
    if 5 <= file_size_kb <= 300:
        fmt_score += 5
    elif file_size_kb < 5:
        fmt_score += 1
        fmt_notes.append(f"File very small ({file_size_kb:.1f}KB) — may be missing content")
    else:
        fmt_score += 3
        fmt_notes.append(f"File large ({file_size_kb:.0f}KB) — large PDFs sometimes cause ATS parsing issues")

    # Content density (word count)
    if 250 <= word_count <= 700:
        fmt_score += 5
    elif word_count < 150:
        fmt_score += 1
        fmt_notes.append(f"Resume too sparse ({word_count} words) — add more detail")
    elif word_count > 800:
        fmt_score += 3
        fmt_notes.append(f"Resume may be too long ({word_count} words) — consider trimming")

    fmt_cat = CategoryScore(min(fmt_score, 20), 20, fmt_notes)

    # ── 4. METRICS & KEYWORDS (20 pts) ──────────────────────────
    kw_score = 0
    kw_notes = []

    # Action verbs count
    action_verb_count = sum(1 for v in ACTION_VERBS if re.search(r'\b' + v + r'\b', text_lower))
    if action_verb_count >= 8:
        kw_score += 8
    elif action_verb_count >= 5:
        kw_score += 5
        kw_notes.append(f"Only {action_verb_count} action verbs found — aim for 8+ (Led, Built, Reduced, etc.)")
    elif action_verb_count >= 2:
        kw_score += 3
        kw_notes.append(f"Only {action_verb_count} action verbs — add more (Led, Built, Reduced, Automated...)")
    else:
        kw_notes.append("Almost no action verbs — start each bullet with Led, Built, Reduced, Automated, etc.")

    # Quantified metrics count
    metric_count = sum(len(re.findall(p, all_text)) for p in METRIC_PATTERNS)
    if metric_count >= 8:
        kw_score += 8
    elif metric_count >= 4:
        kw_score += 5
        kw_notes.append(f"Only {metric_count} metrics found — add numbers to more bullets (%, $, users, time saved)")
    elif metric_count >= 1:
        kw_score += 2
        kw_notes.append(f"Only {metric_count} metric(s) found — every bullet should have a number")
    else:
        kw_notes.append("No numbers/metrics found — add percentages, dollar amounts, user counts to bullets")

    # Bullet structure
    bullet_count = all_text.count("•") + all_text.count("●") + all_text.count("·")
    if bullet_count >= 8:
        kw_score += 4
    elif bullet_count >= 4:
        kw_score += 2
        kw_notes.append(f"Only {bullet_count} bullet points — aim for 8-12 across all experience")
    else:
        kw_notes.append(f"Few bullet points detected ({bullet_count}) — use bullets for all experience entries")

    kw_cat = CategoryScore(min(kw_score, 20), 20, kw_notes)

    # ── 5. CONTACT & LINKS (10 pts) ─────────────────────────────
    contact_score = 0
    contact_notes = []

    email_found = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text))
    phone_found = bool(re.search(r'[\+\(]?\d[\d\s\-\(\)\.]{7,}\d', all_text))
    linkedin_found = "linkedin.com" in text_lower
    github_found = "github.com" in text_lower

    if email_found:    contact_score += 4
    else:              contact_notes.append("No email address found — critical for recruiter contact")

    if phone_found:    contact_score += 3
    else:              contact_notes.append("No phone number found — add for recruiter callbacks")

    if linkedin_found: contact_score += 2
    else:              contact_notes.append("No LinkedIn URL — add it, recruiters check LinkedIn for 80% of candidates")

    if github_found:   contact_score += 1

    contact_cat = CategoryScore(min(contact_score, 10), 10, contact_notes)

    # ── 6. RED FLAG CHECK (10 pts) ───────────────────────────────
    rf_score = 10
    rf_notes = []

    if all_images > 0:
        rf_score -= min(4, all_images * 2)
        rf_notes.append(f"{all_images} image(s) — ATS skips all image content")

    if all_tables > 0:
        rf_score -= min(4, all_tables * 2)
        rf_notes.append(f"{all_tables} table(s) detected — tables often break ATS column parsing")

    # Check for special bullets that aren't standard
    fancy_bullets = len(re.findall(r'[➤➢▶►✓✔✗✘❖◆■□▪▫]', all_text))
    if fancy_bullets > 3:
        rf_score -= 2
        rf_notes.append(f"{fancy_bullets} fancy bullet characters — use plain • only for ATS")

    # Check for ALL CAPS body text (sign of design-heavy resume)
    caps_ratio = sum(1 for c in all_text if c.isupper()) / max(len(all_text), 1)
    if caps_ratio > 0.25:
        rf_score -= 2
        rf_notes.append("High proportion of uppercase text — may indicate design-heavy layout")

    rf_cat = CategoryScore(max(rf_score, 0), 10, rf_notes)

    # ── TOTAL ────────────────────────────────────────────────────
    total = (text_cat.score + sec_cat.score + fmt_cat.score +
             kw_cat.score + contact_cat.score + rf_cat.score)

    # ── RECOMMENDATIONS (top 5 by impact) ────────────────────────
    all_recs: List[Recommendation] = []

    # From text extraction
    if word_count == 0:
        all_recs.append(Recommendation(
            "Resume is Image-Only — ATS Cannot Read It",
            "Your PDF appears to be a scanned image or has no selectable text. ATS software will score it 0 and reject it automatically. Re-create your resume as a text-based PDF using our builder.",
            "high", 20
        ))
    elif word_count < 150:
        all_recs.append(Recommendation(
            "Very Little Text Extracted",
            f"Only {word_count} words were extracted from your PDF. This suggests text is embedded in shapes or text boxes that ATS cannot read. Use a standard text-based PDF format.",
            "high", 15
        ))

    if all_images > 0:
        all_recs.append(Recommendation(
            f"Remove {all_images} Image(s) from Your Resume",
            "Images in a resume are completely invisible to ATS software. This includes profile photos, logos, icons, and decorative graphics. Remove all images — they add file size and subtract ATS score.",
            "high", 8
        ))

    if all_tables > 0:
        all_recs.append(Recommendation(
            f"Replace Tables with Plain Text Sections",
            f"{all_tables} table(s) detected. ATS parsers often scramble table content, mixing up job titles with dates. Use plain text sections instead of tables for all content.",
            "high", 8
        ))

    # Missing required sections
    for sec in missing_required:
        all_recs.append(Recommendation(
            f"Add Missing Section: {sec}",
            f"The '{sec}' section header was not found. ATS systems search for exact section names. Add a clearly labeled {sec} section with the exact word '{sec}' as the heading.",
            "high", 4
        ))

    # Metrics
    if metric_count < 4:
        all_recs.append(Recommendation(
            "Add Quantified Metrics to Bullets",
            f"Only {metric_count} number(s)/metric(s) found. Every bullet should contain a metric: percentages (40% faster), money ($2M revenue), scale (10,000 users), or time (reduced from 3 days to 4 hours). Metrics are the #1 way to stand out.",
            "high" if metric_count == 0 else "medium", 8
        ))

    # Action verbs
    if action_verb_count < 5:
        all_recs.append(Recommendation(
            "Start Every Bullet with an Action Verb",
            f"Only {action_verb_count} action verbs detected. ATS keyword scoring rewards strong action verbs. Every bullet should start with: Led, Built, Reduced, Automated, Designed, Deployed, Increased, Delivered, Implemented, or similar.",
            "medium", 6
        ))

    # Page count
    if pages > 1:
        all_recs.append(Recommendation(
            f"Reduce to One Page (Currently {pages} Pages)",
            "Recruiters spend 7 seconds average on a resume. Single-page resumes have 2× higher callback rates for candidates with under 10 years experience. Cut older roles to 1-2 bullets and trim verbose descriptions.",
            "medium", 6
        ))

    # Contact
    if not email_found:
        all_recs.append(Recommendation(
            "Add Email Address",
            "No email address was detected. This is critical — without contact info your resume cannot progress past ATS screening.",
            "high", 4
        ))
    if not linkedin_found:
        all_recs.append(Recommendation(
            "Add LinkedIn Profile URL",
            "No LinkedIn URL found. 80% of recruiters check LinkedIn before contacting a candidate. Add your full LinkedIn URL: https://linkedin.com/in/yourprofile",
            "medium", 2
        ))
    if not phone_found:
        all_recs.append(Recommendation(
            "Add Phone Number",
            "No phone number detected. Recruiters need multiple ways to contact you. Add your phone number in the contact section.",
            "medium", 3
        ))

    # Bullets
    if bullet_count < 4:
        all_recs.append(Recommendation(
            "Add More Bullet Points to Experience",
            f"Only {bullet_count} bullets found. Each job role should have 2-4 achievement bullets. Bullets make content scannable for both ATS and human reviewers.",
            "medium", 4
        ))

    # Sort by impact, take top 5
    all_recs.sort(key=lambda r: (r.priority == "high", r.points_impact), reverse=True)
    top5 = all_recs[:5]

    # If score is already high, give optimization tips
    if len(top5) < 5 and total >= 70:
        top5.append(Recommendation(
            "Add a Portfolio or GitHub URL",
            "Including links to your work (GitHub, portfolio, live projects) allows recruiters to verify your skills immediately. Projects with links receive 40% more recruiter engagement.",
            "low", 2
        ))
        top5 = top5[:5]

    return {
        "total_score": total,
        "categories": {
            "text_extraction": {"score": text_cat.score, "max": text_cat.max, "notes": text_cat.notes},
            "sections":        {"score": sec_cat.score,  "max": sec_cat.max,  "notes": sec_cat.notes},
            "format":          {"score": fmt_cat.score,  "max": fmt_cat.max,  "notes": fmt_cat.notes},
            "keywords":        {"score": kw_cat.score,   "max": kw_cat.max,   "notes": kw_cat.notes},
            "contact":         {"score": contact_cat.score, "max": contact_cat.max, "notes": contact_cat.notes},
            "red_flags":       {"score": rf_cat.score,   "max": rf_cat.max,   "notes": rf_cat.notes},
        },
        "recommendations": [
            {"title": r.title, "description": r.description, "priority": r.priority, "points_impact": r.points_impact}
            for r in top5
        ],
        "text_preview": all_text[:300],
        "pages": pages,
        "file_size_kb": round(file_size_kb, 1),
        "word_count": word_count,
        "metrics_found": metric_count,
        "action_verbs_found": action_verb_count,
    }
