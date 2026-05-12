"""
app.py — ResumeATS (Flask)
--------------------------
Routes:
  GET  /           → Resume builder page
  GET  /checker    → ATS checker page
  POST /generate   → Build + download PDF
  POST /check-ats  → Upload PDF → return ATS score JSON
  GET  /sitemap.xml
  GET  /robots.txt
  GET  /health
"""

from __future__ import annotations
import io, json, os
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "resumeats-2024")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max upload

from resume_builder import build_resume
from resume_model import resume_from_dict
from ats_checker import score_resume


# ─────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/checker")
def checker():
    return render_template("checker.html")


# ─────────────────────────────────────────────────────────────────────────────
# API: GENERATE PDF
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# API: ATS CHECKER
# ─────────────────────────────────────────────────────────────────────────────

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
            return jsonify({"error": "File appears to be empty"}), 400

        result = score_resume(pdf_bytes)
        return jsonify(result)

    except Exception as e:
        app.logger.error(f"ATS check error: {e}")
        return jsonify({"error": "Could not analyze file. Make sure it is a valid PDF."}), 500


# ─────────────────────────────────────────────────────────────────────────────
# SEO
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/sitemap.xml")
def sitemap():
    base = request.host_url.rstrip("/")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{base}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>{base}/checker</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
</urlset>"""
    return app.response_class(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    return app.response_class(
        "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n",
        mimetype="text/plain",
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
