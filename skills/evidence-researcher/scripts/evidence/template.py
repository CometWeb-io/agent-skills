"""Empty ledger template."""
from __future__ import annotations

from typing import Any, Dict

from .constants import SCHEMA_VERSION
from .identity import make_id


def template(question: str, as_of: str, mode: str) -> Dict[str, Any]:
    research_id = make_id("research", f"{question}|{as_of}|{mode}")
    return {
        "schema_version": SCHEMA_VERSION,
        "research_id": research_id,
        "research_contract": {
            "question": question,
            "objective": None,
            "scope": {},
            "as_of": as_of,
            "mode": mode,
            "consumers": [],
            "constraints": [],
            "known_facts": [],
            "known_unknowns": [],
            "privacy_lane": "PUBLIC",
        },
        "claims": [],
        "sources": [],
        "evidence": [],
        "contradictions": [],
        "searches": [],
        "gaps": [],
        "research_status": "PARTIAL",
        "stop_reason": None,
    }

