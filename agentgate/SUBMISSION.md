# AgentGate — Complete NANDAHack Phase 2 Submission Package

**Live service:** https://agentgate-xwqo.onrender.com  
**Branch:** `hackathon/agentgate`  
**Deadline:** Initial submission **Friday July 10, 2026, 12:00 PM ET**

---

## 1. NANDA Town registry form

**URL:** https://nandatown.projectnanda.org/skills

Copy each field exactly:

| Form field | Value |
|------------|-------|
| **Skill name** | `AgentGate` |
| **Your name or team** | _(your name — e.g. Niraj)_ |
| **Email** | _(your email)_ |
| **GitHub username** | `Niruuu2005` |
| **One line: what does it do?** | `Pre-action decision API: tells agents if a task is safe, what's missing, and which option to choose.` |
| **Hosted .md link** | `https://agentgate-xwqo.onrender.com/skill.md` |
| **Your endpoints** | See block below |
| **Tags** | `agents, safety, decision, guardrail, api, nanda, trust` |

**Endpoints block (paste into "Your endpoints"):**

```
GET  https://agentgate-xwqo.onrender.com/health
POST https://agentgate-xwqo.onrender.com/evaluate-task
POST https://agentgate-xwqo.onrender.com/compare-options
GET  https://agentgate-xwqo.onrender.com/skill.md
```

**Submission summary (if form has a description field):**

> AgentGate is a hosted guardrail service for autonomous agents. Before executing tools, agents call `/evaluate-task` to get structured status, risk level, missing information, and explicit next-step instructions. When choosing between strategies, `/compare-options` ranks candidates and returns a recommendation. Designed for judge agents that read SKILL.md only — no SDK, no auth, structured JSON throughout.

---

## 2. Participation / Google forms

Confirm these separately (links from hackathon organizers):

- [ ] Initial participation form completed
- [ ] Partner's Phase 1 PR open on NANDA Town repo (`hackathon/yourname-topic`)
- [ ] NANDA Town skills form submitted (section 1 above)
- [ ] Registry card shows **"link responded"** green badge
- [ ] Video uploaded + final Google form by **Saturday July 11, 2:00 PM ET**

---

## 3. Pre-submit verification (all must return 200)

```powershell
$BASE = "https://agentgate-xwqo.onrender.com"

curl "$BASE/health"

curl -X POST "$BASE/evaluate-task" -H "Content-Type: application/json" `
  -d '{"task_description":"Book flight to Paris"}'

curl -X POST "$BASE/evaluate-task" -H "Content-Type: application/json" `
  -d '{"task_description":"Delete production database","proposed_action":"db.drop"}'

curl -X POST "$BASE/compare-options" -H "Content-Type: application/json" `
  -d '{"decision_goal":"Weather lookup","options":[{"id":"a","label":"Guess city","action":"search"},{"id":"b","label":"Ask user","action":"ask"}]}'

curl "$BASE/skill.md"
```

- [ ] All 5 calls succeed from phone/off-network (not localhost)
- [ ] `OPENROUTER_API_KEY` only in Render env (rotate if exposed in chat)
- [ ] `SELF_KEEPALIVE_ENABLED=true` on Render

---

## 4. Judging day (Saturday July 11)

| Time (ET) | Action |
|-----------|--------|
| **9:25 AM** | Send warm-up `curl https://agentgate-xwqo.onrender.com/health` |
| **9:30 AM–12:00 PM** | Do **not** redeploy; keep service warm |
| **Overnight Fri→Sat** | Self-keepalive enabled |

---

## 5. Demo video

**Title:** AgentGate: Stop Agents Before They Make Costly Mistakes  
**Script:** See `Submission/agentgate-demo-script.md`  
**Due:** July 11, 2:00 PM ET

---

## 6. Positioning copy

| Field | Text |
|-------|------|
| **Project name** | AgentGate |
| **One-line** | Pre-action decision API that tells autonomous agents whether a task is safe to run, what is missing, and which option to choose next. |
| **Problem** | Agents often execute tools with incomplete context, unclear goals, or unsafe parameters. |
| **Demo title** | AgentGate: Stop Agents Before They Make Costly Mistakes |
