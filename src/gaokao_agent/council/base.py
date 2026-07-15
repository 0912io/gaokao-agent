"""Base class for all council agents."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..config import Profile


class BaseAgent(ABC):
    """Abstract base for expert agents in the council.

    Attributes:
        name: Human-readable agent name (for display)
        weight: Voting weight in council decisions (0.0 - 5.0)
        veto: If True, this agent can block any recommendation
        confidence: Output confidence level — "strategy" | "trend" | "data"
    """

    name: str = "base"
    weight: float = 1.0
    veto: bool = False
    confidence: str = "trend"  # "strategy" | "trend" | "data"

    @abstractmethod
    def analyze(self, school: dict, profile: Profile) -> dict:
        """Analyze a school against a student profile.

        Args:
            school: School data dict with keys like 'name', 'min_rank', etc.
            profile: Student profile with score/rank/subjects/preferences.

        Returns:
            {
                "verdict": "reach" | "match" | "safety" | "reject",
                "confidence": 0.0 - 1.0,
                "reasons": ["reason 1", "reason 2"],
                "warnings": ["warning 1"] (optional),
            }
        """
        ...

    def __repr__(self):
        return f"<{self.name} weight={self.weight} veto={self.veto}>"
