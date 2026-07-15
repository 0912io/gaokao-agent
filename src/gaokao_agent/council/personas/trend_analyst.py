"""Role: New institution discovery.

Tracks newly established or upgraded schools, first-time recruiting
institutions, and expanded enrollment patterns.
"""

from ..base import BaseAgent
from ...config import Profile


class TrendAnalystAgent(BaseAgent):
    name = "trend_analyst"
    weight = 3.0
    confidence = "trend"

    def analyze(self, school: dict, profile: Profile) -> dict:
        reasons = []
        warnings = []

        is_new_school = school.get("is_new_school", False)
        enrollment_change = school.get("enrollment_change", 0.0)  # e.g. 0.3 = +30%
        min_rank = school.get("min_rank", 0)

        # 1. New school detection
        if is_new_school:
            reasons.append(
                "NEW SCHOOL: First year recruiting — zero brand awareness, "
                "competitors have no reference point. Strong opportunity."
            )

        # 2. Significant enrollment expansion
        if enrollment_change > 0.3:
            rank_boost = int(enrollment_change * 10000)
            reasons.append(
                f"Expansion +{enrollment_change:.0%} — estimated rank "
                f"threshold will drop ~{rank_boost} positions. "
                "Entry easier than historical data suggests."
            )
        elif enrollment_change < -0.2:
            warnings.append(
                f"Contraction {enrollment_change:.0%} — fewer seats, "
                "rank threshold may RISE. More competitive than expected."
            )

        # 3. Rank trend analysis
        rank_trend = school.get("rank_trend", [])
        if len(rank_trend) >= 2:
            trend_1 = rank_trend[-1]
            trend_2 = rank_trend[-2]
            if trend_1 > trend_2 + 3000:
                reasons.append("Rank dropping (easier entry) — favorable trend.")
            elif trend_1 < trend_2 - 3000:
                warnings.append("Rank rising (harder entry) — competitive pressure.")

        # Verdict
        rank_gap = min_rank - profile.rank
        if is_new_school or enrollment_change > 0.3:
            verdict, confidence = "reach", 0.8
        elif enrollment_change < -0.2:
            verdict, confidence = "reach", 0.4
        elif rank_gap < 0:
            verdict, confidence = "safety", 0.9
        elif rank_gap < 3000:
            verdict, confidence = "match", 0.7
        else:
            verdict, confidence = "reach", 0.5

        if not reasons:
            reasons.append("No notable enrollment trend signal.")

        return {
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "warnings": warnings,
        }
