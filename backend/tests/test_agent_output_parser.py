"""Tests for agent output JSON parsing and repair."""

from app.services.agent_output_parser import AgentOutputParser


def test_parse_json_repair_trailing_comma():
    raw = '{"jobs": [], "reasoning": "ok",}'
    parsed = AgentOutputParser.parse_json(raw)
    assert parsed["reasoning"] == "ok"
    assert parsed["jobs"] == []


def test_parse_json_repair_python_literals():
    raw = '{"jobs": [], "active": True, "count": None}'
    parsed = AgentOutputParser.parse_json(raw)
    assert parsed["active"] is True
    assert parsed["count"] is None


def test_parse_json_repair_single_quoted_keys():
    raw = "{'jobs': [], 'reasoning': 'plan ok'}"
    parsed = AgentOutputParser.parse_json(raw)
    assert parsed["jobs"] == []
    assert parsed["reasoning"] == "plan ok"
