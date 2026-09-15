"""Execution layer — the four deterministic agents over the spine's primitives."""

from compliance_spine.agents.ai_act_baseline import AiActBaselineAgent
from compliance_spine.agents.base import Agent, AgentResult
from compliance_spine.agents.coding_advisor import CodingAdvisorAgent
from compliance_spine.agents.quality_reviewer import QualityReviewerAgent
from compliance_spine.agents.test_author import TestAuthorAgent

AGENTS = {
    a.name: a
    for a in (CodingAdvisorAgent, TestAuthorAgent, QualityReviewerAgent, AiActBaselineAgent)
}

__all__ = [
    "AGENTS",
    "Agent",
    "AgentResult",
    "AiActBaselineAgent",
    "CodingAdvisorAgent",
    "QualityReviewerAgent",
    "TestAuthorAgent",
]
