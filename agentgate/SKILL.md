# AgentGate

**Pre-action decision API for autonomous agents.**

Before executing a tool or irreversible action, call AgentGate to learn whether the task is **ready**, **needs clarification**, or **unsafe** — and which strategy to choose when multiple options exist.

**Base URL:** https://agentgate-xwqo.onrender.com  
**Auth:** None (public service; no API key required)  
**Content-Type:** `application/json` for all `POST` requests  
**Warm-up:** Call `GET /health` first if the host may have been idle (Render free tier).

---

## Quick reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Liveness check and warm-up |
| POST | `/evaluate-task` | Pre-action readiness, risk, and next step |
| POST | `/compare-options` | Rank 2–5 candidate strategies |
| GET | `/skill.md` | This documentation (agent-readable) |

**Full URLs for registry:**

```
GET  https://agentgate-xwqo.onrender.com/health
POST https://agentgate-xwqo.onrender.com/evaluate-task
POST https://agentgate-xwqo.onrender.com/compare-options
GET  https://agentgate-xwqo.onrender.com/skill.md
```

---

## GET /health

**Purpose:** Confirm the service is reachable. Use at session start and before judging demos.

```bash
curl https://agentgate-xwqo.onrender.com/health
```

**Response (200):**

```json
{
  "status": "ok",
  "service": "agentgate",
  "version": "1.0.0",
  "llm_mode": "rules_only"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"ok"` when healthy |
| `service` | string | Always `"agentgate"` |
| `version` | string | API version |
| `llm_mode` | string | `"rules_only"` or `"rules_with_openrouter_fallback"` |

---

## POST /evaluate-task

**Purpose:** Evaluate a proposed agent action **before** execution. Returns structured status, risk level, missing context, and an explicit instruction for the calling agent.

```bash
curl -X POST https://agentgate-xwqo.onrender.com/evaluate-task \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Send a payment of $5000 to vendor account 99281",
    "goal": "Pay quarterly invoice",
    "available_context": {
      "user_confirmed": false,
      "amount_usd": 5000,
      "recipient_verified": false
    },
    "proposed_action": "stripe.transfer",
    "constraints": ["no_irreversible_without_confirmation"]
  }'
```

### Request body

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `task_description` | **yes** | string | What the agent plans to do (min 1 character) |
| `goal` | no | string | Higher-level user objective |
| `available_context` | no | object | Key-value facts already known (booleans, strings, numbers) |
| `proposed_action` | no | string | Tool or action name (e.g. `stripe.transfer`, `db.drop`) |
| `constraints` | no | string[] | Policy strings such as `no_irreversible_without_confirmation`, `require_human_approval`, `no_pii_export` |

**Useful `available_context` keys:** `user_confirmed`, `recipient_verified`, `backup_exists`, `dates_provided`, `destination_confirmed`, `amount_confirmed`, `human_approved`, `notes_available`.

### Response body (always JSON)

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `ready` \| `needs_clarification` \| `unsafe` \| `incomplete` |
| `risk_level` | string | `low` \| `medium` \| `high` |
| `missing_info` | string[] | Context keys the agent should collect from the user |
| `recommended_next_action` | string | Machine-readable next step (e.g. `proceed_with_proposed_action`, `ask_user_for_missing_fields`, `stop_and_request_human_approval`) |
| `reasoning_summary` | string | Short human-readable explanation |
| `confidence` | number | 0.0–1.0; below 0.6 = weak signal, prefer clarification |
| `agent_instruction` | string | **Direct command for the calling agent — follow this** |

### Example: needs clarification (incomplete flight booking)

**Request:**

```json
{"task_description": "Book flight to Paris"}
```

**Response (200):**

```json
{
  "status": "needs_clarification",
  "risk_level": "medium",
  "missing_info": ["dates_provided", "destination_confirmed"],
  "recommended_next_action": "ask_user_for_missing_fields",
  "reasoning_summary": "Task requires additional context before safe execution: dates_provided, destination_confirmed.",
  "confidence": 0.82,
  "agent_instruction": "Do not execute yet. Ask the user to provide: dates_provided, destination_confirmed. Then call /evaluate-task again with updated available_context."
}
```

### Example: unsafe (high-value payment without confirmation)

**Response (200):**

```json
{
  "status": "unsafe",
  "risk_level": "high",
  "missing_info": ["user_confirmed", "recipient_verified"],
  "recommended_next_action": "stop_and_request_human_approval",
  "reasoning_summary": "Task or action 'stripe.transfer' matches destructive, financial, or security-sensitive patterns without sufficient safeguards.",
  "confidence": 0.95,
  "agent_instruction": "Do not execute stripe.transfer. Request explicit human approval and verify all safety checks before retrying /evaluate-task."
}
```

### Example: unsafe (destructive database action)

```bash
curl -X POST https://agentgate-xwqo.onrender.com/evaluate-task \
  -H "Content-Type: application/json" \
  -d '{"task_description":"Delete production database","proposed_action":"db.drop"}'
```

**Response (200):**

```json
{
  "status": "unsafe",
  "risk_level": "high",
  "missing_info": ["user_confirmed", "backup_exists"],
  "recommended_next_action": "stop_and_request_human_approval",
  "reasoning_summary": "Task or action 'db.drop' matches destructive, financial, or security-sensitive patterns without sufficient safeguards.",
  "confidence": 0.95,
  "agent_instruction": "Do not execute db.drop. Request explicit human approval and verify all safety checks before retrying /evaluate-task."
}
```

### Example: ready (low-risk summarization)

```bash
curl -X POST https://agentgate-xwqo.onrender.com/evaluate-task \
  -H "Content-Type: application/json" \
  -d '{"task_description":"Summarize meeting notes from today","proposed_action":"text.summarize","available_context":{"notes_available":true}}'
```

**Response (200):**

```json
{
  "status": "ready",
  "risk_level": "low",
  "missing_info": [],
  "recommended_next_action": "proceed_with_proposed_action",
  "reasoning_summary": "Task has sufficient context and no blocking safety signals detected.",
  "confidence": 0.85,
  "agent_instruction": "Proceed with text.summarize if it aligns with the user's goal."
}
```

### Errors

| Code | When |
|------|------|
| `422` | Missing or empty `task_description` |
| `500` | Unexpected server error (rare; rules engine always prefers returning 200 with valid JSON) |

---

## POST /compare-options

**Purpose:** When an agent must choose between 2–5 strategies, AgentGate ranks them and returns the best option with reasoning.

```bash
curl -X POST https://agentgate-xwqo.onrender.com/compare-options \
  -H "Content-Type: application/json" \
  -d '{
    "decision_goal": "Choose how to fetch weather for user trip planning",
    "options": [
      {
        "id": "opt_a",
        "label": "Call public weather API with city name only",
        "action": "http.get",
        "pros": ["fast", "simple"],
        "cons": ["city ambiguous"],
        "estimated_risk": "low"
      },
      {
        "id": "opt_b",
        "label": "Ask user for airport code then call aviation API",
        "action": "user.ask_then_http.get",
        "pros": ["precise"],
        "cons": ["extra turn"],
        "estimated_risk": "low"
      }
    ],
    "context": {"user_provided_city": false}
  }'
```

### Request body

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `decision_goal` | **yes** | string | What the agent is trying to decide |
| `options` | **yes** | array | 2–5 option objects (see below) |
| `context` | no | object | Facts that affect ranking (e.g. `needs_citations`, `user_provided_city`) |

**Each option object:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | **yes** | string | Unique option identifier |
| `label` | **yes** | string | Human-readable description |
| `action` | no | string | Tool or action name |
| `pros` | no | string[] | Advantages |
| `cons` | no | string[] | Disadvantages |
| `estimated_risk` | no | string | `low` \| `medium` \| `high` (default `low`) |

### Response body

| Field | Type | Description |
|-------|------|-------------|
| `recommended_option_id` | string | ID of the best option |
| `ranking` | string[] | Option IDs best-first |
| `risk_level` | string | Overall risk of the recommendation |
| `reasoning_summary` | string | Why this option was chosen |
| `confidence` | number | 0.0–1.0 |
| `agent_instruction` | string | **Direct command — execute the recommended option** |

### Example response (live)

```json
{
  "recommended_option_id": "opt_b",
  "ranking": ["opt_b", "opt_a"],
  "risk_level": "low",
  "reasoning_summary": "Location is ambiguous; prefer asking the user before fetching external data.",
  "confidence": 0.84,
  "agent_instruction": "Execute option opt_b: Ask user for airport code then call aviation API."
}
```

### Example: research strategy with citations required

```bash
curl -X POST https://agentgate-xwqo.onrender.com/compare-options \
  -H "Content-Type: application/json" \
  -d '{"decision_goal":"Pick research strategy","options":[{"id":"a","label":"Web search only","action":"search.web","estimated_risk":"low"},{"id":"b","label":"Search then verify sources","action":"search.verify","estimated_risk":"low"}],"context":{"needs_citations":true}}'
```

**Response (200):**

```json
{
  "recommended_option_id": "b",
  "ranking": ["b", "a"],
  "risk_level": "low",
  "reasoning_summary": "Citations are required; prefer the option that verifies sources before acting.",
  "confidence": 0.84,
  "agent_instruction": "Execute option b: Search then verify sources."
}
```

### Errors

| Code | When |
|------|------|
| `422` | Fewer than 2 options, missing `decision_goal`, or invalid option shape |
| `500` | Unexpected server error |

---

## How an agent should use AgentGate

Follow this sequence on every session:

1. **Warm up:** `GET /health` once. If slow or timeout, retry once (free-tier cold start).
2. **Before irreversible tools** (payments, deletes, sends, auth changes): call `POST /evaluate-task` with `task_description`, `proposed_action`, and all known `available_context`.
3. **Interpret `status`:**
   - `ready` + `risk_level` `low` → proceed with `recommended_next_action`.
   - `needs_clarification` or `incomplete` → ask user for every field in `missing_info`, update `available_context`, call `/evaluate-task` again.
   - `unsafe` or `risk_level` `high` → follow `agent_instruction`; **do not execute** unless a human explicitly overrides.
4. **When choosing between strategies:** call `POST /compare-options` with at least 2 options; use `recommended_option_id`.
5. **Confidence rule:** if `confidence` < 0.6, prefer asking the user over autonomous execution.
6. **Always obey `agent_instruction`** — it is the direct command for your next step.

### Decision table

| `status` | `risk_level` | Agent behavior |
|----------|--------------|----------------|
| `ready` | `low` | Execute `recommended_next_action` |
| `ready` | `medium` | Proceed with caution; consider user confirmation |
| `needs_clarification` | any | Collect `missing_info`, re-evaluate |
| `incomplete` | any | Clarify task with user |
| `unsafe` | `high` | Stop; request human approval |

---

## Notes

- No authentication, OAuth, or SDK required — HTTP + JSON only.
- Responses use a **stable schema**; all fields above are always present on success.
- Logic is **rules-first** (deterministic, fast, no API key needed). Optional LLM enhancement may be enabled server-side.
- Designed for NANDA Town / NANDAHack Phase 2: judges' stock agents need only this file.

**Repository:** https://github.com/Niruuu2005/CredenceAI/tree/hackathon/agentgate  
**GitHub raw SKILL.md:** https://raw.githubusercontent.com/Niruuu2005/CredenceAI/hackathon/agentgate/agentgate/SKILL.md
