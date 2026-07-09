# AgentGate — Pre-action decisions for autonomous agents

A minimal HTTP API that helps agents decide whether to execute a task, what information is missing, and which option to pick next. Built for NANDAHack Phase 2.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness check |
| POST | `/evaluate-task` | Pre-action task readiness and risk |
| POST | `/compare-options` | Rank 2–5 candidate strategies |
| GET | `/skill.md` | Agent-readable skill documentation |

## Local development

```bash
cd agentgate
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

```bash
curl http://localhost:8080/health
```

## Rules engine (primary)

Deterministic heuristics — no API key required:

- **unsafe**: destructive ops, mass email, credential exfiltration, high-value transfers without confirmation
- **needs_clarification**: missing `user_confirmed`, `recipient_verified`, dates, etc.
- **incomplete**: empty or vague task descriptions
- **compare-options**: lower risk wins; ties favor options that gather missing info

## Optional LLM enhancement

Set `OPENROUTER_API_KEY` in environment. On ambiguous cases, OpenRouter may refine the rules output. On timeout or failure, rules output is returned.

## Deploy on Render

1. Create a **new Web Service** (not CredenceAI) from this repo with root directory `agentgate`
2. Use Docker (`Dockerfile`) or Python start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Set env vars:
   - `SELF_KEEPALIVE_ENABLED=true`
   - `OPENROUTER_API_KEY` (rotate if exposed)
   - `PUBLIC_BASE_URL=https://your-service.onrender.com`
4. Health check path: `/health`

Or use `render.yaml` blueprint from repo root.

## Tests

```bash
cd agentgate
pytest tests/ -v
```

## Registry submission

See `SUBMISSION.md` for NANDA Town form copy, endpoint URLs, and demo video script.
