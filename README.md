# Agentic support: when should an agent answer, act, or escalate?

A small, runnable agent for client support in a regulated domain (banking-flavored).
For every inbound message it makes one decision — **answer**, **act**, or
**escalate** — and the safety of that decision does not depend on the model
being right.

The whole design is one principle:

> **The model proposes. Code disposes.**

A probabilistic model is allowed to *suggest* what to do. It is never allowed to
*decide* whether a sensitive action runs. That call belongs to a deterministic
guardrail layer. In a domain where the wrong action means an unauthorized loan
approval or a moved balance, you cannot hand the keys to something that is right
"most of the time."

Runs offline, no API key, standard library only.

## The flow

```
inbound message
      │
      ▼
  brain proposes   ── policy.py        (stand-in for an LLM; deliberately fallible)
      │  {answer | act | escalate}
      ▼
  guardrails decide ── guardrails.py   (deterministic; can override the brain)
      │
      ├── answer   → grounded in the knowledge base, or escalate (never invent)
      ├── act      → only the small set of SAFE tools may run
      └── escalate → routed to Compliance / Engineering / Product / Human
```

The brain is intentionally written to make the mistake a real model makes: it
sees "approve this loan" and proposes *acting*, because it looks like an action.
The guardrail layer catches every one of those and forces an escalation instead.

## Run it

```bash
python run.py "How do I reset my access?"
python run.py "Approve this customer's \$40,000 loan increase."
python eval.py        # scores the agent and writes eval_report.md
```

The first command answers from the knowledge base. The second shows the guardrail
blocking an action the brain wanted to take.

## What the eval measures (and why)

One accuracy number hides the failures that matter. The harness scores by what
actually counts for support in a regulated setting, and breaks results down by
request type so you can see *where* it breaks:

| Metric | Result | Why it matters |
|---|---|---|
| Routing accuracy | 88% | Did it pick the right lane? Useful, but not the safety bar. |
| Escalation recall | 100% | Of requests that **must** reach a human, how many did. |
| Over-escalation | 12% | Wrongly punting easy requests — annoying, not dangerous. |
| **Guardrail violations** | **0** | Restricted actions that actually executed. **This must be 0.** |
| Unsafe proposals caught | 4 | Times the brain tried a restricted action and was blocked. |

The number to read first is the boring one: **guardrail violations = 0.** The
brain proposed acting on four restricted requests (loan approval, compliance
override, fund movement, account closure); the guardrail blocked all four. Safety
held even where the brain was wrong — which is the point.

## The misses are real

Routing is 88%, not 100%, and the failing cases are in the per-case trace on
purpose:

- **c01** ("how do I reset my access") — the agent *resets the session* instead
  of explaining how. Arguably resolves the user's problem, but it's an action
  where an answer was expected. A keyword brain can't tell "do X" from "how do I X."
- **c16** ("draft a friendly reply…") — no knowledge-base grounding, so it
  escalates rather than inventing a reply. A wrong call here, but it fails *safe*.

Both are honest limitations of a rule-based brain, and both are the kind of
pattern-recognition gap (education vs. action vs. limitation) you'd tune with a
real model and a larger labeled set.

## What a production version would change

- Swap the rule-based brain in `policy.py` for an LLM call returning a structured
  proposal — the guardrail and tool interfaces stay exactly the same.
- Replace keyword retrieval with embeddings + vector search over a real,
  versioned knowledge base.
- Grow `eval_cases.jsonl` into a labeled regression set run in CI, so a change to
  the brain can't silently raise the violation count.

## Layout

```
agent/
  policy.py          brain: proposes answer | act | escalate (fallible on purpose)
  guardrails.py      deterministic override layer — the "code disposes" half
  tools.py           the only actions allowed to run autonomously
  knowledge_base.py  grounded answers + simple retrieval
  agent.py           orchestrator
data/
  knowledge_base.json
  eval_cases.jsonl   labeled evaluation set
run.py               run one message
eval.py              score the agent, write eval_report.md
```
