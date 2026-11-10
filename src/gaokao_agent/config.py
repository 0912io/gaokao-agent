"""Configuration management for gaokao-agent."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Profile:
    """Student profile — the input to the agent pipeline.

    Args:
        province: Province name (e.g. "北京", "陕西", "广东")
        score: Total gaokao score
        rank: Provincial rank (位次)
        subjects: Selected subjects (e.g. ["物理", "化学", "生物"])
        gender: Optional gender for safety-aware recommendations
        preferences: Optional preference tags (e.g. ["冲学校", "捡漏"])
        constraints: Optional constraints (e.g. {"require_985": True})
    """
    province: str
    score: int
    rank: int
    subjects: List[str] = field(default_factory=list)
    gender: str = ""
    preferences: List[str] = field(default_factory=list)
    constraints: dict = field(default_factory=dict)

    def validate(self):
        """Validate required fields. Returns (ok, missing_fields)."""
        missing = []
        if not self.province:
            missing.append("province")
        if self.score <= 0:
            missing.append("score")
        if self.rank <= 0:
            missing.append("rank")
        if not self.subjects:
            missing.append("subjects")
        return len(missing) == 0, missing

    @property
    def track(self):
        """Infer track from subjects."""
        if "物理" in self.subjects:
            return "physics"
        elif "历史" in self.subjects:
            return "history"
        return "unknown"


@dataclass
class Settings:
    """Global agent settings."""
    verbose: bool = False
    output_format: str = "json"  # json | table
    demo_mode: bool = True
