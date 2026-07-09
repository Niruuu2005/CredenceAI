# AgentGate

Pre-action decision API that tells autonomous agents whether a task is safe to run, what information is missing, and which option to choose next.

https://YOUR_DEPLOYED_SERVICE_URL

## GET /health

Returns service liveness. Call this first to warm up the host if it was idle.

```bash
curl https://YOUR_DEPLOYED_SERVICE_URL/health
```

Example response:
```json
{"status":"ok","service":"agentgate","version":"1.0.0","llm_mode":"rules_with_openrouter_fallback"}
```

## POST /evaluate-task

Evaluates a proposed agent task before execution. Returns status, risk, missing fields, and what to do next.

```bash
curl -X POST https://YOUR_DEPLOYED_SERVICE_URL/evaluate-task \
  -H "Content-Type: application/json" \
  -d '{"task_description":"Delete all files in /data","proposed_action":"fs.delete_recursive","available_context":{"backup_exists":false}}'
```

Example response:
```json
{
  "status": "unsafe",
  "risk_level": "high",
  "missing_info": ["backup_exists","user_confirmed"],
  "recommended_next_action": "stop_and_request_human_approval",
  "reasoning_summary": "Destructive action without backup or confirmation.",
  "confidence": 0.95,
  "agent_instruction": "Do not delete files. Ask user to confirm and verify backup exists."
}
```

## POST /compare-options

Compares 2-5 options and returns the best next action for an agent.

```bash
curl -X POST https://YOUR_DEPLOYED_SERVICE_URL/compare-options \
  -H "Content-Type: application/json" \
  -d '{"decision_goal":"Pick research strategy","options":[{"id":"a","label":"Web search only","action":"search.web","estimated_risk":"low"},{"id":"b","label":"Search then verify sources","action":"search.verify","estimated_risk":"low"}],"context":{"needs_citations":true}}'
```

Example response:
```json
{
  "recommended_option_id": "b",
  "ranking": ["b","a"],
  "risk_level": "low",
  "reasoning_summary": "Citations required; verify step reduces hallucination risk.",
  "confidence": 0.88,
  "agent_instruction": "Execute option b: search then verify sources."
}
```

## How an agent should use this service

1. Call `GET /health` once per session to confirm the service is reachable.
2. Before executing any irreversible or high-impact tool call, call `POST /evaluate-task` with `task_description`, `proposed_action`, and all known `available_context`.
3. If `status` is `ready` and `risk_level` is `low`, proceed with `recommended_next_action`.
4. If `status` is `needs_clarification` or `incomplete`, ask the user for items in `missing_info`, then call `/evaluate-task` again.
5. If `status` is `unsafe` or `risk_level` is `high`, follow `agent_instruction` and do not execute the proposed action unless a human explicitly overrides.
6. When choosing between strategies, call `POST /compare-options` with at least 2 options and use `recommended_option_id`.
7. Treat `confidence` below 0.6 as weak: prefer clarification over autonomous execution.

## Notes

- `status` values: `ready`, `needs_clarification`, `unsafe`, `incomplete`
- `risk_level` values: `low`, `medium`, `high`
- Always read `agent_instruction` — it is the direct command for the calling agent.
