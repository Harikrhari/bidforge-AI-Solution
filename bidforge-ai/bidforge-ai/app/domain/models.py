from dataclasses import dataclass, field
from enum import Enum


class Priority(str, Enum):
    MUST = "must"
    SHOULD = "should"
    NICE = "nice"


@dataclass(frozen=True)
class Requirement:
    id: str
    text: str
    priority: Priority


@dataclass(frozen=True)
class Evidence:
    chunk_id: str
    text: str
    source: str
    score: float


@dataclass
class ProposalSection:
    requirement_id: str
    answer: str
    citations: list[str] = field(default_factory=list)

    def is_grounded(self) -> bool:
        return len(self.citations) > 0


@dataclass
class Proposal:
    tenant_id: str
    tender_id: str
    sections: list[ProposalSection]

    def compliance_rate(self, reqs: list[Requirement]) -> float:
        must = {r.id for r in reqs if r.priority == Priority.MUST}
        answered = {s.requirement_id for s in self.sections if s.is_grounded()}
        return 1.0 if not must else len(must & answered) / len(must)
