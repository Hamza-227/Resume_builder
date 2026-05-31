"""
app.py — ResumeATS Career Platform
------------------------------------
Full production Flask app with blog engine, ATS tools, and all pages.
"""
from __future__ import annotations
import io, json, os
from flask import (Flask, render_template, request, send_file,
                   jsonify, abort, redirect, url_for)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "resumeats-prod-2024")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

from resume_builder import build_resume
from resume_model import resume_from_dict
from ats_checker import score_resume
from blog_engine import (load_blog, load_all_blogs, get_related,
                         get_categories, search_blogs, paginate)


# ─────────────────────────────────────────────────────────────────
# MAIN PAGES
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    featured = load_all_blogs(featured_only=True)[:3]
    recent   = load_all_blogs()[:3]
    return render_template("index.html", featured=featured, recent=recent)

@app.route("/builder")
def builder():
    return render_template("builder.html")

@app.route("/checker")
def checker():
    return render_template("checker.html")

@app.route("/about")
def about():
    return render_template("pages/about.html")

@app.route("/contact")
def contact():
    return render_template("pages/contact.html")

@app.route("/privacy")
def privacy():
    return render_template("pages/privacy.html")

@app.route("/terms")
def terms():
    return render_template("pages/terms.html")


# ─────────────────────────────────────────────────────────────────
# BLOG ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/blog")
def blog_index():
    query    = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    page     = int(request.args.get("page", 1))

    if query:
        all_posts = search_blogs(query)
    elif category:
        all_posts = [p for p in load_all_blogs() if p["category"] == category]
    else:
        all_posts = load_all_blogs()

    paginated  = paginate(all_posts, page=page, per_page=9)
    categories = get_categories()
    featured   = load_all_blogs(featured_only=True)[:2]

    return render_template("blog/index.html",
        posts=paginated["items"],
        pagination=paginated,
        categories=categories,
        featured=featured,
        query=query,
        active_category=category,
    )


@app.route("/blog/<slug>")
def blog_post(slug):
    post = load_blog(slug)
    if not post:
        abort(404)
    related = get_related(slug, limit=3)
    recent  = [p for p in load_all_blogs()[:4] if p["slug"] != slug]
    return render_template("blog/post.html",
        post=post, related=related, recent=recent)


# ─────────────────────────────────────────────────────────────────
# API — GENERATE PDF
# ─────────────────────────────────────────────────────────────────

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No data received"}), 400
        contact = data.get("contact", {})
        if not contact.get("name", "").strip():
            return jsonify({"error": "Name is required"}), 400
        if not contact.get("email", "").strip():
            return jsonify({"error": "Email is required"}), 400
        if not data.get("experience"):
            return jsonify({"error": "At least one experience entry is required"}), 400

        resume    = resume_from_dict(data)
        pdf_bytes = build_resume(resume)
        safe_name = contact.get("name", "Resume").replace(" ", "_")
        return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                         as_attachment=True,
                         download_name=f"{safe_name}_ATS_Resume.pdf")
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        app.logger.error(f"PDF error: {e}")
        return jsonify({"error": "Failed to generate PDF."}), 500


# ─────────────────────────────────────────────────────────────────
# API — ATS CHECKER
# ─────────────────────────────────────────────────────────────────

@app.route("/check-ats", methods=["POST"])
def check_ats():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    if not f.filename or not f.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a PDF file"}), 400
    try:
        pdf_bytes = f.read()
        if len(pdf_bytes) < 100:
            return jsonify({"error": "File appears empty"}), 400
        return jsonify(score_resume(pdf_bytes))
    except Exception as e:
        app.logger.error(f"ATS check error: {e}")
        return jsonify({"error": "Could not analyze file."}), 500


# ─────────────────────────────────────────────────────────────────
# SEO FILES
# ─────────────────────────────────────────────────────────────────

@app.route("/sitemap.xml")
def sitemap():
    base  = request.host_url.rstrip("/")
    posts = load_all_blogs()
    static_urls = [
        (base + "/",          "weekly",  "1.0"),
        (base + "/builder",   "weekly",  "0.9"),
        (base + "/checker",   "weekly",  "0.9"),
        (base + "/blog",      "daily",   "0.9"),
        (base + "/about",     "monthly", "0.5"),
        (base + "/contact",   "monthly", "0.4"),
        (base + "/privacy",   "yearly",  "0.3"),
        (base + "/terms",     "yearly",  "0.3"),
    ]
    blog_urls = [(base + f"/blog/{p['slug']}", "monthly", "0.8") for p in posts]
    all_urls  = static_urls + blog_urls

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for loc, freq, pri in all_urls:
        xml += f"  <url><loc>{loc}</loc><changefreq>{freq}</changefreq><priority>{pri}</priority></url>\n"
    xml += "</urlset>"
    return app.response_class(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    base = request.host_url.rstrip("/")
    return app.response_class(
        f"User-agent: *\nAllow: /\nDisallow: /generate\nDisallow: /check-ats\n\nSitemap: {base}/sitemap.xml\n",
        mimetype="text/plain")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "blogs": len(load_all_blogs())})


# ─────────────────────────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("pages/404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("pages/404.html"), 500


# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
