Email to Carlos Becker — submission draft

Copy the "Message body" section into your mail client. Update meeting date, video link, and HappyRobot workflow share URL if you have newer values.


Send settings

To: c.becker@happyrobot.ai
CC: (add recruiter email)
Subject: Ahead of our meeting — carrier sales POC live


Message body (ready to send)

Hi Carlos,

Ahead of our session [ADD DATE/TIME], wanted to share what's ready on the carrier sales POC.

The agent runs end-to-end on a web call: FMCSA verification on the MC (in the HappyRobot workflow), lane-matched load pitch from our API, up to three negotiation rounds against a 92% loadboard floor via /negotiation/counter, and post-call persistence to the dashboard.

Links:

Live API + dashboard: https://case-study-carrier-load-negotiatior.onrender.com/
OpenAPI docs: https://case-study-carrier-load-negotiatior.onrender.com/docs
API key (dashboard + API): b579df0be405ff684f8892068c434a2b — use header X-API-Key on all protected routes; paste into the dashboard gate on first visit
Repo: https://github.com/mobuffon/case_study_carrier_load_negotiatior
Acme build doc: https://github.com/mobuffon/case_study_carrier_load_negotiatior/blob/main/docs/acme_logistics_doc.md
HappyRobot workflow: [PASTE SHARE LINK FROM BUILDER] — use case ID 019e426e-6d5d-76de-8dd5-0d06095933bc (workflow export: inbound-carrier-sales-new-v1.json in repo)
5-min walkthrough: [ADD LOOM / GOOGLE DRIVE VIDEO URL]

HappyRobot env for the workflow:

API_BASE_URL = https://case-study-carrier-load-negotiatior.onrender.com
API_KEY = b579df0be405ff684f8892068c434a2b

Happy to walk through the negotiation policy in particular — floor % and max rounds are the levers brokers tune by lane and season.

Looking forward to it.

Best,
Moritz


Quick test commands (for you, not in the email)

export URL=https://case-study-carrier-load-negotiatior.onrender.com
export API_KEY=b579df0be405ff684f8892068c434a2b

curl "$URL/health"

curl -H "X-API-Key: $API_KEY" "$URL/loads/search?origin=Chicago&limit=3"

curl -H "X-API-Key: $API_KEY" \
  "$URL/negotiation/counter?loadboard_rate=1850&our_offer=1850&carrier_counter=2000&round=1"

curl -X POST -H "X-API-Key: $API_KEY" "$URL/calls/seed-demo?force=true"


Submission checklist

[ ] Replace [ADD DATE/TIME] with your meeting slot
[ ] Generate HappyRobot workflow share link at builder.happyrobot.ai and replace placeholder
[ ] Record demo video and replace [ADD LOOM / GOOGLE DRIVE VIDEO URL]
[ ] Confirm workflow API_BASE_URL points to Render (not ngrok)
[ ] Optional: send API key in a separate email for hygiene (body above includes it for convenience)


All deliverable links (one block)

Deployed app / dashboard: https://case-study-carrier-load-negotiatior.onrender.com/
API docs: https://case-study-carrier-load-negotiatior.onrender.com/docs
GitHub repo: https://github.com/mobuffon/case_study_carrier_load_negotiatior
Acme doc: https://github.com/mobuffon/case_study_carrier_load_negotiatior/blob/main/docs/acme_logistics_doc.md
HappyRobot workflow: [share link from builder]
Demo video: [your Loom/Drive link]
API key: b579df0be405ff684f8892068c434a2b
