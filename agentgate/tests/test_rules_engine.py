"""Tests for AgentGate rules engine."""

import pytest

from models import CompareOptionsRequest, EvaluateTaskRequest, OptionItem
from rules_engine import compare_options_rules, evaluate_task_rules


def test_unsafe_delete_production():
    req = EvaluateTaskRequest(
        task_description="Delete production database",
        proposed_action="db.drop",
    )
    res = evaluate_task_rules(req)
    assert res.status == "unsafe"
    assert res.risk_level == "high"
    assert "stop" in res.recommended_next_action.lower() or "human" in res.recommended_next_action.lower()


def test_payment_needs_clarification():
    req = EvaluateTaskRequest(
        task_description="Send a payment of $5000 to vendor account 99281",
        goal="Pay quarterly invoice",
        available_context={"user_confirmed": False, "amount_usd": 5000, "recipient_verified": False},
        proposed_action="stripe.transfer",
        constraints=["no_irreversible_without_confirmation"],
    )
    res = evaluate_task_rules(req)
    assert res.status in ("needs_clarification", "unsafe")
    assert "user_confirmed" in res.missing_info or res.status == "unsafe"


def test_book_flight_incomplete():
    req = EvaluateTaskRequest(task_description="Book flight to Paris")
    res = evaluate_task_rules(req)
    assert res.status == "needs_clarification"
    assert len(res.missing_info) > 0


def test_simple_read_ready():
    req = EvaluateTaskRequest(
        task_description="Summarize the meeting notes from today",
        proposed_action="text.summarize",
        available_context={"notes_available": True},
    )
    res = evaluate_task_rules(req)
    assert res.status == "ready"
    assert res.risk_level == "low"


def test_rm_rf_unsafe():
    req = EvaluateTaskRequest(task_description="Run rm -rf /data on server")
    res = evaluate_task_rules(req)
    assert res.status == "unsafe"


def test_compare_options_prefers_ask_when_city_missing():
    req = CompareOptionsRequest(
        decision_goal="Choose weather fetch strategy",
        options=[
            OptionItem(id="opt_a", label="Call public weather API with city name only", action="http.get"),
            OptionItem(id="opt_b", label="Ask user for airport code then call aviation API", action="user.ask"),
        ],
        context={"user_provided_city": False},
    )
    res = compare_options_rules(req)
    assert res.recommended_option_id == "opt_b"
    assert res.ranking[0] == "opt_b"


def test_compare_options_citations():
    req = CompareOptionsRequest(
        decision_goal="Pick research strategy",
        options=[
            OptionItem(id="a", label="Web search only", action="search.web"),
            OptionItem(id="b", label="Search then verify sources", action="search.verify"),
        ],
        context={"needs_citations": True},
    )
    res = compare_options_rules(req)
    assert res.recommended_option_id == "b"


def test_compare_minimum_options_validation():
    with pytest.raises(Exception):
        CompareOptionsRequest(decision_goal="x", options=[OptionItem(id="a", label="only one")])
