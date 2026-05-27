# 05 — Deliverables Spec

The brief requires 6 deliverables. This file specs them all.

---

## Deliverable 1: README.md (in repo root)

Required sections, in this order:

### 1. Title + 1-paragraph summary
"HappyRobot Carrier Sales is an automated inbound call agent for freight brokers. Carriers call in, get verified against FMCSA, hear matching loads, negotiate rate, and book — all without a human broker on the line. Built for the HappyRobot FDE technical challenge."

### 2. Live links table
```
| Resource | URL |
|---|---|
| Live API | https://<app>.fly.dev |
| Dashboard | https://<app>.fly.dev/ |
| API docs (OpenAPI) | https://<app>.fly.dev/docs |
| HappyRobot workflow | <link to workflow in HappyRobot> |
| Demo video | <link to Loom/Drive video> |
```

### 3. Architecture
Embed the architecture diagram (export the structural diagram from earlier as SVG/PNG, save to `docs/architecture.png`, reference here). Below the image, a short prose description of the request flow.

### 4. Tech stack
- Backend: FastAPI, SQLModel, Pydantic v2, httpx, uvicorn (Python 3.11)
- Storage: SQLite with persistent volume (loads sourced from CSV in-memory)
- Frontend: vanilla HTML + Chart.js (no build step)
- Deployment: Docker → Fly.io (Let's Encrypt HTTPS, persistent volume)
- Voice + LLM: HappyRobot platform (managed STT, TTS, LLM, workflow orchestration)

### 5. API endpoints
A table with method, path, description. Link to `/docs` for full OpenAPI.

### 6. Local development
Copy from `01_BACKEND_API.md` "Local Dev Commands".

### 7. Deployment
Copy from `04_DEPLOYMENT.md` "Deployment Steps (First Time)".

### 8. Reproduction (`Reproduction from scratch`)
Copy from `04_DEPLOYMENT.md` "Reproduction" section.

### 9. Configuration / env vars
Table of every env var, type, default, purpose.

### 10. Testing
"Run `pytest` from repo root."

### 11. HappyRobot workflow setup
Link to `docs/happyrobot_workflow.md` for full node-by-node spec. README has a 5-line summary of what nodes are involved and which endpoints they hit.

### 12. Security
Bullet-list from `04_DEPLOYMENT.md` "Security Notes".

### 13. Limitations + future work
Be honest about what's not built:
- API key in sessionStorage on dashboard (would replace with proper auth)
- Single API key for all clients (would partition per-tenant)
- No call recording storage (HappyRobot handles transcripts)
- Loads are static from CSV (would integrate with TMS/load board APIs)
- No multi-language support (English only)
- No A/B testing infrastructure for negotiation strategies

### 14. License
MIT or unlicensed — your choice.

---

## Deliverable 2: Acme Logistics Build Description (`docs/acme_logistics_doc.md`)

Frame this as something you'd hand to a real freight broker after a successful pilot. Length target: 2 pages of dense markdown (~600-800 words). NOT a code doc — a product/value doc.

Section outline:

### Header
**Inbound Carrier Sales Automation**
Built for Acme Logistics · Powered by HappyRobot

### The problem
2-3 sentences. Carriers call in during business hours. Each call ties up a broker for 8-12 minutes on verification, lane-matching, and rate negotiation. The volume scales with the business; broker headcount doesn't.

### What we built
2-3 sentences. An AI voice agent that takes inbound calls, verifies carriers against FMCSA in real time, pitches matching loads, negotiates within authority you set, and books — handing off to a human only when the deal is done or escalation is needed.

### How a call goes
A short numbered walkthrough (5-6 steps): caller dialed → MC captured and verified → carrier confirmed → loads searched → top match pitched → negotiation (up to 3 rounds, configurable floor) → mock transfer to your sales rep for paperwork.

### Capabilities (concrete list)
- Live FMCSA QCMobile verification (eligibility check on every inbound)
- Lane matching against your load board (origin, destination, equipment, pickup date)
- Configurable negotiation policy (floor as % of loadboard rate, max rounds)
- Automatic data extraction (carrier, load, agreed rate, negotiation history)
- Outcome and sentiment classification per call
- Real-time dashboard with conversion, rate delta, sentiment trends

### What we measure (the dashboard)
- Total inbound volume
- Booking rate (calls → booked deals)
- Average negotiation rounds per call
- Average rate delta vs loadboard (dollars and %)
- Carrier eligibility rate (FMCSA-passes / total)
- Outcome breakdown (booked, no-match, no-agreement, declined, ineligible)
- Sentiment breakdown (positive, neutral, negative)

### Security
- HTTPS everywhere, with auto-renewing certificates
- API-key authentication on every backend endpoint
- Secrets managed via the platform's encrypted secret store, never in code
- Each carrier verification call hits the official FMCSA API — no cached eligibility older than the conversation

### Deployment + ops
- Containerized (Docker), deployed to Fly.io with one command (`fly deploy`)
- Persistent storage for call records on a managed volume
- Health checks + automatic restarts
- Logs streamable on demand (`fly logs`)
- Estimated steady-state cost at Acme's volume: <$10/mo for infrastructure (excluding HappyRobot platform fees)

### What's next (priorities for a v2)
- Integrate live load board feed (replace CSV with API connector)
- Per-broker accounts with rotated API keys
- Carrier history: recognize repeat callers, offer continuity in greeting
- Post-call CRM sync (push booked deals to your TMS automatically)
- Multilingual support for Spanish-speaking carriers (Spanish is ~20% of US trucking)
- Real-time alerting for outlier negotiations (large discounts, hostile sentiment)

### How to evaluate this pilot
Suggest the metrics Acme should track to decide on adoption: hours of broker time saved per week, calls handled outside business hours, booking-rate parity vs human brokers, carrier NPS on the agent.

---

## Deliverable 3: Carlos Becker Email (`docs/carlos_email.md`)

Short, professional, addressed to the prospect ahead of the meeting. Tone: confident but not over-the-top, signaling "this is ready to look at, not a sketch on a napkin."

Recipient: c.becker@happyrobot.ai
CC: <recruiter email — you'll fill this in>
Subject: `Ahead of our meeting — carrier sales POC live`

```
Hi Carlos,

Ahead of our session [day/date — fill in], wanted to share what's ready
on the carrier sales POC.

The agent runs end-to-end on a web call: FMCSA verification on the MC,
lane-matched load pitch, up to three negotiation rounds against a
configurable floor, and a mock handoff once a rate is agreed.

A few links so you can poke around before we meet:
- Live demo: https://<app>.fly.dev
- Dashboard: https://<app>.fly.dev (enter the API key I'll share separately)
- Repo: https://github.com/<user>/happyrobot-carrier-sales
- Workflow in HappyRobot: <link>
- 5-min walkthrough: <video link>

Happy to walk through the negotiation policy in particular — I made it
parameterizable (floor %, max rounds) since that's the lever brokers
will want to tune by lane and season.

Looking forward to it.

Best,
[Your name]
```

Keep it 8 lines of body max. No marketing language. No bullets in the email itself except the link list.

---

## Deliverable 4: Deployed Dashboard

Already covered in `03_DASHBOARD.md` and `04_DEPLOYMENT.md`. The deliverable is just the URL: `https://<app>.fly.dev/`. Include the API key in the email body (or send separately for slightly better hygiene).

---

## Deliverable 5: Code Repository Link

GitHub repo, public (or invite Carlos as a collaborator if private). Must contain everything above. Ensure:
- README is rendered well on GitHub (no broken links, image renders)
- No secrets committed (`.env` in `.gitignore`)
- Commit history is sensible (not one giant "initial commit")
- A short `LICENSE` file if you choose to license

---

## Deliverable 6: HappyRobot Workflow Link

Generate a shareable link to the workflow in your HappyRobot account. Confirm the link allows view-only access from outside your tenant if needed. Otherwise, include screenshots in `docs/happyrobot_workflow.md` as backup.

---

## Deliverable 7: 5-Minute Demo Video

### Script (target 4:30, leave buffer)

**0:00–0:30 — Intro + architecture (30s)**
"Hi, I'm [name]. This is my FDE technical challenge build — an inbound carrier sales agent for HappyRobot. Quick architecture: carriers call into a HappyRobot web agent, which handles voice and LLM. The agent makes HTTP requests to my FastAPI backend deployed on Fly.io for FMCSA verification, load search, and call persistence. The dashboard is a single page served by the same backend."

[Show architecture diagram on screen]

**0:30–3:00 — Demo two calls (2.5min)**

Call 1 — Happy path with negotiation (~90s):
- Click "start web call" in HappyRobot
- Give MC 12345
- Agent verifies, confirms carrier name
- "I'm looking for something out of Chicago"
- Agent pitches L-1001 Chicago→Dallas at $1850
- "Can you do $2000?"
- Agent counters at ~$1925
- "Let's do $1950"
- Agent accepts, mock transfer
- "Notice the agent stayed above the floor and split the difference"

Call 2 — Negotiation failure (~60s):
- New web call, MC 12345
- Ask for Atlanta→Miami
- Agent pitches L-1003 at $1650
- "I need $1400" (below floor)
- Agent counters at $1520 (the floor)
- "$1400 final"
- Agent politely declines, ends call
- "Notice it never quoted below the floor"

**3:00–4:30 — Dashboard tour (90s)**
- Open dashboard URL, enter API key
- "Six KPIs across the top — total calls, booking rate, average rounds, rate delta in dollars and percent, eligibility rate"
- "Outcome breakdown shows the distribution — you can see the two calls we just made"
- "Sentiment is classified per call by the post-call extraction step"
- "Recent calls table at the bottom shows the full record, including the rate negotiated, the rounds, and the sentiment"
- "All of this updates in real time — the dashboard polls every 30 seconds"

**4:30–5:00 — Wrap (30s)**
"That's the build. A few things I'd add next: live load-board integration, per-broker API keys, repeat-caller recognition. Repo and full docs are linked. Happy to walk through any of it in the meeting. Thanks."

### Recording tips

- Use Loom or QuickTime. No editing needed for a single take.
- Test mic level beforehand. Headset > laptop mic.
- Close other tabs and notifications.
- Have the dashboard URL bookmarked and pre-logged-in to a separate browser profile so the auth gate doesn't break the flow (or quickly type the key on screen — that's fine too).
- Do 2 takes minimum. Pick the better one. Don't over-polish.
- Keep mouse cursor calm. Don't wave it.
- Target file size: <100MB. Upload to Loom or Google Drive (with link sharing enabled).

---

## Final Checklist (Submission Day)

- [ ] Repo pushed to GitHub, README renders correctly
- [ ] App deployed to Fly, `/health` returns 200
- [ ] Made 5+ test calls covering all outcome types — all visible in dashboard
- [ ] Dashboard URL works on a fresh browser (no cached auth)
- [ ] OpenAPI docs page (`/docs`) loads correctly
- [ ] FMCSA webkey set in prod (when FMCSA verification is enabled)
- [ ] Negotiation floor verified across 3+ test cases (never quoted below)
- [ ] Video recorded, uploaded, link sharable
- [ ] Carlos email drafted with all links filled in
- [ ] Acme Logistics doc finalized
- [ ] HappyRobot workflow shareable link generated and tested in incognito
- [ ] All 6 deliverable links collected in one place (paste into email)

---

## What to Send Carlos (final email content checklist)

The submission email itself should contain:

1. The drafted message body (per the email template above)
2. All 6 links in the body or as a compact list:
   - Deployed app URL
   - Dashboard URL (+ API key, sent separately or in the body if you're comfortable)
   - GitHub repo
   - HappyRobot workflow share link
   - Video link
   - Acme doc (PDF export of the markdown, or linked from the repo)

Don't attach files if you can avoid it — links are better. If you must attach the video, compress to <25MB.
