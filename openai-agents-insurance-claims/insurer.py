"""Fictional insurer back office: policy, coverage and claim data plus the three operations the agents call."""

import json
import uuid
from pathlib import Path

DATA = json.loads((Path(__file__).parent / "data" / "insurer.json").read_text())
POLICIES = DATA["policies"]
CLAIMS = dict(DATA["claims"])


def lookup_claim(claim_id: str) -> dict:
    claim = CLAIMS.get(claim_id.upper())
    if claim is None:
        return {"error": f"no claim found with id {claim_id}"}
    return {"claim_id": claim_id.upper(), **claim}


def check_coverage(policy_id: str, peril: str) -> dict:
    policy = POLICIES.get(policy_id.upper())
    if policy is None:
        return {"error": f"no policy found with id {policy_id}"}
    peril = peril.lower().strip().replace(" ", "_")
    if policy["status"] != "active":
        return {"policy_id": policy_id.upper(), "covered": False, "reason": f"policy is {policy['status']}"}
    if peril in policy["excluded"]:
        return {"policy_id": policy_id.upper(), "covered": False, "reason": f"{peril} is excluded"}
    if peril in policy["covered"]:
        return {"policy_id": policy_id.upper(), "covered": True, "deductible_usd": policy["deductible_usd"]}
    return {"policy_id": policy_id.upper(), "covered": False, "reason": f"{peril} is not listed on this policy"}


def open_claim(policy_id: str, description: str, estimated_amount_usd: float) -> dict:
    policy = POLICIES.get(policy_id.upper())
    if policy is None:
        return {"error": f"no policy found with id {policy_id}"}
    if policy["status"] != "active":
        return {"error": f"policy is {policy['status']}; cannot open a claim"}
    claim_id = f"CL-{uuid.uuid4().hex[:4].upper()}"
    CLAIMS[claim_id] = {"policy_id": policy_id.upper(), "status": "received", "amount_usd": estimated_amount_usd,
                        "adjuster": "unassigned", "note": description}
    return {"claim_id": claim_id, "status": "received"}
