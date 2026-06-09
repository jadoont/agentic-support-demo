"""
Mock backend tools.

In production these would be real API calls. Here they are deterministic stubs
so the whole demo runs offline with no credentials. The point isn't the tools
themselves -- it's that the agent is only ever allowed to call the *safe* ones
(see guardrails.py). Anything money-moving, compliance-altering, or account-
altering is deliberately NOT exposed here; those paths must escalate to a human.
"""


def reset_session(user: str = "current_user") -> str:
    return f"Session for {user} has been reset. Ask them to sign in again."


def create_ticket(description: str = "") -> str:
    ticket_id = "TKT-" + str(abs(hash(description)) % 10000).zfill(4)
    return f"Opened {ticket_id} for engineering triage: \"{description.strip()[:80]}\"."


def lookup_status(reference: str = "") -> str:
    ref = reference or "unknown"
    return f"Request {ref} is currently 'in review' (mock record). No action needed from the user."


# Registry of the ONLY actions the agent is permitted to execute autonomously.
SAFE_TOOLS = {
    "reset_session": reset_session,
    "create_ticket": create_ticket,
    "lookup_status": lookup_status,
}
