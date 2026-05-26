# HappyRobot FDE Challenge — Master Execution Plan

## Project: Inbound Carrier Sales Automation

A freight brokerage automation system. HappyRobot handles voice (STT, LLM reasoning, TTS) and calls our FastAPI backend via HTTP for FMCSA carrier verification, load search, and post-call data persistence. We expose a dashboard for use-case metrics.

---

## Architecture Overview

```
Carrier (web call)
    ↓
HappyRobot Platform (managed — STT, LLM, TTS, workflow)
    ↓ HTTP requests with API key
Our FastAPI backend (Dockerized, deployed to Fly.io)
    ├── /carriers/verify  → proxies FMCSA QCMobile API
    ├── /loads/search     → queries in-memory loads (loaded from CSV)
    ├── /loads/{id}       → load detail
    ├── /calls            → POST: store call record (SQLite)
    ├── /metrics/summary  → GET: aggregated metrics for dashboard
    ├── /calls            → GET: recent calls for dashboard table
    └── /                 → serves dashboard index.html
```

**Key boundary**: HappyRobot owns all voice/LLM concerns. Our backend is a stateless data API plus a single-page dashboard. SQLite stores only call records (loads come from a CSV loaded into memory at startup).

---

## Repository Structure

```
happyrobot-carrier-sales/
├── README.md                    # Setup, deployment, reproduction
├── Dockerfile
├── .dockerignore
├── .gitignore
├── fly.toml                     # Fly.io deployment config
├── requirements.txt
├── pyproject.toml               # Optional, for ruff/black config
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, route mounting
│   ├── config.py                # Settings via pydantic-settings
│   ├── auth.py                  # X-API-Key dependency
│   ├── db.py                    # SQLite engine, session, init
│   ├── models.py                # SQLModel ORM models
│   ├── schemas.py               # Pydantic request/response models
│   ├── loads.py                 # Load search logic (in-memory)
│   ├── fmcsa.py                 # FMCSA client
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── carriers.py          # /carriers/verify
│   │   ├── loads.py             # /loads/search, /loads/{id}
│   │   ├── calls.py             # POST /calls, GET /calls
│   │   ├── metrics.py           # /metrics/summary
│   │   └── health.py            # /health
│   ├── data/
│   │   └── loads.csv            # Seed loads data (15-20 rows)
│   └── static/
│       └── index.html           # Single-page dashboard
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_loads.py
│   ├── test_carriers.py
│   └── test_calls.py
└── docs/
    ├── happyrobot_workflow.md   # Workflow specification + prompts
    ├── acme_logistics_doc.md    # Build description doc deliverable
    └── carlos_email.md          # Email deliverable
```

---

## Spec Files (read in order)

Each spec file is self-contained and contains everything a coding agent needs to implement that component. Read them in this order:

1. **`01_BACKEND_API.md`** — FastAPI app: all endpoints, models, auth, data layer. This is the biggest spec and the foundation.
2. **`02_HAPPYROBOT_WORKFLOW.md`** — HappyRobot workflow design: nodes, prompts, HTTP action configs, extraction schema.
3. **`03_DASHBOARD.md`** — Single-page HTML dashboard: layout, charts, fetch logic.
4. **`04_DEPLOYMENT.md`** — Dockerfile, fly.toml, deployment steps, env vars.
5. **`05_DELIVERABLES.md`** — README content, Acme Logistics doc, Carlos email, video script.

---

## Critical Conventions

These apply across all files:

- **Python version**: 3.11
- **Framework**: FastAPI + SQLModel (SQLAlchemy 2.x under the hood)
- **Validation**: Pydantic v2
- **Settings**: pydantic-settings, all config from env vars
- **Auth**: single shared `X-API-Key` header on every route except `/health` and `/` (dashboard root)
- **Errors**: return `{"detail": "message"}` with appropriate HTTP status. Use FastAPI's `HTTPException`.
- **Logging**: standard `logging` module, JSON-ish formatter, INFO level by default
- **Timezone**: store all timestamps as UTC ISO 8601 strings in DB
- **Money**: store rates as integers in cents to avoid float issues (e.g. $1,500.00 = 150000). Display as dollars in API responses with two decimal places.
- **No async DB**: use sync SQLModel sessions for simplicity (this is a low-traffic demo)
- **CORS**: allow `*` for the demo — note in docs this would be tightened in prod

---

## Environment Variables

```
API_KEY=<random 32-char hex string>           # required, for our auth
FMCSA_WEBKEY=<key from FMCSA portal>          # required for prod, mockable for dev
DATABASE_URL=sqlite:////data/app.db           # path inside container
LOG_LEVEL=INFO
ENVIRONMENT=production                         # or "development"
ALLOW_MOCK_FMCSA=false                        # if true, returns fake eligibility for testing
```

`.env.example` should ship in the repo with placeholder values.

---

## Timeline (2 days)

### Day 1
- **Morning (4h)**: Build FastAPI backend per `01_BACKEND_API.md`. All endpoints working locally.
- **Afternoon (2h)**: Dockerize + deploy to Fly.io per `04_DEPLOYMENT.md`. Verify HTTPS live URL.
- **Evening (2h)**: Build HappyRobot workflow skeleton per `02_HAPPYROBOT_WORKFLOW.md`. End-to-end web call succeeds.

### Day 2
- **Morning (3h)**: Tune HappyRobot prompts (negotiation logic, extraction, classification). Test 5+ scenarios end-to-end.
- **Midday (2h)**: Build dashboard per `03_DASHBOARD.md`. Verify metrics render correctly.
- **Afternoon (2h)**: Polish — run full happy path + 4 edge cases. Fix anything broken.
- **Evening (2h)**: Write README, Acme doc, Carlos email per `05_DELIVERABLES.md`. Record video.

---

## Definition of Done

Each item must be checked before submission:

- [ ] All 7 API endpoints respond correctly with valid API key
- [ ] All endpoints reject requests without/with wrong API key (401)
- [ ] FMCSA verification works against real API for at least 3 known carrier MCs
- [ ] Loads search returns relevant matches given partial filters
- [ ] HappyRobot workflow completes a full happy-path call (verify → search → pitch → negotiate → agree → mock transfer → post)
- [ ] HappyRobot workflow handles 4 failure modes: not eligible, no match, declined, max rounds reached
- [ ] Call records appear in `/calls` after each completed call
- [ ] Dashboard loads at deployed URL and shows all 6 metric tiles + charts + recent calls table
- [ ] Dashboard auto-refreshes or has a manual refresh button
- [ ] Live deployment accessible at `https://<app>.fly.dev`
- [ ] README contains: setup, env vars, local dev, deploy steps, reproduction commands, architecture diagram
- [ ] Acme Logistics doc complete (1-2 pages)
- [ ] Carlos email drafted
- [ ] 5-min demo video recorded
- [ ] All 6 deliverable links ready (email, doc, dashboard URL, repo, workflow link, video)

---

## Things That Will Bite You (Pre-Read)

1. **FMCSA webkey takes ~1 day to issue.** Request it FIRST THING. Build with `ALLOW_MOCK_FMCSA=true` until the key arrives.
2. **Fly.io SQLite needs a volume.** Without `fly volumes create`, every redeploy wipes the DB.
3. **HappyRobot variable passing is fiddly.** Plan extra time to debug how outputs from one node become inputs to the next.
4. **Negotiation prompts need a hard floor.** Without explicit instructions and a numeric floor (e.g. `min_rate = loadboard_rate * 0.92`), the LLM will agree to anything.
5. **Web call audio quality matters for the demo video.** Quiet room, headset mic, do 2-3 takes.
6. **The dashboard API key.** Don't expose it client-side in production. For this demo, use a separate read-only key or a simple session-based fetch — document the tradeoff in README.

---

## Out of Scope (Document but Don't Build)

- Real phone number / phone call routing (use web call trigger as specified)
- Actual call transfer to sales rep (mock the message)
- OAuth, SSO, multi-tenant auth (single API key is fine)
- Loads CRUD admin UI (loads come from CSV, static)
- Carrier history / repeat-caller recognition
- Database migrations (we run `init_db()` at startup)
- Multi-region deployment, autoscaling
- Webhooks for real-time dashboard updates (polling is fine)
