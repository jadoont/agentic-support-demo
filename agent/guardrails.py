"""
Guardrails: the deterministic layer that decides whether the brain's proposal is
allowed to execute. This is the core idea of the demo:

    The model PROPOSES. Code DISPOSES.

No matter how confident the brain is, an action only runs if it clears these
rules. Restricted actions can never be executed autonomously -- they are forced
to escalate to a human, regardless of what the brain wanted. In a regulated
domain you cannot let a probabilistic model hold the keys to money movement or
compliance decisions.
"""

from agent import tools

# Actions the brain might propose that must NEVER run autonomously.
RESTRICTED_ACTIONS = {
    "approve_request": "Compliance",   # lending / credit decisions
    "override_flag": "Compliance",     # compliance overrides
    "move_funds": "Compliance",        # any money movement
    "close_account": "Compliance",     # account lifecycle changes
}

# Below this confidence, don't act/answer -- escalate.
MIN_CONFIDENCE = 0.45


def apply(proposal: dict) -> dict:
    """
    Returns a decision dict:
        {final_intent, action, escalated_to, reason, blocked_unsafe}
    blocked_unsafe is True when the brain tried to execute a restricted action
    and the guardrail stopped it -- this is the metric that should stay > 0 in
    eval while actual violations stay at 0.
    """
    intent = proposal["intent"]
    action = proposal.get("action")
    conf = proposal.get("confidence", 0.0)

    # Rule 1: a proposed action in the restricted set is always blocked + escalated.
    if intent == "ACT" and action in RESTRICTED_ACTIONS:
        return {"final_intent": "ESCALATE", "action": None,
                "escalated_to": RESTRICTED_ACTIONS[action],
                "reason": f"'{action}' is a restricted action and cannot run autonomously.",
                "blocked_unsafe": True}

    # Rule 2: an action the brain proposed but no real safe tool backs -> escalate.
    if intent == "ACT" and action not in tools.SAFE_TOOLS:
        return {"final_intent": "ESCALATE", "action": None,
                "escalated_to": "Engineering",
                "reason": f"No safe tool implements '{action}'.",
                "blocked_unsafe": False}

    # Rule 3: low confidence -> don't guess, escalate.
    if conf < MIN_CONFIDENCE:
        return {"final_intent": "ESCALATE", "action": None,
                "escalated_to": "Human",
                "reason": f"Low confidence ({conf:.2f}); escalating instead of guessing.",
                "blocked_unsafe": False}

    # Otherwise the proposal is allowed through unchanged.
    return {"final_intent": intent, "action": action,
            "escalated_to": None, "reason": "Cleared guardrails.",
            "blocked_unsafe": False}
