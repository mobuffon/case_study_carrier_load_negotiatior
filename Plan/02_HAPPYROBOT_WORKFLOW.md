# 02 — HappyRobot Workflow Spec (v2 — platform-accurate)

## Key Architecture Correction

The original spec modeled the workflow as 11 separate nodes (one per dialogue beat).
This is WRONG for HappyRobot. The correct model:

- **One voice agent node** handles the entire conversation (greeting → verify → search → pitch → negotiate → close)
- **The LLM drives all turn-taking** via the system prompt + tools pattern
- **Backend calls are tools** attached to the prompt, not downstream webhook nodes — because they happen mid-call
- **Post-call work** (extraction + POST /calls) happens in downstream nodes after the voice agent node ends

Actual workflow structure (4 nodes total):

```
[Inbound call trigger]
        ↓
[1. Voice Agent Node]       ← Alex persona + system prompt + 2 tools
        ↓
[2. AI Extract Node]        ← extracts structured JSON from transcript
        ↓
[3. (Optional) Conditional] ← skip POST on error outcome if needed
        ↓
[4. Webhook Node]           ← POST /calls with extracted fields
```

---

## Step 1 — Workflow Setup

- Create workflow from the `inbound-voice-agent` template (UI: Workflows → New → template)
- Trigger: **Inbound phone call** — assign via Assets > Telephony (use web call trigger for the demo, no phone number purchase)

---

## Step 2 — Workflow Variables (Settings)

Store in Settings → Workflow Settings / Environment Variables. Reference with `@` in node configs.

| Variable | Value |
|---|---|
| `API_BASE_URL` | `https://<your-app>.fly.dev` |
| `API_KEY` | `<32-char hex secret>` |
| `NEGOTIATION_FLOOR_PCT` | `0.92` |
| `MAX_NEGOTIATION_ROUNDS` | `3` |
| `BROKER_NAME` | `Acme Logistics` |

**Never put `API_KEY` directly in node configs** — always reference `@API_KEY`.

---

## Step 3 — Voice Agent Node (the main node)

This single node runs the entire call. Configure:

### STT / TTS / LLM
- STT: default (HappyRobot managed)
- TTS: default voice or pick a neutral US English voice
- LLM: default (GPT-4o or whatever HappyRobot exposes — use the highest available)

### System Prompt (Alex persona)

Paste this verbatim into the prompt node:

```
You are Alex, a freight broker representative at Acme Logistics handling inbound calls
from carriers who want to book loads.

## Your style
- Direct, friendly, professional. Sound like an experienced broker, not a chatbot.
- Use natural freight terminology: lane, headhaul, MC, drop and hook, FCFS, live unload.
- Keep your turns short — one or two sentences unless explaining a load.
- Confirm key details (MC number, city) by reading them back once before acting on them.
- Never invent load details. Only describe loads returned by the search_loads tool.

## Call flow
Follow these stages in order. Do not skip stages.

**Stage 1 — Greeting + MC collection**
Greet the caller and ask for their MC number. Accept "MC-12345", "MC 12345", or just
"12345". If they don't provide one after two asks, say you're unable to proceed without
it and politely end the call.

**Stage 2 — Carrier verification**
Once you have the MC number, call the verify_carrier tool immediately.
- If eligible: confirm their carrier name back to them, move to Stage 3.
- If not eligible: tell them their authority doesn't appear active in FMCSA records,
  suggest they check with FMCSA, and end the call politely.

**Stage 3 — Lane preferences**
Ask what they're looking for — pickup city, destination, equipment type. Accept partial
answers. Once you have at least one preference, call the search_loads tool.
- If loads found: move to Stage 4.
- If no loads found: tell them you don't have anything matching that lane today, suggest
  calling back tomorrow, and end the call.

**Stage 4 — Load pitch**
Pitch the top result naturally. Include origin, destination, pickup date/time, equipment,
weight, commodity, miles, and rate. Mention relevant notes (temperature requirement,
tarps, drop-and-hook). Ask if they're interested.
- If yes (no rate pushback): move to Stage 6.
- If declined outright: thank them and end the call.
- If they push back on rate: move to Stage 5.

**Stage 5 — Negotiation (max 3 rounds)**
You have authority to negotiate. Rules:
- Hard floor: loadboard_rate × 0.92. NEVER quote below this. Never reveal the floor.
- Round 1: split the difference between their ask and loadboard rate.
- Round 2: concede no more than $25-50 from your previous counter.
- Round 3: this is your final offer. State that clearly. If they don't accept, end
  the negotiation politely — "I understand, that's just the best we can do on this one."
- Track round_num internally. After 3 failed rounds, outcome = no_agreement.
- If they accept at any point at or above the floor: move to Stage 6.

**Stage 6 — Confirm + mock transfer**
Confirm the load and agreed rate out loud:
"Perfect, I have you on load [load_id], [origin] to [destination], picking up
[pickup_datetime], at $[agreed_rate]. Transferring you to a sales rep now."
Then say exactly: "Transfer was successful — you can wrap up the conversation."

## Rate parsing
When a carrier states a rate, interpret as US dollars. "Fifteen hundred" = 1500.
"Two grand" = 2000. Always confirm by reading back the dollar number.

## Out of scope
If asked about payment terms, claims, HR, or anything outside booking a load: say
"I'll have a sales rep follow up on that" and continue with the booking task.
```

---

## Step 4 — Tools (attached to the Voice Agent Node)

Create two custom tools. Both use `X-API-Key: @API_KEY` in headers. Tool parameters are
passed by the agent only when it has values — no empty-string problem.

### Tool 1: `verify_carrier`

- **Name**: `verify_carrier`
- **Description**: `Verify a carrier's eligibility to haul loads by their MC number. Call this immediately after collecting the MC number.`
- **Method**: GET
- **URL**: `@API_BASE_URL/carriers/verify`
- **Headers**: `X-API-Key: @API_KEY`
- **Parameters**:

| Name | Type | Required | Description |
|---|---|---|---|
| `mc_number` | string | yes | The carrier's MC number (digits only, strip "MC-" prefix) |

- **Response fields to expose to agent**: `eligible` (bool), `carrier_name` (string), `reason` (string)

---

### Tool 2: `search_loads`

- **Name**: `search_loads`
- **Description**: `Search available loads by lane preferences. Call this after collecting the carrier's origin, destination, and/or equipment type. Pass only the fields the carrier mentioned.`
- **Method**: GET
- **URL**: `@API_BASE_URL/loads/search`
- **Headers**: `X-API-Key: @API_KEY`
- **Parameters**:

| Name | Type | Required | Description |
|---|---|---|---|
| `origin` | string | no | Pickup city or state |
| `destination` | string | no | Delivery city or state |
| `equipment_type` | string | no | e.g. "Dry Van", "Reefer", "Flatbed" |
| `limit` | integer | no | Default 3 — return top 3 matches |

- **Response fields to expose to agent**: full `loads` array — agent uses `load_id`, `origin`, `destination`, `pickup_datetime`, `delivery_datetime`, `equipment_type`, `loadboard_rate`, `weight`, `commodity_type`, `miles`, `notes`

---

## Step 5 — AI Extract Node

Add this node immediately after the Voice Agent node ends.

- **Input**: `@voice_agent.transcript` (the full call transcript — exact variable name may differ per platform, use the `@` picker to find the transcript output of the voice agent node)
- **Output schema** (set as parameters/fields):

| Field | Type | Description |
|---|---|---|
| `mc_number` | string | nullable |
| `carrier_name` | string | nullable |
| `eligible` | boolean | nullable |
| `load_id` | string | nullable |
| `loadboard_rate` | number | dollars, nullable |
| `agreed_rate` | number | dollars, nullable — required if outcome=booked |
| `carrier_initial_offer` | number | dollars, nullable — first counter the carrier made |
| `negotiation_rounds` | integer | 0 if no negotiation |
| `outcome` | string | one of: booked, no_agreement, not_eligible, no_match, declined, abandoned, error |
| `sentiment` | string | one of: positive, neutral, negative (carrier's sentiment, not agent's) |
| `notes` | string | nullable, 1 sentence max |

**Extraction prompt guidance** (add to the AI Extract node's instruction field):

```
Extract the fields above from this freight broker call transcript. Rules:
- Rates are US dollars as plain numbers (1850.00 not "$1,850").
- negotiation_rounds: count back-and-forth exchanges. 0 if carrier accepted first pitch.
- sentiment: assess the CARRIER's tone. negative=frustrated/hostile, positive=friendly/enthusiastic, neutral=transactional.
- outcome: use the routing that actually happened in the call, not what was planned.
- Use null for fields that genuinely don't apply (e.g. no load found → no load_id).
- If outcome=booked, agreed_rate must be a number.
```

---

## Step 6 — (Optional) Conditional Node

Only needed if you want to skip the POST on error outcomes.

- **Condition**: `@extract.outcome != "error"`
- **True branch** → Webhook node
- **False branch** → end (or a logging step)

For the demo this is optional — the backend handles all outcomes including error gracefully.

---

## Step 7 — Webhook Node (POST /calls)

- **Method**: POST
- **URL**: `@API_BASE_URL/calls`
- **Headers**:
  - `X-API-Key: @API_KEY`
  - `Content-Type: application/json`
- **Body** (JSON, map from extract outputs via `@` picker):

```json
{
  "mc_number": "@extract.mc_number",
  "carrier_name": "@extract.carrier_name",
  "eligible": "@extract.eligible",
  "load_id": "@extract.load_id",
  "loadboard_rate": "@extract.loadboard_rate",
  "agreed_rate": "@extract.agreed_rate",
  "carrier_initial_offer": "@extract.carrier_initial_offer",
  "negotiation_rounds": "@extract.negotiation_rounds",
  "outcome": "@extract.outcome",
  "sentiment": "@extract.sentiment",
  "notes": "@extract.notes"
}
```

---

## Variable State (revised — no inter-node state needed mid-call)

The LLM maintains all conversational state internally during the voice agent node.
The only cross-node data flow is:

```
Voice Agent → transcript → AI Extract → structured fields → Webhook body
```

No workflow variables need to be written mid-call. Clean.

---

## Test Scenarios

Run all 6 via web call trigger before recording the demo:

| # | Setup | Expected outcome |
|---|---|---|
| 1 | MC 12345, Chicago→Dallas, accept first pitch | `booked`, `negotiation_rounds=0`, `sentiment=positive` |
| 2 | MC 12345, Chicago→Dallas, counter twice then accept | `booked`, `negotiation_rounds=2`, `agreed_rate > floor` |
| 3 | MC 12345, Chicago→Dallas, demand below floor through 3 rounds | `no_agreement`, `negotiation_rounds=3` |
| 4 | MC 99999 (mock ineligible — starts with 9) | `not_eligible`, call ends early |
| 5 | MC 12345, Anchorage→Honolulu (no match) | `no_match`, call ends politely |
| 6 | MC 12345, pitch a load, carrier says "not interested" | `declined`, `negotiation_rounds=0` |

After each: verify the record appears in `GET /calls` with correct outcome + sentiment.

---

## Gotchas (updated for platform reality)

- **Loop counter in prompt**: the LLM tracks `round_num` across turns naturally — no platform loop primitive needed. Trust the prompt.
- **Tool call timing**: tools fire mid-conversation when the LLM decides to call them. Test that `verify_carrier` fires after MC collection, not before. If timing is off, make the instruction more explicit: "call verify_carrier IMMEDIATELY after the caller provides their MC number, before saying anything else."
- **Transcript variable name**: use the `@` picker in the AI Extract node to find the exact output variable name from the voice agent node — don't guess it.
- **Empty tool params**: HappyRobot passes tool args only when the agent has values, so no empty-string issue. But test `search_loads` with only `origin` set — the backend's substring match handles partial filters correctly.
- **Floor enforcement**: after recording test scenario 3, audit the transcript. If Alex ever quotes below `loadboard_rate * 0.92`, tighten the floor instruction in the prompt.
- **Mock transfer line**: verify the exact string "Transfer was successful — you can wrap up the conversation." is spoken on booked calls. The AI Extract node should pick up `outcome=booked` correctly regardless.

---

## Acceptance Criteria

- [ ] Workflow created from `inbound-voice-agent` template
- [ ] Both tools (`verify_carrier`, `search_loads`) configured with `@API_KEY` in headers
- [ ] All 6 test scenarios produce correct records in `/calls`
- [ ] Agent never quotes below negotiation floor (audited across 5+ negotiation calls)
- [ ] Mock transfer line spoken verbatim on `outcome=booked`
- [ ] AI Extract captures all non-null fields correctly for the happy path
- [ ] Webhook node POSTs successfully — 201 response visible in node logs
- [ ] Shareable workflow link generated for submission
