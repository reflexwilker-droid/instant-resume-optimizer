# Instant Resume Optimizer - Installation & Deployment

## Local Setup

### 1. Install dependencies
```bash
pip install flask flask-limiter requests reportlab gunicorn
```

### 2. Configure environment
Create `.env` file:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
SECRET_KEY=random-32-char-string-for-flask-sessions
```

Optional (for payments):
```bash
# For single rewrite payments
STRIPE_PAYMENT_LINK_SINGLE=https://buy.stripe.com/...

# For monthly subscription
STRIPE_PAYMENT_LINK_MONTHLY=https://buy.stripe.com/...

# For annual subscription
STRIPE_PAYMENT_LINK_ANNUAL=https://buy.stripe.com/...
```

Generate a secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(16))"
```

### 3. Run locally
```bash
python3 app.py
# Visit http://localhost:5000
```

## Free Deployment (Railway.app)

1. Push code to GitHub repository
2. Sign up at [railway.app](https://railway.app) with GitHub
3. Create new project from repo
4. Add environment variables in Railway dashboard:
   - `OPENROUTER_API_KEY`
   - `SECRET_KEY`
   - Optional Stripe links
5. Deploy — Railway gives you a random subdomain (e.g., `resume-optim.up.railway.app`)
6. Done. Free tier includes $5 monthly credit (enough for thousands of rewrites).

## Alternative: Render.com

1. Create Web Service from repo
2. Environment: Python 3
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add env vars as above
6. Free tier with 750 hours/month (enough for 24/7)

## Custom Domain (Optional $10-15/year)
- Purchase domain (Namecheap, Porkbun, Cloudflare)
- Add CNAME pointing to your Railway/Render URL
- Update `app.py` `SERVER_NAME` config if needed

## Post-Deployment Checklist
- [ ] Test free rewrite flow
- [ ] Test payment flow (use Stripe test mode first)
- [ ] Verify SQLite DB is created and writable
- [ ] Set up rate limiting (default: 3 free rewrites/hour, 10/day)
- [ ] Add your domain to `.env` if using custom domain
- [ ] Monitor logs for errors

## Cost Breakdown
- **Hosting:** $0 (free tier sufficient for 10k-50k visitors/month)
- **Domain:** ~$12/year (optional)
- **Payment fees:** 2.9% + $0.30 per transaction (Stripe)
- **AI costs:** ~$0.0015–0.003 per rewrite (OpenRouter free/low-cost models)

**Break-even:** ~50 single rewrites or 10 monthly subscriptions covers domain + any minor costs.

## Support & Monitoring
- Check Railway/Render logs for errors
- Set up UptimeRobot free monitoring to ping home page every 5 min
- Use simple analytics: Google Analytics or Plausible (free tier)

Need help? Check errors in host logs — common issues:
- Missing environment variables
- File permissions for SQLite
- OPENROUTER_API_KEY invalid/expired
