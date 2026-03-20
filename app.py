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
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/stepfun/step-3.5-flash:free")
DB_PATH = Path("usage.db")
STRIPE_SINGLE = os.getenv("STRIPE_PAYMENT_LINK_SINGLE")
STRIPE_MONTHLY = os.getenv("STRIPE_PAYMENT_LINK_MONTHLY")
STRIPE_ANNUAL = os.getenv("STRIPE_PAYMENT_LINK_ANNUAL")

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
    """ )
    conn.commit()
    conn.close()

init_db()

# Minimal entrypoint guard added for Railway compatibility
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
