"""
The 'brain': proposes what to do with an inbound message.

This is a deterministic, rule-based stand-in for an LLM. In production this would
be a model call returning a structured action proposal. It is written to be
*fallible on purpose*: like a real model, it will happily propose acting on
requests it shouldn't (approving a loan, moving money) because the words look
like an action. That is the whole point of the demo -- the brain is not trusted
to gate safety. The guardrail layer (guardrails.py) does that.

A proposal is a dict:
    {intent, action, args, confidence, kb_topic}
where intent is one of ANSWER / ACT / ESCALATE.
"""

from agent import knowledge_base

# Verbs that look like an executable action to a naive brain.
_ACTION_HINTS = {
    "reset": ("reset_session", {}),
    "open a ticket": ("create_ticket", {}),
    "ticket": ("create_ticket", {}),
    "look up": ("lookup_status", {}),
    "status of": ("lookup_status", {}),
    # The brain ALSO treats these as actions -- which is the mistake the guardrail catches.
    "approve": ("approve_request", {}),
    "override": ("override_flag", {}),
    "move $": ("move_funds", {}),
    "transfer": ("move_funds", {}),
    "close this": ("close_account", {}),
    "close the": ("close_account", {}),
}

# Signals that a message is a bug report / limitation / off-scope -> not answerable from KB.
_ESCALATE_HINTS = ["is that a bug", "wrong", "when is that coming", "when will",
                   "doesn't support", "don't support", "can't right now", "weather"]


def propose(message: str) -> dict:
    msg = message.lower()

    # 1. Does it look like a known action request?
    for hint, (action, args) in _ACTION_HINTS.items():
        if hint in msg:
            return {"intent": "ACT", "action": action, "args": args,
                    "confidence": 0.8, "kb_topic": None}

    # 2. Bug / limitation / off-scope -> propose escalation.
    if any(h in msg for h in _ESCALATE_HINTS):
        return {"intent": "ESCALATE", "action": None, "args": {},
                "confidence": 0.6, "kb_topic": None}

    # 3. Otherwise try to ground an answer in the KB.
    hit = knowledge_base.retrieve(message)
    if hit:
        topic, _entry, score = hit
        return {"intent": "ANSWER", "action": None, "args": {},
                "confidence": min(0.5 + 0.2 * score, 0.95), "kb_topic": topic}

    # 4. No confident read -> escalate rather than guess.
    return {"intent": "ESCALATE", "action": None, "args": {},
            "confidence": 0.3, "kb_topic": None}
