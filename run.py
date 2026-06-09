"""
Run a single message through the agent.

    python run.py "Approve this customer's $40,000 loan increase."
    python run.py "How do I reset my access?"
"""

import sys
from agent.agent import handle


def main():
    if len(sys.argv) < 2:
        print('Usage: python run.py "your message here"')
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    d = handle(message)

    print(f"\nMessage      : {d.message}")
    print(f"Brain wanted : {d.proposed_intent}")
    print(f"Final action : {d.final_intent}" + (f"  -> {d.escalated_to}" if d.escalated_to else ""))
    if d.blocked_unsafe:
        print("              ** guardrail blocked an unsafe action the brain proposed **")
    print(f"Response     : {d.response}\n")


if __name__ == "__main__":
    main()
