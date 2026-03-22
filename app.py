#!/usr/bin/env python3
"""
Instant Resume Optimizer - Flask web app
Faceless, automated AI resume rewriting with optional PDF output.
"""

import os
import sys
import sqlite3
import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import requests
from requests.exceptions import HTTPError
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.colors import black, navy

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-this")

# Rate limiter: identify by IP
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
DB_PATH = Path("usage.db")
STRIPE_SINGLE = os.getenv("STRIPE_PAYMENT_LINK_SINGLE")
STRIPE_MONTHLY = os.getenv("STRIPE_PAYMENT_LINK_MONTHLY")
STRIPE_QUARTERLY = os.getenv("STRIPE_PAYMENT_LINK_QUARTERLY")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not set in environment")

# ————————————————— DB Setup —————————————————
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS usage (
        id INTEGER PRIMARY KEY,
        ip TEXT,
        email TEXT,
        rewrites_today INTEGER DEFAULT 0,
        rewrites_total INTEGER DEFAULT 0,
        last_rewrite TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ————————————————— Helpers —————————————————
def get_or_create_user(ip: str, email: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if email:
        c.execute("SELECT * FROM usage WHERE ip=? OR email=?", (ip, email))
    else:
        c.execute("SELECT * FROM usage WHERE ip=?", (ip,))
    row = c.fetchone()
    if row:
        user_id, ip_db, email_db, rewrites_today, rewrites_total, last_rewrite, created_at = row
    else:
        now = datetime.datetime.utcnow().isoformat()
        c.execute("INSERT INTO usage (ip, email, rewrites_today, rewrites_total, last_rewrite, created_at) VALUES (?, ?, 0, 0, ?, ?)",
                  (ip, email, now, now))
        conn.commit()
        user_id = c.lastrowid
        rewrites_today = rewrites_total = 0
    conn.close()
    return {"id": user_id, "rewrites_today": rewrites_today, "rewrites_total": rewrites_total}

def increment_usage(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    c.execute("UPDATE usage SET rewrites_today = rewrites_today + 1, rewrites_total = rewrites_total + 1, last_rewrite = ? WHERE id = ?",
              (datetime.datetime.utcnow().isoformat(), user_id))
    # Reset daily counter if last rewrite was yesterday
    c.execute("SELECT last_rewrite FROM usage WHERE id=?", (user_id,))
    (last,) = c.fetchone()
    if last and last.split('T')[0] != today:
        c.execute("UPDATE usage SET rewrites_today = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def check_payment_required(user):
    """Return True if user exceeded free tier (1/month no email, 3/month with email)"""
    if user["rewrites_total"] == 0:
        return False
    return False  # Always free for now; implement later if needed

# ————————————————— AI Rewrite —————————————————
SYSTEM_PROMPT = """You are an expert resume writer. Rewrite the resume to:
- Use strong action verbs and quantifiable achievements
- Optimize for ATS with relevant keywords
- Improve clarity, conciseness, and professional tone
- Keep original sections but rewrite content
- Do NOT invent false information

Return ONLY the improved resume in clean format."""

def call_openrouter(resume_text: str, tone: str = "professional") -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Tone: {tone}\n\nResume:\n{resume_text}"}
    ]
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://instantresume.io",
            "X-Title": "InstantResume"
        },
        json={
            "model": DEFAULT_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4000
        },
        timeout=60
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()

def compile_pdf(resume_text: str) -> bytes:
    """Generate PDF bytes from resume text."""
    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    styles = getSampleStyleSheet()
    story = []
    header_style = ParagraphStyle('Header', parent=styles['Heading1'], fontSize=14, spaceAfter=6, textColor=navy, alignment=1)
    name_style = ParagraphStyle('Name', parent=styles['Heading1'], fontSize=18, spaceAfter=2, textColor=black, alignment=1)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12, spaceBefore=12, spaceAfter=6, textColor=navy)
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.spaceAfter = 3

    lines = resume_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if i == 0 and line and '@' not in line and not line.startswith('http'):
            story.append(Paragraph(line, name_style))
            i += 1
            if i < len(lines) and lines[i].strip():
                story.append(Paragraph(lines[i], header_style))
                i += 1
            continue
        if line and (line.isupper() or line in ['SUMMARY', 'EXPERIENCE', 'EDUCATION', 'SKILLS', 'CERTIFICATIONS', 'PROFESSIONAL SUMMARY']):
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=1, color=navy))
            story.append(Spacer(1, 6))
            story.append(Paragraph(line.title(), section_style))
            i += 1
            continue
        if line.startswith(('•', '-', '*')):
            bullet = line[1:].strip()
            story.append(Paragraph(f"• {bullet}", normal_style))
            i += 1
            continue
        if line:
            story.append(Paragraph(line, normal_style))
            i += 1
        else:
            i += 1
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

@app.route("/tips")
def tips():
    return render_template("tips.html")

# ————————————————— Routes —————————————————
@app.route("/")
def index():
    return render_template("index.html",
        stripe_single=STRIPE_SINGLE,
        stripe_monthly=STRIPE_MONTHLY,
        stripe_quarterly=STRIPE_QUARTERLY
    )

@app.route("/rewrite", methods=["POST"])
@limiter.limit("5 per minute")
def rewrite():
    data = request.json
    resume_text = data.get("resume", "").strip()
    tone = data.get("tone", "professional")
    email = data.get("email", "").strip() or None

    if not resume_text or len(resume_text) < 50:
        return jsonify({"error": "Resume too short"}), 400

    ip = request.remote_addr or "unknown"
    user = get_or_create_user(ip, email)

    # Free tier: 1 rewrite total (no email) or 3/month with email
    if email:
        free_limit = 3
    else:
        free_limit = 1

    if user["rewrites_total"] >= free_limit:
        return jsonify({
            "error": "free_limit_exceeded",
            "message": f"You've used your {free_limit} free rewrite(s). Get unlimited with a subscription.",
            "upgrade_url": STRIPE_MONTHLY or "/#pricing"
        }), 403

    try:
        improved = call_openrouter(resume_text, tone)
        increment_usage(user["id"])
        return jsonify({"success": True, "resume": improved})
    except HTTPError as e:
        # Capture OpenRouter's error response
        try:
            err_json = e.response.json()
            err_msg = err_json.get("error", {}).get("message", str(e))
        except:
            err_msg = e.response.text if e.response else str(e)
        app.logger.error(f"OpenRouter HTTP error: {err_msg}")
        return jsonify({"error": "AI service error", "details": err_msg}), 500
    except Exception as e:
        app.logger.error(f"Rewrite failed: {e}")
        return jsonify({"error": "AI service error", "details": str(e)}), 500

@app.route("/pdf", methods=["POST"])
def generate_pdf():
    data = request.json
    resume_text = data.get("resume", "").strip()
    if not resume_text:
        return jsonify({"error": "No resume provided"}), 400
    try:
        pdf_bytes = compile_pdf(resume_text)
        return send_file(
            BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="resume_optimized.pdf"
        )
    except Exception as e:
        app.logger.error(f"PDF generation failed: {e}")
        return jsonify({"error": "PDF generation failed"}), 500

@app.route("/rewrites_remaining")
def rewrites_remaining():
    """Return how many free rewrites remain for current user/IP."""
    ip = request.remote_addr or "unknown"
    email = request.args.get("email", "").strip() or None
    user = get_or_create_user(ip, email)
    free_limit = 3 if email else 1
    remaining = max(0, free_limit - user["rewrites_total"])
    message = f"You have {remaining} free rewrite(s) remaining today."
    return jsonify({"remaining": remaining, "message": message, "total_used": user["rewrites_total"], "limit": free_limit})

@app.route("/admin")
@limiter.limit("10 per hour")
def admin():
    auth = request.authorization
    if not auth or auth.password != os.getenv("ADMIN_PASSWORD", "admin"):
        return abort(401)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total_users, SUM(rewrites_total) as total_rewrites FROM usage")
    stats = c.fetchone()
    conn.close()
    return jsonify({
        "total_users": stats[0],
        "total_rewrites": stats[1],
        "revenue_estimate": "$0"  # calculate from Stripe webhook later
    })

# Health check for uptime monitors
@app.route("/health")
def health():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)
