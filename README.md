# Instant Resume Optimizer — Complete

AI-powered resume rewriting web service. Faceless, automated, ready to deploy.

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` and `SECRET_KEY`.
3. Run: `python3 app.py`
4. Visit: http://localhost:5000

## Deploy for Free (Railway/Render)

1. Push this folder to GitHub.
2. Create new service on Railway or Render from your repo.
3. Add environment variables in the host dashboard.
4. Deploy. Get your URL.

See `DEPLOY.md` for full instructions.

## Files

- `app.py` — Flask backend (API, DB, rate limiting)
- `templates/index.html` — Frontend one-page app
- `static/style.css` — Styling (responsive, clean)
- `requirements.txt` — Python dependencies
- `Procfile`, `runtime.txt` — For deployment
- `.env.example` — Env vars template
- `DEPLOY.md` — Deployment guide
- `MARKETING.md` — Free marketing tactics
- `business_plan.md` — Business strategy

## Monetization

- Free tier: 1 rewrite (no email) or 3 rewrites total (with email)
- Single rewrite: $7 (Stripe link)
- Monthly unlimited: $15/month
- Annual: $120/year

Set your Stripe Payment Links and add to `.env` as `STRIPE_PAYMENT_LINK_SINGLE`, etc.

## How It Works

1. User pastes resume, selects tone, optionally enters email.
2. Frontend POSTs to `/rewrite` with text.
3. Backend checks usage DB; either serves or returns upgrade prompt.
4. OpenAI rewrites via OpenRouter.
5. User sees result, can copy text or download PDF (via `/pdf` endpoint).
6. If out of free rewrites, Stripe payment link shown.

After payment, manually add user email to a whitelist (or implement webhook later).

## Customization

- Change free limits in `app.py` rewrite() function (`free_limit` variable).
- Update styling in `static/style.css`.
- Edit pricing in `templates/index.html`.
- Adjust AI model/temperature in `call_openrouter()`.

## Cost & Revenue

- **Hosting:** $0 (Railway/Render free tier)
- **Domain:** ~$12/year (optional but recommended)
- **OpenRouter cost:** ~$0.002 per rewrite (negligible at low volume)
- **Stripe fees:** 2.9% + $0.30 per transaction

Break-even: ~50 single rewrites or 10 monthly subs.

## Next Steps

- Deploy to Railway/Render (takes < 10 min).
- Set up Stripe Payment Links.
- Start marketing (Reddit, SEO, etc.).
- Monitor logs, improve conversion.

## Support

- Check `MARKETING.md` for promotion ideas.
- Check `DEPLOY.md` for troubleshooting.
- Health endpoint: `/health` for uptime monitoring.

Good luck! 🚀
