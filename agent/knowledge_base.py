"""
Knowledge base + retrieval.

A real system would embed the KB and do vector similarity search. Here retrieval
is keyword overlap -- deliberately simple, because the interesting design question
isn't *how* you retrieve, it's that ANSWER responses are grounded in a known
source instead of generated free-hand. If nothing matches well, the agent should
NOT make something up; it returns None and the agent escalates.
"""

import json
import os

_KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base.json")

with open(_KB_PATH) as f:
    _KB = json.load(f)


def retrieve(message: str):
    """Return (topic_key, entry, score) for the best match, or None if no good match."""
    msg = message.lower()
    best = None
    best_score = 0
    for key, entry in _KB.items():
        score = sum(1 for kw in entry["keywords"] if kw in msg)
        if score > best_score:
            best_score = score
            best = (key, entry)
    if best is None or best_score == 0:
        return None
    return (best[0], best[1], best_score)
