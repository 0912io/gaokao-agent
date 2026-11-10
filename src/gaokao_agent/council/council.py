"""Council — weighted voting engine with veto power."""

from collections import defaultdict
from typing import Dict, List

from .base import BaseAgent
from ..config import Profile


class Council:
    """Orchestrates multiple expert agents with weighted voting.

    Parallel deliberation → weighted vote aggregation → veto check → consensus.

    Usage:
        council = Council()
        council.add(Strategist(weight=4.5))
        council.add(SafetyAuditor(veto=True))
        results = council.deliberate(schools, profile)
    """

    def __init__(self, auto_load: bool = True):
        self.agents: List[BaseAgent] = []
        if auto_load:
            for agent_cls in self._default_agents():
                self.add(agent_cls())

    @staticmethod
    def _default_agents() -> list:
        """Return the 10 default council agent classes."""
        from .personas import ALL_AGENTS  # noqa: E402

        return list(ALL_AGENTS)

    def add(self, agent: BaseAgent):
        """Register an agent to the council."""
        self.agents.append(agent)

    def remove(self, name: str):
        """Remove an agent by name."""
        self.agents = [a for a in self.agents if a.name != name]

    def deliberate(self, schools: List[dict], profile: Profile) -> dict:
        """Run all agents on all schools. Returns per-school verdicts.

        Returns:
            {
                "school_id": {
                    "agent_name": {"verdict": "...", "confidence": 0.8, ...},
                    ...
                },
            }
        """
        results = defaultdict(dict)
        for school in schools:
            school_id = school.get("id", school.get("name", "unknown"))
            for agent in self.agents:
                try:
                    analysis = agent.analyze(school, profile)
                    results[school_id][agent.name] = analysis
                except Exception as e:
                    results[school_id][agent.name] = {
                        "verdict": "error",
                        "confidence": 0.0,
                        "reasons": [str(e)],
                    }
        return dict(results)

    def consensus(self, votes: Dict[str, dict]) -> str:
        """Compute consensus verdict from agent votes.

        Returns:
            "reach" | "match" | "safety" | "reject" | "high_risk"
        """
        weighted = defaultdict(float)
        veto_count = 0

        for agent in self.agents:
            vote = votes.get(agent.name, {})
            verdict = vote.get("verdict", "unknown")
            confidence = vote.get("confidence", 0.5)
            w = agent.weight * confidence

            if agent.veto and verdict == "reject":
                veto_count += 1

            weighted[verdict] += w

        # Veto override: any veto agent rejecting → high_risk
        if veto_count > 0:
            return "high_risk"

        if not weighted:
            return "unknown"

        return max(weighted, key=weighted.get)

    def summary(self, deliberations: dict) -> dict:
        """Generate a summary of council deliberations."""
        total = len(self.agents)
        weighted = sum(a.weight for a in self.agents)
        veto_count = sum(1 for a in self.agents if a.veto)

        return {
            "total_agents": total,
            "total_weight": weighted,
            "veto_agents": veto_count,
            "schools_evaluated": len(deliberations),
        }
