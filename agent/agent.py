"""
Agent orchestrator.

Flow for every inbound message:
    1. brain proposes an action               (policy.propose)
    2. guardrails decide if it's allowed       (guardrails.apply)
    3. execute / answer / escalate accordingly

Returns a Decision with the full trace so the routing is auditable -- you can
always see what the brain wanted vs. what actually happened.
"""

from dataclasses import dataclass, field
from typing import Optional

from agent import policy, guardrails, tools, knowledge_base


@dataclass
class Decision:
    message: str
    proposed_intent: str
    final_intent: str
    response: str
    escalated_to: Optional[str] = None
    blocked_unsafe: bool = False
    trace: dict = field(default_factory=dict)


def handle(message: str) -> Decision:
    proposal = policy.propose(message)
    verdict = guardrails.apply(proposal)
    final = verdict["final_intent"]

    if final == "ACT":
        tool = tools.SAFE_TOOLS[verdict["action"]]
        response = tool(message)
    elif final == "ANSWER":
        hit = knowledge_base.retrieve(message)
        if hit:
            response = hit[1]["answer"]
        else:
            # KB failed at execution time -> fall back to escalation, never invent.
            final = "ESCALATE"
            verdict["escalated_to"] = "Human"
            response = "I don't have a grounded answer for that, so I'm routing it to a person."
    else:  # ESCALATE
        target = verdict["escalated_to"] or "Human"
        response = f"Escalating to {target}: {verdict['reason']}"

    return Decision(
        message=message,
        proposed_intent=proposal["intent"],
        final_intent=final,
        response=response,
        escalated_to=verdict.get("escalated_to"),
        blocked_unsafe=verdict.get("blocked_unsafe", False),
        trace={"proposal": proposal, "guardrail": verdict},
    )
