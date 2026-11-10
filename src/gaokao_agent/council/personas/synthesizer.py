"""Role: Synthesizer — integrates all agent perspectives into final summary.

Produces the human-readable output: reach/match/safety buckets,
key risk warnings, and an overall strategy assessment.
"""

from ..base import BaseAgent
from ...config import Profile


class SynthesizerAgent(BaseAgent):
    name = "synthesizer"
    weight = 1.0
    confidence = "strategy"

    def analyze(self, school: dict, profile: Profile) -> dict:
        """The synthesizer runs AFTER the council has collected all votes.
        This analyze() provides per-school integration comments.
        """
        reasons = []
        warnings = []

        min_rank = school.get("min_rank", 0)
        rank_gap = min_rank - profile.rank

        # Bucket classification
        if rank_gap < -8000:
            bucket = "safety"
            comment = (
                f"Comfortable safety ({abs(rank_gap)} positions margin). "
                "High confidence of admission. Use as backstop."
            )
        elif rank_gap < 3000:
            bucket = "match"
            comment = (
                f"Match range ({'above' if rank_gap > 0 else 'below'} "
                f"threshold by {abs(rank_gap)}). Moderate confidence."
            )
        else:
            bucket = "reach"
            comment = (
                f"Reach target ({abs(rank_gap)} away). Lower probability "
                "but worth attempting in parallel with safer options."
            )

        reasons.append(comment)
        # personas/__init__.py imports this class before ALL_AGENTS exists.
        from ..personas import ALL_AGENTS

        reasons.append(
            f"Final recommendation integrates all {len(ALL_AGENTS)} agent "
            "perspectives with weighted voting. Check individual agent "
            "verdicts for detail."
        )

        # Overall risk assessment
        has_supplementary = school.get("supplementary_history", False)
        if bucket == "reach" and not has_supplementary:
            warnings.append(
                "Reach without supplementary backup — ensure safety "
                "layer is solid before attempting."
            )

        return {
            "verdict": bucket,
            "confidence": 0.7,
            "reasons": reasons,
            "warnings": warnings,
        }
