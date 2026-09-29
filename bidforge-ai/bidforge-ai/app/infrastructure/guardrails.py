"""Guardrails pipeline (chain of responsibility): citation -> PII -> LLM-as-judge."""
import re

from pydantic import BaseModel

from app.domain.models import ProposalSection


class Verdict(BaseModel):
    faithful: bool
    reason: str


PII = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b(?:\d[ -]*?){13,16}\b")


class Guardrails:
    def __init__(self, llm):
        self.llm = llm

    async def check(self, section: ProposalSection, evidence_text: str) -> list[str]:
        issues = []
        if not section.is_grounded():
            issues.append("no_citation")
        if PII.search(section.answer):
            issues.append("pii_detected")
        verdict: Verdict = await self.llm.complete(
            "judge",
            "You are a strict auditor. Answer only from the evidence.",
            f"EVIDENCE:\n{evidence_text}\n\nANSWER:\n{section.answer}\n\n"
            "Is every factual claim in ANSWER supported by EVIDENCE?",
            schema=Verdict,
        )
        if not verdict.faithful:
            issues.append(f"unfaithful:{verdict.reason}")
        return issues
