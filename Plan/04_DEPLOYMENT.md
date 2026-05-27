# 04 — Deployment Spec

## Goal

Deploy the FastAPI app to Render with HTTPS, SQLite (demo), and reproducible steps. Docker is optional for local testing.

---

## File: `render.yaml`

Blueprint for Render. Creates a free-tier Python web service:

```yaml
services:
  - type: web
    name: acme-carrier-sales
    runtime: python
    plan: free
    region: oregon
    buildCommand: pip install -r requirements.txt
    startCommand: mkdir -p data && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: DATABASE_URL
        value: sqlite:///./data/app.db
      - key: SEED_DEMO_DATA
        value: "true"
      - key: LOG_LEVEL
        value: INFO
      - key: API_KEY
        sync: false
```

**Notes**:
- Replace `acme-carrier-sales` with your preferred service name (must be unique within your Render account).
- `API_KEY` with `sync: false` prompts you to set the secret in the Render dashboard on first deploy.
- `SEED_DEMO_DATA=true` seeds demo calls when the DB is empty (important on Render free tier — see below).
- HTTPS is automatic at `https://<service-name>.onrender.com`.

---

## File: `Dockerfile` (optional — local Docker only)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

RUN mkdir -p /data
ENV DATABASE_URL=sqlite:////data/app.db
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:${PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
```

---

## File: `.dockerignore`

```
.venv
__pycache__
*.pyc
.pytest_cache
.ruff_cache
.git
.gitignore
.env
*.db
tests/
Plan/
creds.txt
inbound-carrier-sales-new-v1.json
```

---

## File: `.env.example`

```
API_KEY=replace-with-32-char-hex
DATABASE_URL=sqlite:///./app.db
LOG_LEVEL=INFO
SEED_DEMO_DATA=false
```

---

## Deployment Steps (First Time)

### Prerequisites

1. Sign up at [render.com](https://render.com) (GitHub login works)
2. Push this repo to GitHub (Render deploys from Git)

### Option A — Blueprint (recommended)

1. In Render dashboard: **New → Blueprint**
2. Connect your GitHub repo
3. Render reads `render.yaml` and creates the web service
4. When prompted, set **`API_KEY`** (use your existing key or generate one):

   ```bash
   python3 -c "import secrets; print(secrets.token_hex(16))"
   ```

5. Click **Apply** and wait for the deploy (~2–3 min)
6. Open `https://<service-name>.onrender.com/`

### Option B — Manual web service

1. **New → Web Service** → connect repo
2. Settings:
   - **Runtime**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `mkdir -p data && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health check path**: `/health`
3. Environment variables:

   | Key | Value |
   |-----|-------|
   | `PYTHON_VERSION` | `3.11.9` |
   | `API_KEY` | your secret key |
   | `DATABASE_URL` | `sqlite:///./data/app.db` |
   | `SEED_DEMO_DATA` | `true` |
   | `LOG_LEVEL` | `INFO` |

4. **Plan**: Free
5. Deploy

### Verify

```bash
export URL=https://acme-carrier-sales.onrender.com
export API_KEY=your-key-here

curl "$URL/health"
# Expect: {"status":"ok"}

curl -H "X-API-Key: $API_KEY" "$URL/loads/search"
# Expect: list of loads from CSV

open "$URL/"
# Enter API key in the dashboard prompt
```

---

## Subsequent Deploys

Push to the connected branch — Render auto-deploys (if `autoDeploy` is enabled, which is the default).

Or trigger manually from the Render dashboard: **Manual Deploy → Deploy latest commit**.

---

## Local Docker Run (Optional)

```bash
docker build -t carrier-sales .

docker run --rm -p 8000:8000 \
  -e API_KEY=test-key-123 \
  -e SEED_DEMO_DATA=true \
  -e DATABASE_URL=sqlite:////data/app.db \
  -v "$(pwd)/data:/data" \
  carrier-sales

curl http://localhost:8000/health
curl -H "X-API-Key: test-key-123" http://localhost:8000/loads/search
```

---

## SQLite on Render

| Scenario | Behavior |
|----------|----------|
| Free tier | Ephemeral disk — **DB wiped on each new deploy** |
| Same instance, no redeploy | SQLite file persists between restarts |
| After idle spin-down | Instance may restart; data usually persists until next deploy |
| Paid + persistent disk | Attach a disk at `/data` and set `DATABASE_URL=sqlite:////data/app.db` |

For this demo, `SEED_DEMO_DATA=true` re-populates the dashboard after a fresh deploy. Real call data from HappyRobot persists until the next deploy on free tier.

---

## Cost Estimate

Render free tier (2025–2026):

- **1 free web service** (512 MB RAM)
- **750 instance-hours/month** included
- Service **spins down after ~15 min idle** — first request after idle takes ~30–60s (cold start)
- **HTTPS included** at `*.onrender.com`
- **No credit card required** for free tier

Expect **$0/month** for a demo/challenge at low traffic.

Upgrade to Starter (~$7/mo) if you need: always-on (no spin-down), persistent disk, or more RAM.

---

## Operational Commands

Use the Render dashboard:

- **Logs** — real-time deploy and runtime logs
- **Environment** — view/edit `API_KEY` and other vars
- **Events** — deploy history
- **Shell** — available on paid plans

---

## Security Notes

What's implemented:

- HTTPS via Render (automatic TLS)
- API key auth on every data endpoint
- Secrets stored in Render environment (not in repo)

What would be added in prod:

- Persistent Postgres instead of SQLite
- Rate limiting (`slowapi`)
- Narrow CORS from `*` to known origins
- Separate read/write API keys

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Deploy fails on build | Missing `requirements.txt` or Python version | Check build logs; confirm `PYTHON_VERSION=3.11.9` |
| `/health` times out on first visit | Free tier cold start after idle | Wait 30–60s; retry |
| App crashes on startup | `API_KEY` not set | Set in Render **Environment** tab |
| Dashboard empty after redeploy | Expected on free tier | `SEED_DEMO_DATA=true` re-seeds demo data |
| Dashboard shows auth failed | Wrong API key | Match dashboard input to Render `API_KEY` env var |
| HappyRobot HTTP action times out | Cold start | Hit `/health` once before demo, or upgrade to Starter |

---

## HappyRobot config

Set your workflow `API_BASE_URL` to:

```
https://<service-name>.onrender.com
```
