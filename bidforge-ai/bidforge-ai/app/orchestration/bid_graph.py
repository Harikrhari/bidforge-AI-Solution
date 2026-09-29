"""Bid workflow as a LangGraph state machine: extract -> draft (+guardrails) -> retry or end."""
from typing import TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.domain.models import Priority, ProposalSection, Requirement


class ReqList(BaseModel):
    items: list[dict]  # {id, text, priority}


class BidState(TypedDict, total=False):
    tenant_id: str
    tender_text: str
    requirements: list[Requirement]
    sections: list[ProposalSection]
    issues: list[str]
    attempts: int


def build_graph(llm, retriever, guardrails):
    async def extract(s: BidState):
        out: ReqList = await llm.complete(
            "extract", "Extract every shall/must/should requirement as JSON.",
            s["tender_text"], schema=ReqList)
        reqs = [Requirement(i["id"], i["text"], Priority(i["priority"])) for i in out.items]
        return {"requirements": reqs, "attempts": 0}

    async def draft(s: BidState):
        sections, issues = [], []
        for r in s["requirements"]:
            ev = await retriever.search(s["tenant_id"], r.text)
            ctx = "\n".join(f"[{e.chunk_id}] {e.text}" for e in ev)
            ans = await llm.complete(
                "draft",
                "Write a persuasive, factual bid answer. Cite chunk ids like [id]. "
                "If evidence is missing, write MISSING_EVIDENCE.",
                f"REQUIREMENT: {r.text}\n\nEVIDENCE:\n{ctx}")
            cites = [e.chunk_id for e in ev if f"[{e.chunk_id}]" in ans]
            sec = ProposalSection(r.id, ans, cites)
            issues += await guardrails.check(sec, ctx)
            sections.append(sec)
        return {"sections": sections, "issues": issues, "attempts": s["attempts"] + 1}

    def route(s: BidState):
        return "draft" if s["issues"] and s["attempts"] < 2 else END

    g = StateGraph(BidState)
    g.add_node("extract", extract)
    g.add_node("draft", draft)
    g.set_entry_point("extract")
    g.add_edge("extract", "draft")
    g.add_conditional_edges("draft", route)
    return g.compile()
