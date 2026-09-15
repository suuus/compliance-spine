"""Agent base — Execution layer.

Agents are **deterministic services** over the gates, evidence, and classifiers. They make
no model calls, so they are fast, offline, and testable, and they inherit the fail-closed
guarantees of the primitives they compose. Each agent turns a change into an
:class:`AgentResult`; some also write Evidence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from compliance_spine.change import Change


@dataclass
class AgentResult:
    agent: str
    change_id: str
    ok: bool
    verdict: str
    items: list[str] = field(default_factory=list)
    detail: dict = field(default_factory=dict)

    def render(self) -> str:
        head = f"[{self.agent}] {self.change_id}: {self.verdict}"
        return "\n".join([head, *(f"  - {item}" for item in self.items)])


class Agent(ABC):
    name: str = "agent"

    @abstractmethod
    def run(self, change: Change) -> AgentResult:
        raise NotImplementedError
