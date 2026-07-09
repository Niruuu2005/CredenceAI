# AgentGate — NANDA Town Submission Package

Replace `YOUR_DEPLOYED_SERVICE_URL` with your live Render URL after deploy.

## Registry form (https://nandatown.projectnanda.org/skills)

| Field | Value |
|-------|-------|
| **Skill name** | AgentGate |
| **One-line** | Pre-action decision API: tells agents if a task is safe, what's missing, and which option to choose. |
| **Tags** | agents, safety, decision, guardrail, api, nanda, trust |
| **GitHub username** | _(your username)_ |
| **SKILL.md URL** | `https://YOUR_DEPLOYED_SERVICE_URL/skill.md` |

### Endpoints (FULL URLs — required for "link responded" badge)

```
GET https://YOUR_DEPLOYED_SERVICE_URL/health
POST https://YOUR_DEPLOYED_SERVICE_URL/evaluate-task
POST https://YOUR_DEPLOYED_SERVICE_URL/compare-options
GET https://YOUR_DEPLOYED_SERVICE_URL/skill.md
```

### Submission summary

AgentGate is a hosted guardrail service for autonomous agents. Before executing tools, agents call /evaluate-task to get structured status, risk level, missing information, and explicit next-step instructions. When choosing between strategies, /compare-options ranks candidates and returns a recommendation. Designed for judge agents that read SKILL.md only — no SDK, no auth, structured JSON throughout.

## Pre-submit verification

Run from any network (not localhost):

```bash
export BASE=https://YOUR_DEPLOYED_SERVICE_URL

curl "$BASE/health"

curl -X POST "$BASE/evaluate-task" \
  -H "Content-Type: application/json" \
  -d '{"task_description":"Book flight to Paris"}'

curl -X POST "$BASE/evaluate-task" \
  -H "Content-Type: application/json" \
  -d '{"task_description":"Delete production database","proposed_action":"db.drop"}'

curl -X POST "$BASE/compare-options" \
  -H "Content-Type: application/json" \
  -d '{"decision_goal":"Weather lookup","options":[{"id":"a","label":"Guess city","action":"search"},{"id":"b","label":"Ask user","action":"ask"}]}'

curl "$BASE/skill.md"
```

- [ ] All 4 URLs return 200
- [ ] Registry card shows **link responded** green badge
- [ ] API keys only in Render env (rotated if exposed in chat)

## Judging day (July 11, 9:30 AM ET)

- [ ] Warm-up `curl $BASE/health` at 9:25 AM ET
- [ ] Self-keepalive enabled overnight
- [ ] Do not redeploy during 9:30–12:00 ET window

## Demo video script (< 90 seconds)

**Title:** AgentGate: Stop Agents Before They Make Costly Mistakes

1. **[0–10s]** "AgentGate is a pre-action decision API for autonomous agents. Before an agent runs a tool, it calls AgentGate to check if the task is safe, complete, and what to do next."

2. **[10–25s]** "Here's our health endpoint on Render — it's live and returns JSON." *(show curl /health)*

3. **[25–45s]** "An agent wants to book a flight but didn't provide dates. AgentGate returns needs_clarification, lists missing_info, and tells the agent exactly what to ask." *(show /evaluate-task)*

4. **[45–60s]** "For a destructive action like deleting a database, status is unsafe, risk is high, and agent_instruction says stop." *(show unsafe example)*

5. **[60–75s]** "When choosing between strategies, compare-options ranks them and picks the best." *(show /compare-options)*

6. **[75–90s]** "Judges' agents only need our SKILL.md — base URL, endpoints, curl examples, and numbered steps. AgentGate is composable guardrail infrastructure for the agentic web."

Upload video and attach URL in final Google form by **July 11, 2:00 PM ET**.

## Deploy checklist

1. Render Dashboard → New Web Service → connect repo
2. Root directory: `agentgate`
3. Environment: Docker
4. Add `OPENROUTER_API_KEY`, `PUBLIC_BASE_URL=https://<your-app>.onrender.com`
5. Deploy → copy URL → set `PUBLIC_BASE_URL` → redeploy once so `/skill.md` has real URLs
