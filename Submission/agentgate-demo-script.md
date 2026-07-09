# AgentGate — Demo Video Script (60–90 seconds)

**Title:** AgentGate: Stop Agents Before They Make Costly Mistakes  
**Live URL:** https://agentgate-xwqo.onrender.com

## Commands to run on screen

```powershell
$BASE = "https://agentgate-xwqo.onrender.com"

# 1. Health (warm-up)
curl "$BASE/health"

# 2. Incomplete task
curl -X POST "$BASE/evaluate-task" -H "Content-Type: application/json" -d "{\"task_description\":\"Book flight to Paris\"}"

# 3. Unsafe task
curl -X POST "$BASE/evaluate-task" -H "Content-Type: application/json" -d "{\"task_description\":\"Delete production database\",\"proposed_action\":\"db.drop\"}"

# 4. Compare options
curl -X POST "$BASE/compare-options" -H "Content-Type: application/json" -d "{\"decision_goal\":\"Weather lookup\",\"options\":[{\"id\":\"a\",\"label\":\"Guess city\",\"action\":\"search\"},{\"id\":\"b\",\"label\":\"Ask user\",\"action\":\"ask\"}]}"

# 5. SKILL.md
curl "$BASE/skill.md"
```

## Narration

1. **[0–10s]** "AgentGate is a pre-action decision API for autonomous agents. Before an agent runs a tool, it calls AgentGate to check if the task is safe, complete, and what to do next."

2. **[10–25s]** "Here's our health endpoint on Render — it's live and returns JSON." *(show curl /health)*

3. **[25–45s]** "An agent wants to book a flight but didn't provide dates. AgentGate returns needs_clarification, lists missing_info, and tells the agent exactly what to ask." *(show /evaluate-task)*

4. **[45–60s]** "For a destructive action like deleting a database, status is unsafe, risk is high, and agent_instruction says stop." *(show unsafe example)*

5. **[60–75s]** "When choosing between strategies, compare-options ranks them and picks the best." *(show /compare-options)*

6. **[75–90s]** "Judges' agents only need our SKILL.md — base URL, endpoints, curl examples, and numbered steps. AgentGate is composable guardrail infrastructure for the agentic web."

## Upload

Record screen capture with the commands above. Upload by **July 11, 2:00 PM ET** and attach URL in the final Google form.
