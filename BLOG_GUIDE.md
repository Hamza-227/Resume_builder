# ResumeATS — Blog Management & Deployment Guide

Everything you need to publish blogs, maintain the site, and deploy updates.

---

## 📁 Project Structure

```
ats_v2/
│
├── app.py                    ← Flask backend (all 13 routes)
├── blog_engine.py            ← Blog CMS (auto-loads markdown files)
├── ats_checker.py            ← ATS scoring engine (100 points)
├── resume_builder.py         ← PDF generator
├── resume_model.py           ← Pydantic data models
├── resume_parser.py          ← PDF text extractor
│
├── blogs/                    ← ⭐ DROP YOUR .md FILES HERE
│   ├── how-ats-systems-work.md
│   ├── resume-bullet-formulas.md
│   └── linkedin-profile-optimization.md
│
├── static/
│   ├── css/main.css          ← Complete design system
│   ├── js/main.js            ← Core JS (navbar, theme, FAQ, counters)
│   ├── js/home.js            ← Homepage animations
│   ├── js/script.js          ← Builder form + PDF download
│   ├── js/checker.js         ← ATS checker + score animation
│   └── images/blogs/         ← Blog images go here
│
├── templates/
│   ├── base.html             ← Shared nav + footer
│   ├── index.html            ← Homepage
│   ├── builder.html          ← Resume builder
│   ├── checker.html          ← ATS checker
│   ├── blog/
│   │   ├── index.html        ← Blog listing
│   │   └── post.html         ← Individual blog post
│   └── pages/
│       ├── about.html
│       ├── contact.html
│       ├── privacy.html
│       ├── terms.html
│       └── 404.html
│
├── requirements.txt
├── render.yaml               ← Render.com deploy config
└── Procfile                  ← Railway / Heroku
```

---

## ✍️ How to Publish a New Blog Post

**Total time: 5 minutes. No coding required.**

### Step 1 — Create a markdown file

Create a new `.md` file inside the `/blogs/` folder.

**Naming rule:** Use lowercase with hyphens. The filename becomes the URL.
- `my-new-post.md` → `yoursite.com/blog/my-new-post`

### Step 2 — Add the frontmatter header

Copy this template and fill it in at the top of your file:

```markdown
---
title: "Your Blog Post Title Here"
description: "A 1-2 sentence summary for SEO and blog cards. Keep under 160 characters."
image: "/static/images/blogs/your-image.jpg"
category: "Resume Tips"
tags: ["ATS", "Resume", "Career"]
date: "2026-05-20"
author: "ResumeATS Team"
keywords: ["ats resume", "resume tips", "keyword1", "keyword2"]
featured: true
---
```

**Fields explained:**

| Field | Required | Description |
|-------|----------|-------------|
| `title` | ✅ Yes | The blog post headline |
| `description` | ✅ Yes | Short summary shown in cards and Google |
| `image` | Optional | Path to blog image (see Step 3) |
| `category` | ✅ Yes | Groups posts in filters. Pick one: `Resume Tips`, `Resume Writing`, `LinkedIn`, `Career Tips`, `Interview Prep` |
| `tags` | Optional | Array of tags for search |
| `date` | ✅ Yes | Format: `YYYY-MM-DD` |
| `author` | Optional | Defaults to "ResumeATS Team" |
| `keywords` | Optional | SEO keywords for the post |
| `featured` | Optional | Set `true` to show on homepage. Max 3 featured at a time. |

### Step 3 — Add a blog image (optional)

1. Save your image to `/static/images/blogs/`
2. Recommended size: **1200×630px** (landscape, 16:9)
3. Supported formats: `.jpg`, `.png`, `.webp`
4. Reference it in frontmatter: `image: "/static/images/blogs/my-image.jpg"`

If you skip the image, the blog card shows a beautiful gradient placeholder automatically.

### Step 4 — Write your content

After the `---` closing line, write your blog content in Markdown:

```markdown
---
(frontmatter above)
---

# Your H1 Heading

Introduction paragraph here.

## Section Heading

Regular paragraph text. You can use **bold**, *italic*, and `inline code`.

### Sub-section

- Bullet point one
- Bullet point two

## Code Example

```python
def hello():
    print("Hello World")
```

## Checklist

- [ ] Unchecked item
- [x] Checked item
```

**Supported Markdown features:**
- Headings (H1–H4) — H2 generates table of contents
- Bold, italic, strikethrough
- Bullet and numbered lists
- Code blocks with syntax highlighting (python, javascript, bash, etc.)
- Blockquotes
- Tables
- Checklists
- Links and images
- Horizontal rules

### Step 5 — Deploy

```bash
git add blogs/my-new-post.md
git commit -m "Add blog: Your Post Title"
git push
```

**That's it.** The blog post automatically appears:
- ✅ On the `/blog` listing page
- ✅ At `/blog/my-new-post`
- ✅ In the homepage blog preview (if `featured: true`)
- ✅ In search results
- ✅ In category filters
- ✅ In the sitemap.xml
- ✅ With full SEO metadata

---

## 📂 Categories Reference

Use one of these exact strings to keep filters consistent:

```
Resume Tips
Resume Writing
LinkedIn
Career Tips
Interview Prep
Job Search
```

To add a new category, just use a new string — it automatically appears in the filter bar.

---

## 🖼️ Image Best Practices

| Use | Size | Format |
|-----|------|--------|
| Blog hero image | 1200×630px | .jpg or .webp |
| Blog card thumbnail | 800×450px | .jpg or .webp |
| Default fallback | automatic | gradient (no image needed) |

- Compress images before uploading: use [squoosh.app](https://squoosh.app) (free)
- Keep file size under 200KB for fast loading
- Use descriptive filenames: `ats-resume-tips-2024.jpg` not `image1.jpg`

---

## ⭐ Featured Posts

Set `featured: true` in frontmatter to show a post on the homepage.

- The homepage shows up to **3 featured posts**
- If more than 3 are featured, it shows the 3 most recent
- The blog listing page shows the top 2 featured posts at the top

To un-feature a post, set `featured: false` or remove the field.

---

## 🔍 How Search Works

The search function scans: title, description, tags, and category.
No configuration needed — it's automatic.

---

## 📈 SEO — What Happens Automatically

Every blog post automatically gets:

- `<title>` tag: `{post.title} | ResumeATS Blog`
- `<meta description>`: from your `description` field
- `<meta keywords>`: from your `keywords` array
- Open Graph tags (LinkedIn/Facebook preview)
- Twitter Card metadata
- JSON-LD Article schema markup
- Canonical URL
- Entry in `/sitemap.xml`

**After publishing a new post:**
1. Go to [Google Search Console](https://search.google.com/search-console)
2. Enter your new blog URL
3. Click "Request Indexing"
4. Google typically indexes within 24–48 hours

---

## 🚀 Deployment

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python app.py

# Open in browser
http://localhost:5000
```

### Deploy to Railway (Recommended — Free)

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Railway auto-detects Python and uses your `Procfile`
5. Add environment variable: `SECRET_KEY` = any random string
6. Your site is live in ~2 minutes

**To update after publishing a new blog:**
```bash
git add .
git commit -m "Add new blog post"
git push
# Railway auto-deploys in ~1 minute
```

### Deploy to Render (Free Tier)

1. Push to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. The `render.yaml` file auto-configures everything
5. Click Deploy

### Deploy to PythonAnywhere (No Card Required)

1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Go to Files → upload all project files
3. Go to Web → Add new web app → Flask → Python 3.11
4. Set WSGI file to point to `app:app`
5. Click Reload

---

## 🎨 Design Customization

### Change Colors

Open `/static/css/main.css` and find the `:root` block at the top:

```css
:root {
  --accent: #3b82f6;        /* Main blue — change this */
  --navy-950: #020818;      /* Darkest background */
  --grad-text: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%); /* Gradient text */
}
```

### Add a New Nav Link

Open `templates/base.html` and find the nav-menu section:

```html
<div class="nav-menu" id="navMenu">
  <!-- Add your link here -->
  <a href="/your-page" class="nav-item">Your Page</a>
</div>
```

### Add a New Page

1. Create `templates/pages/my-page.html` extending base.html
2. Add a route in `app.py`:
```python
@app.route("/my-page")
def my_page():
    return render_template("pages/my-page.html")
```
3. Add to sitemap in `app.py` → `sitemap()` function

---

## 💰 Monetization Setup

### AdSense (after approval)

In `templates/base.html`, find this comment in `<head>`:
```html
<!-- <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXX" ...></script> -->
```
Uncomment it and replace `ca-pub-XXXXXXXX` with your publisher ID.

Then in any template, add ad units like:
```html
<ins class="adsbygoogle" style="display:block"
     data-ad-client="ca-pub-XXXXXXXX"
     data-ad-slot="XXXXXXXXXX"
     data-ad-format="auto"></ins>
<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script>
```

### Affiliate Links

Open `templates/builder.html` and `templates/checker.html`. Find the sidebar affiliate section:
```html
<a href="https://linkedin.com/premium" class="aff-item" ...>
```
Replace with your actual affiliate URLs from:
- **Grammarly:** grammarly.com/affiliates
- **Coursera:** coursera.org/affiliates  
- **LinkedIn Premium:** Impact.com → search LinkedIn

---

## 🐛 Troubleshooting

**Blog post not appearing?**
- Check filename has `.md` extension
- Check frontmatter has correct `---` delimiters
- Check `date` format is `YYYY-MM-DD`
- Redeploy / restart server

**PDF not generating?**
- Check all required fields are filled (name, email, at least 1 experience)
- Check server logs: `python app.py` shows errors in terminal

**ATS checker failing?**
- PDF must be under 5MB
- PDF must have selectable text (not a scanned image)

**Site not loading after deploy?**
- Check `requirements.txt` has all dependencies
- Check `SECRET_KEY` environment variable is set
- Check `Procfile` exists with correct command

---

## 📊 Content Calendar Suggestion

Publish 1–2 blogs per week for best SEO growth:

| Week | Topic | Category |
|------|-------|----------|
| 1 | "Top 10 ATS Resume Mistakes" | Resume Tips |
| 2 | "How to Write Resume Bullets with Metrics" | Resume Writing |
| 3 | "LinkedIn Profile Checklist 2024" | LinkedIn |
| 4 | "Remote Job Search Strategy" | Career Tips |
| 5 | "STAR Method for Interviews" | Interview Prep |
| 6 | "Salary Negotiation Scripts" | Career Tips |

---

*ResumeATS — Free forever · Built for job seekers · No login required*
