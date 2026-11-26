import asyncio
import json

from agents.tool_context import ToolContext

import insurer
import main


def invoke(tool, **arguments):
    ctx = ToolContext(context=None, tool_name=tool.name, tool_call_id="t1", tool_arguments=json.dumps(arguments))
    return json.loads(asyncio.run(tool.on_invoke_tool(ctx, json.dumps(arguments))))


def test_covered_peril_returns_deductible():
    assert insurer.check_coverage("AU-4471", "collision") == {"policy_id": "AU-4471", "covered": True, "deductible_usd": 500}


def test_excluded_peril_is_denied_with_reason():
    result = insurer.check_coverage("HM-2290", "Flood")
    assert result["covered"] is False and "excluded" in result["reason"]


def test_lapsed_policy_covers_nothing_and_cannot_open_claims():
    assert insurer.check_coverage("HM-3318", "fire")["reason"] == "policy is lapsed"
    assert "error" in insurer.open_claim("HM-3318", "kitchen fire", 900)


def test_open_claim_is_then_findable():
    opened = insurer.open_claim("AU-4471", "bumper damage", 2300)
    assert insurer.lookup_claim(opened["claim_id"])["status"] == "received"


def test_unknown_ids_return_errors_not_exceptions():
    assert "error" in insurer.lookup_claim("CL-0000")
    assert "error" in insurer.check_coverage("XX-1", "fire")


def test_tools_run_with_tracking_disabled():
    # The OpikTracingProcessor is registered at import; with OPIK_TRACK_DISABLE=true tools still behave normally.
    assert invoke(main.check_coverage, policy_id="TM-5513", peril="emergency_care")["covered"] is True


def test_triage_can_hand_off_to_all_three_specialists():
    assert {a.name for a in main.triage_agent.handoffs} == {"Auto Claims Agent", "Home Claims Agent", "Travel Medical Agent"}
