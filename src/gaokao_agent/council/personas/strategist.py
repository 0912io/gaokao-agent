"""Role: Elite university path specialist.

Focuses on 985/211 access strategies: branch campuses, joint programs,
Sino-foreign cooperation, and college-to-university upgrades.
"""

from ..base import BaseAgent
from ...config import Profile


class StrategistAgent(BaseAgent):
    name = "strategist"
    weight = 4.5
    confidence = "strategy"

    def analyze(self, school: dict, profile: Profile) -> dict:
        reasons = []
        warnings = []
        min_rank = school.get("min_rank", 0)
        label = school.get("label", "")
        is_985 = "985" in str(label)
        is_211 = "211" in str(label)

        rank_gap = min_rank - profile.rank

        # 1. Elite school strategy
        if is_985 or is_211:
            if rank_gap > 0 and rank_gap < 5000:
                reasons.append(
                    f"Elite school ({label}) within reach — brand value "
                    "outweighs major fit. Recommend aggressive approach."
                )
            elif rank_gap > 0:
                reasons.append(
                    f"Elite school ({label}) — stretch target, "
                    "consider branch campus or joint program as alternative."
                )

        # 2. Branch campus / joint program detection
        school_type = school.get("type", "")
        if "分校区" in str(school_type) or "联合培养" in str(school_type):
            reasons.append(
                "Branch campus or joint program — lower entry barrier, "
                "same diploma. Strong strategic play."
            )

        # 3. Sino-foreign cooperation
        if "中外合作" in str(school_type):
            tuition = school.get("tuition", 0)
            reasons.append(
                f"Sino-foreign program (tuition: {tuition}/yr) — "
                "significantly lower score threshold. "
                "Verify diploma annotation before committing."
            )

        # Verdict
        if rank_gap < -3000:
            verdict, confidence = "safety", 0.9
        elif rank_gap < 2000:
            verdict, confidence = "match", 0.8
        elif rank_gap < 8000:
            verdict, confidence = "reach", 0.7
        else:
            verdict, confidence = "reach", 0.5

        if not reasons:
            reasons.append("Standard evaluation — no special strategic signal.")

        return {
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "warnings": warnings,
        }
