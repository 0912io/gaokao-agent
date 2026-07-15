"""Role: Game theory arbitrageur.

Corrects for competitor blind spots: enrollment expansion discounting,
subject pool shifts, and risk-averse crowding patterns.
"""

from ..base import BaseAgent
from ...config import Profile


class ArbitrageurAgent(BaseAgent):
    name = "arbitrageur"
    weight = 4.0
    confidence = "strategy"

    def analyze(self, school: dict, profile: Profile) -> dict:
        reasons = []
        warnings = []

        min_rank = school.get("min_rank", 0)
        expansion = school.get("enrollment_change", 0.0)
        cleanliness = school.get("cleanliness", 1.0)
        plan_type = school.get("plan_type", "")

        # 1. Expansion arbitrage: competitors underprice expansion
        if expansion > 0.2:
            reasons.append(
                f"Expansion +{expansion:.0%}: most competitors will NOT "
                "adjust their estimates. Real entry threshold likely drops "
                "more than the naive adjustment suggests."
            )

        # 2. Cleanliness arbitrage: dirty groups scare away competitors
        if cleanliness < 0.5:
            reasons.append(
                "Mixed major group (low cleanliness): competitors avoid "
                "due to reassignment fear. Fewer applicants = lower actual "
                "threshold. BUT verify worst-case major is acceptable."
            )
        elif cleanliness > 0.8:
            reasons.append(
                "Pure major group (high cleanliness): competitors cluster "
                "here for safety. May be MORE competitive than expected."
            )

        # 3. Program type awareness discount
        if "联合培养" in plan_type or "中外合作" in plan_type:
            reasons.append(
                "Joint/Sino-foreign program: cognitive awareness lag — "
                "many applicants don't know or misunderstand this option. "
                "Lower competition density."
            )

        # 4. Crowding pattern analysis
        city = school.get("city", "")
        if city in ("北京", "上海", "深圳", "杭州", "广州"):
            reasons.append(
                "Tier-1 city school: expect crowding from status-seeking "
                "applicants. Actual threshold may be inflated vs. rank data."
            )

        # Verdict
        rank_gap = min_rank - profile.rank
        if expansion > 0.3 or cleanliness < 0.5:
            verdict, confidence = "reach", 0.8
        elif rank_gap < 0:
            verdict, confidence = "safety", 0.9
        elif rank_gap < 5000:
            verdict, confidence = "match", 0.7
        else:
            verdict, confidence = "reach", 0.5

        if not reasons:
            reasons.append("No significant arbitrage signal.")

        return {
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "warnings": warnings,
        }
