"""Environment configuration for AgentGate."""

import os

SERVICE_VERSION = "1.0.0"
SERVICE_NAME = "agentgate"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free"
).strip()
LLM_ENABLED = os.getenv("LLM_ENABLED", "true" if OPENROUTER_API_KEY else "false").lower() == "true"
LLM_TIMEOUT_SEC = float(os.getenv("LLM_TIMEOUT_SEC", "8"))

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
SELF_KEEPALIVE_ENABLED = os.getenv("SELF_KEEPALIVE_ENABLED", "true").lower() == "true"
# Render free tier can idle quickly; ping well under 50s (default 30s).
SELF_KEEPALIVE_INTERVAL_SEC = int(os.getenv("SELF_KEEPALIVE_INTERVAL_SEC", "30"))

RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
