"""Role: Information asymmetry detector.

Identifies new programs (first-time enrollment), newly upgraded colleges,
and cross-institution joint degrees — all with low competitor awareness.
"""

from ..base import BaseAgent
from ...config import Profile


class DetectiveAgent(BaseAgent):
    name = "detective"
    weight = 4.5
    confidence = "trend"

    def analyze(self, school: dict, profile: Profile) -> dict:
        reasons = []
        warnings = []

        is_new = school.get("is_new", False)
        is_cross = school.get("is_cross_new", False)  # Cross-institution
        min_rank = school.get("min_rank", 0)

        # 1. First-time enrollment: strongest signal
        if is_new and not min_rank:
            reasons.append(
                "NEW: First-time enrollment — no historical baseline, "
                "competitor awareness near zero. Maximum information asymmetry."
            )
        elif is_new:
            reasons.append(
                "NEW: First-time enrollment with estimated baseline — "
                "still strong asymmetry, verify estimate conservatively."
            )

        # 2. Cross-institution joint degree
        if is_cross:
            reasons.append(
                "CROSS: Joint degree from two institutions — triple "
                "uncertainty (no history, no awareness, degree uncertainty). "
                "Highest-priority pick-up signal."
            )

        # 3. New program window
        new_major = school.get("new_major", False)
        if new_major:
            reasons.append(
                "New major in existing school — competition hasn't "
                "formed yet. First 3 years = best entry window."
            )

        # 4. Recently upgraded college
        upgraded = school.get("upgraded", False)
        if upgraded:
            reasons.append(
                "Recently upgraded institution — brand perception "
                "lagging 3+ years behind reality. Time arbitrage opportunity."
            )

        # Verdict: information asymmetry → grade UP
        rank_gap = min_rank - profile.rank
        if is_new or is_cross:
            verdict, confidence = "reach", 0.8
        elif new_major or upgraded:
            verdict, confidence = "reach", 0.7
        elif rank_gap < 0:
            verdict, confidence = "safety", 0.9
        elif rank_gap < 3000:
            verdict, confidence = "match", 0.8
        else:
            verdict, confidence = "reach", 0.6

        if not reasons:
            reasons.append("No special information asymmetry signal detected.")

        return {
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "warnings": warnings,
        }
