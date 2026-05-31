"""
blog_engine.py
--------------
Production-grade markdown blog engine.
Add a .md file to /blogs/ → it appears everywhere automatically.
No database. No manual frontend editing ever.
"""
from __future__ import annotations
import os, re, math
from pathlib import Path
from typing import List, Optional
from datetime import datetime

import frontmatter
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension

BLOGS_DIR = Path(__file__).parent / "blogs"

MD_EXTENSIONS = [
    FencedCodeExtension(),
    CodeHiliteExtension(linenums=False, css_class="highlight"),
    TocExtension(permalink=True, toc_depth="2-4"),
    TableExtension(),
    "markdown.extensions.attr_list",
    "markdown.extensions.def_list",
    "markdown.extensions.footnotes",
    "markdown.extensions.meta",
    "markdown.extensions.nl2br",
    "markdown.extensions.sane_lists",
    "markdown.extensions.smarty",
]

WORDS_PER_MINUTE = 200


def _slug_from_filename(fname: str) -> str:
    return fname.replace(".md", "").lower().strip()


def _reading_time(text: str) -> int:
    words = len(text.split())
    return max(1, math.ceil(words / WORDS_PER_MINUTE))


def _excerpt(text: str, length: int = 160) -> str:
    clean = re.sub(r"#.*?\n", "", text)
    clean = re.sub(r"[*_`\[\]()>#\-]", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:length] + ("…" if len(clean) > length else "")


def load_blog(slug: str) -> Optional[dict]:
    path = BLOGS_DIR / f"{slug}.md"
    if not path.exists():
        return None
    post = frontmatter.load(str(path))
    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    html = md.convert(post.content)
    toc = getattr(md, "toc", "")
    meta = post.metadata

    raw_date = meta.get("date", "")
    try:
        date_obj = datetime.strptime(str(raw_date), "%Y-%m-%d")
        date_fmt = date_obj.strftime("%B %d, %Y")
    except Exception:
        date_fmt = str(raw_date)

    return {
        "slug":         slug,
        "title":        meta.get("title", slug.replace("-", " ").title()),
        "description":  meta.get("description", _excerpt(post.content)),
        "image":        meta.get("image", "/static/images/blogs/default.jpg"),
        "category":     meta.get("category", "Career Tips"),
        "tags":         meta.get("tags", []),
        "date":         date_fmt,
        "date_raw":     str(raw_date),
        "author":       meta.get("author", "ResumeATS Team"),
        "keywords":     meta.get("keywords", []),
        "featured":     meta.get("featured", False),
        "content_html": html,
        "toc":          toc,
        "reading_time": _reading_time(post.content),
        "excerpt":      meta.get("description", _excerpt(post.content)),
    }


def load_all_blogs(sort_by: str = "date", featured_only: bool = False) -> List[dict]:
    if not BLOGS_DIR.exists():
        return []
    posts = []
    for f in BLOGS_DIR.glob("*.md"):
        slug = _slug_from_filename(f.name)
        post = load_blog(slug)
        if post:
            posts.append(post)
    if featured_only:
        posts = [p for p in posts if p["featured"]]
    posts.sort(key=lambda p: p.get("date_raw", ""), reverse=True)
    return posts


def get_related(slug: str, limit: int = 3) -> List[dict]:
    current = load_blog(slug)
    if not current:
        return []
    all_posts = [p for p in load_all_blogs() if p["slug"] != slug]
    current_tags = set(current.get("tags", []))
    current_cat  = current.get("category", "")

    def relevance(p):
        tag_overlap = len(set(p.get("tags", [])) & current_tags)
        cat_match   = 1 if p.get("category") == current_cat else 0
        return tag_overlap * 2 + cat_match

    all_posts.sort(key=relevance, reverse=True)
    return all_posts[:limit]


def get_categories() -> List[str]:
    cats = set()
    for p in load_all_blogs():
        cats.add(p["category"])
    return sorted(cats)


def search_blogs(query: str) -> List[dict]:
    q = query.lower()
    results = []
    for p in load_all_blogs():
        haystack = (p["title"] + " " + p["description"] + " " +
                    " ".join(p["tags"]) + " " + p["category"]).lower()
        if q in haystack:
            results.append(p)
    return results


def paginate(items: list, page: int = 1, per_page: int = 9) -> dict:
    total = len(items)
    pages = max(1, math.ceil(total / per_page))
    page  = max(1, min(page, pages))
    start = (page - 1) * per_page
    return {
        "items":    items[start:start + per_page],
        "page":     page,
        "pages":    pages,
        "total":    total,
        "has_prev": page > 1,
        "has_next": page < pages,
    }
