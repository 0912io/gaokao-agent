"""Role: Fallback strategist — worst-case scenario planning.

Designs alternative pathways if normal admission fails: supplementary
enrollment (征集志愿), lower-tier guarantees, and gap year evaluation.
"""

from ..base import BaseAgent
from ...config import Profile


class FallbackAgent(BaseAgent):
    name = "fallback"
    weight = 1.0
    confidence = "trend"

    def analyze(self, school: dict, profile: Profile) -> dict:
        reasons = []
        warnings = []

        min_rank = school.get("min_rank", 0)
        is_supplementary = school.get("supplementary_history", False)
        rank_gap = min_rank - profile.rank

        # 1. Absolute safety check
        if min_rank and rank_gap < -10000:
            reasons.append(
                "Deep safety margin (10k+ below your rank) — "
                "near-certain admission. Strong backstop option."
            )
        elif min_rank and rank_gap < -5000:
            reasons.append("Solid safety margin — good fallback candidate.")

        # 2. Supplementary enrollment history
        if is_supplementary:
            reasons.append(
                "Appeared in supplementary enrollment (征集志愿) lists — "
                "potential second-chance target if main batch fails."
            )

        # 3. Acceptable minimum evaluation
        transfer_policy = school.get("transfer_policy", "")
        if transfer_policy in ("容易", "较容易"):
            reasons.append(
                "Flexible transfer policy — even if assigned to "
                "undesirable major, can switch later."
            )

        # Verdict
        if rank_gap < -10000:
            verdict, confidence = "safety", 0.95
        elif rank_gap < -5000:
            verdict, confidence = "safety", 0.85
        elif rank_gap < 0:
            verdict, confidence = "safety", 0.7
        else:
            verdict, confidence = "match", 0.6

        if not reasons:
            reasons.append("No special fallback signal — standard evaluation.")

        return {
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "warnings": warnings,
        }
