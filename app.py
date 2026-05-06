"""
app.py — Free ATS Resume Builder (Flask)
-----------------------------------------
No database. No login. Pure PDF generation + download.
AdSense-ready, SEO-optimized, mobile-friendly.
"""

from __future__ import annotations
import io, json, os
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ats-resume-builder-2024")

# ── Import PDF builder from your existing code ────────────────────────────────
from resume_builder import build_resume
from resume_model import resume_from_dict


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Accepts JSON resume data → returns PDF bytes.
    No storage. Stateless. Each request is self-contained.
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Validate required fields
        contact = data.get("contact", {})
        if not contact.get("name", "").strip():
            return jsonify({"error": "Name is required"}), 400
        if not contact.get("email", "").strip():
            return jsonify({"error": "Email is required"}), 400
        if not data.get("experience"):
            return jsonify({"error": "At least one experience entry is required"}), 400

        resume = resume_from_dict(data)
        pdf_bytes = build_resume(resume)

        safe_name = contact.get("name", "Resume").replace(" ", "_")
        filename = f"{safe_name}_ATS_Resume.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        app.logger.error(f"PDF generation error: {e}")
        return jsonify({"error": "Failed to generate PDF. Please check your data."}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


# ─────────────────────────────────────────────────────────────────────────────
# SITEMAP  (helps Google index the site)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/sitemap.xml")
def sitemap():
    base = request.host_url.rstrip("/")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    return app.response_class(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    return app.response_class(
        "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n",
        mimetype="text/plain",
    )


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
