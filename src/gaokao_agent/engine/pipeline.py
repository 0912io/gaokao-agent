"""Pipeline orchestrator — 6-stage execution flow."""

from dataclasses import dataclass, field
from typing import List

from .state_machine import StateMachine
from ..config import Profile, Settings
from ..council.council import Council
from ..guards.pre_check import PreCheck
from ..guards.post_check import PostCheck


@dataclass
class PipelineResult:
    """Output of a full pipeline run."""
    profile: Profile
    phase: str
    recommendations: List[dict] = field(default_factory=list)
    risks: List[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self):
        return len(self.errors) == 0

    def to_dict(self):
        return {
            "profile": {
                "province": self.profile.province,
                "score": self.profile.score,
                "rank": self.profile.rank,
                "subjects": self.profile.subjects,
            },
            "phase": self.phase,
            "recommendations": self.recommendations,
            "risks": self.risks,
            "metadata": self.metadata,
            "errors": self.errors,
        }


class Pipeline:
    """6-stage orchestration engine.

    Stages:
        1. Input validation (pre_check)
        2. Record the profile on the state machine
        3. Load schools from one data source
        4. Council deliberation
        5. Assemble recommendations from council votes
        6. Output validation (post_check)

    PolicyEngine and CrossValidator are not part of this path. The run
    has no free-text query and no second source of rank or score data.
    """

    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()
        self.sm = StateMachine()
        self.pre_check = PreCheck()
        self.post_check = PostCheck()
        self._council = None

    @property
    def council(self):
        if self._council is None:
            self._council = Council()
        return self._council

    def run(self, profile: Profile, data_source) -> PipelineResult:
        """Execute the full 6-stage pipeline."""
        result = PipelineResult(profile=profile, phase="INITIAL")
        errors = []

        # Stage 1: Input validation
        valid, missing = self.pre_check.validate_profile(profile)
        if not valid:
            errors.append(f"profile_invalid:{missing}")
            result.errors = errors
            result.phase = "REJECTED"
            return result

        # Stage 2: Set constraints in state machine
        self.sm.set_four_elements(
            province=profile.province,
            score=profile.score,
            rank=profile.rank,
            track=profile.track,
            subjects=profile.subjects,
            gender=profile.gender,
        )
        self.sm.set_gate("memory_loaded", True)
        result.phase = self.sm.current_phase()

        # Stage 3: Data acquisition
        schools = data_source.get_schools(profile)
        self.sm.set_gate("mcp_called", True)
        self.sm.transition("DATA_ACQUIRED")
        result.phase = self.sm.current_phase()

        # Stage 4: Council deliberation
        deliberations = self.council.deliberate(schools, profile)
        self.sm.transition("DELIBERATED")
        result.phase = self.sm.current_phase()

        # Stage 5: Assemble recommendations from council votes
        recommendations, risks = self._assemble(deliberations, profile)
        result.recommendations = recommendations
        result.risks = risks
        self.sm.set_gate("citation_added", True)
        self.sm.transition("PLAN_GENERATED")
        result.phase = self.sm.current_phase()

        # Stage 6: Output validation
        post_ok, post_issues = self.post_check.validate(recommendations)
        if not post_ok:
            errors.extend(post_issues)

        self.sm.transition("OUTPUT_DELIVERED")
        result.phase = self.sm.current_phase()
        result.errors = errors
        result.metadata = {
            "state_machine": self.sm.current_phase(),
            "agents_consulted": len(self.council.agents),
            "schools_evaluated": len(schools),
        }

        return result

    def _assemble(self, deliberations, profile):
        """Assemble council output into structured recommendations."""
        recommendations = []
        risks = []

        for school_id, votes in deliberations.items():
            rec = {
                "school_id": school_id,
                "verdicts": votes,
                "consensus": self.council.consensus(votes),
            }
            if rec["consensus"] == "high_risk":
                risks.append(rec)
            else:
                recommendations.append(rec)

        recommendations.sort(
            key=lambda r: sum(
                v.get("confidence", 0) for v in r["verdicts"].values()
            ),
            reverse=True,
        )
        return recommendations, risks
