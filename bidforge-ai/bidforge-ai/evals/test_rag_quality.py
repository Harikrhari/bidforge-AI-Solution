"""Evals gate: run with `pytest evals/ -q` against a running stack with API keys set."""
import json
import pathlib

import pytest

GOLDEN_PATH = pathlib.Path(__file__).parent / "golden_set.jsonl"
GOLDEN = [json.loads(line) for line in GOLDEN_PATH.read_text().splitlines() if line.strip()]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", GOLDEN, ids=lambda c: c["id"])
async def test_draft_quality(case):
    from app.container import get_graph
    graph = await get_graph()
    out = await graph.ainvoke({"tenant_id": "eval", "tender_text": case["tender"]})
    extracted = {r.text for r in out["requirements"]}
    expected = set(case["expected_requirements"])
    recall = len(extracted & expected) / len(expected)
    grounded = sum(s.is_grounded() for s in out["sections"]) / max(len(out["sections"]), 1)
    assert recall >= 0.9, f"requirement recall {recall:.2f}"
    assert grounded >= 0.95, f"grounded rate {grounded:.2f}"
    assert not [i for i in out["issues"] if i.startswith("unfaithful")]
