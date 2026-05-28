# Inbound Carrier Sales Automation

**Built for Acme Logistics · Powered by HappyRobot**

---

## The problem

Carriers call freight brokers during business hours looking to book loads. Each inbound call ties up a broker for 8–12 minutes on MC verification, lane matching, rate negotiation, and paperwork handoff. Call volume scales with the business; broker headcount does not. After hours and peak windows, calls go unanswered or sit in queue.

## What we built

An AI voice agent that answers inbound carrier calls, verifies authority via FMCSA (inside the HappyRobot workflow), searches your load board, pitches the best lane match, negotiates within policy you control, and records structured outcomes for your team. Humans step in only when a deal is booked (mock transfer in the POC) or when the caller is ineligible, declines, or cannot agree on rate.

## How a call goes

1. **Carrier dials in** (web call or phone) and reaches Alex, the Acme Logistics broker persona.
2. **MC captured and verified** — the agent collects the MC number and confirms company name against FMCSA before proceeding.
3. **Lane intent gathered** — origin, destination, equipment, and pickup timing (as the caller provides them).
4. **Load search** — the agent calls your backend `GET /loads/search` and pitches the top match (e.g. Chicago → Dallas dry van at $1,850).
5. **Negotiation** — up to three rounds using a deterministic policy (92% floor of loadboard rate by default; configurable). The agent can call `GET /negotiation/counter` for the next spoken counter-offer.
6. **Close** — on agreement, mock transfer to your sales desk for paperwork; on failure, polite wrap-up. Post-call, structured data is written to `POST /calls` and appears on the dashboard within seconds.

## Capabilities

- **Live FMCSA verification** on every inbound (HappyRobot tool → FMCSA; not cached across calls)
- **Lane matching** against your load inventory (15 demo loads from CSV; substring match on city/state, equipment, pickup date)
- **Configurable negotiation** — floor as % of loadboard (default 92%), max 3 rounds, split-the-difference round 1, firm floor on round 3
- **Spoken rate amounts** — negotiation API returns `rate_words` (e.g. “nineteen hundred fifty dollars”) for natural TTS
- **Automatic extraction** — carrier, load, agreed rate, rounds, outcome, sentiment from transcript
- **Operations dashboard** — conversion, rate delta, sentiment, outcome mix, recent calls with follow-up actions

## What we measure (dashboard)

| Metric | What it tells you |
|--------|-------------------|
| Total inbound volume | Call traffic over time |
| Booking rate | Share of calls ending in `booked` |
| Avg negotiation rounds | How hard carriers push on rate |
| Avg rate delta vs loadboard | $ and % vs listed rate on booked loads |
| Carrier eligibility rate | FMCSA-pass rate (when `eligible` is posted) |
| Outcome breakdown | booked, no_match, no_agreement, declined, not_eligible, abandoned, error |
| Sentiment breakdown | positive, neutral, negative per call |

**Live dashboard:** [https://case-study-carrier-load-negotiatior.onrender.com/](https://case-study-carrier-load-negotiatior.onrender.com/)

## Demo loads (pilot inventory)

| Load ID | Lane | Equipment | Loadboard rate |
|---------|------|-----------|----------------|
| L-1001 | Chicago IL → Dallas TX | Dry Van | $1,850 |
| L-1003 | Atlanta GA → Miami FL | Dry Van | $1,650 |
| L-1002 | Los Angeles CA → Phoenix AZ | Reefer | $1,400 |

Full list: `app/data/loads.csv` in the repo (15 lanes).

## Security

- **HTTPS** on all public endpoints (`*.onrender.com`, auto TLS)
- **API key** on every data endpoint (`X-API-Key` header); `/health` and dashboard shell are public; metrics require the key in the browser session
- **Secrets** in Render environment variables and HappyRobot workflow settings — never committed to git (`.env` is gitignored)
- **FMCSA** queried at conversation time via HappyRobot; no stale eligibility cache in the backend
- **CORS** open for demo; production would restrict origins to your broker portal and HappyRobot

## Deployment + ops

| Item | Detail |
|------|--------|
| **Hosting** | [Render](https://render.com) — web service `case-study-carrier-load-negotiatior` |
| **Runtime** | Python 3.11, FastAPI, Uvicorn |
| **Storage** | SQLite (`./data/app.db` on Render; ephemeral on free tier — see note below) |
| **Container** | `Dockerfile` available for local parity |
| **Health** | `GET /health` → `{"status":"ok"}` |
| **Deploy** | Connect GitHub repo → Render auto-deploy on push |
| **Demo data** | `SEED_DEMO_DATA=true` seeds 15 sample calls when DB is empty; `POST /calls/seed-demo?force=true` refreshes |
| **Est. infra cost** | Render free tier for pilot; Starter + persistent disk for production call history |

**Ephemeral disk (Render free tier):** When the service spins down or redeploys, the SQLite file on local disk is reset. Demo seeding restores dashboard metrics; live HappyRobot `POST /calls` data is lost unless you attach a persistent disk or use a managed database.

## Integration reference (for your IT / HappyRobot admin)

**Base URL (production):** `https://case-study-carrier-load-negotiatior.onrender.com`

**HappyRobot workflow variables:**

| Variable | Value |
|----------|--------|
| `API_BASE_URL` | `https://case-study-carrier-load-negotiatior.onrender.com` |
| `API_KEY` | `b579df0be405ff684f8892068c434a2b` |
| `NEGOTIATION_FLOOR_PCT` | `0.92` |
| `MAX_NEGOTIATION_ROUNDS` | `3` |
| `BROKER_NAME` | `Acme Logistics` |

**Backend tools (HTTP, header `X-API-Key: @API_KEY`):**

| Tool | Method | URL |
|------|--------|-----|
| Search loads | GET | `@API_BASE_URL/loads/search` |
| Negotiation counter | GET | `@API_BASE_URL/negotiation/counter` |
| Save call | POST | `@API_BASE_URL/calls` |

**OpenAPI / API docs:** [https://case-study-carrier-load-negotiatior.onrender.com/docs](https://case-study-carrier-load-negotiatior.onrender.com/docs)

**Source code:** [https://github.com/mobuffon/case_study_carrier_load_negotiatior](https://github.com/mobuffon/case_study_carrier_load_negotiatior)

**Workflow export (backup):** `inbound-carrier-sales-new-v1.json` in repo  
**Workflow IDs (HappyRobot builder):** use case `019e426e-6d5d-76de-8dd5-0d06095933bc`, org `019e426d-1147-7c49-a458-868d2b037dfb`  
**Builder:** [https://builder.happyrobot.ai/](https://builder.happyrobot.ai/) — paste your share link in the submission email when generated from the UI

## What's next (v2 priorities)

1. **Persistent database** — Render disk or Postgres so call history survives deploys and spin-down
2. **Live load board** — replace CSV with TMS / load-board API connector
3. **Per-broker API keys** — rotate keys per customer, audit log per tenant
4. **Repeat caller recognition** — greet by name, surface prior lanes and rates
5. **CRM / TMS sync** — push booked loads to your system of record automatically
6. **Spanish lane** — ~20% of US trucking; bilingual agent variant
7. **Alerting** — Slack/email when negotiation exceeds discount thresholds or sentiment is strongly negative

## How to evaluate this pilot

Track for 30 days:

- **Broker hours saved** — (calls handled by agent × avg human handle time) − oversight time
- **Coverage** — calls answered outside 9–5 vs baseline
- **Booking rate parity** — agent `booked` % vs human team on same lanes
- **Rate integrity** — % of booked deals at or above floor; avg delta vs loadboard
- **Carrier experience** — spot-check transcripts; sentiment trend; callback rate

If booking rate and rate discipline match human brokers on pilot lanes, expand equipment types and integrate live inventory.

---

*Document version: May 2026 · POC for HappyRobot FDE technical challenge*
