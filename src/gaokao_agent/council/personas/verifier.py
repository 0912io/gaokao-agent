"""Role: Rank and charter verifier.

Validates historical rank data against official sources, checks admission
rules (专业清 vs 分数清), and flag any charter restrictions.
"""

from ..base import BaseAgent
from ...config import Profile


class VerifierAgent(BaseAgent):
    name = "verifier"
    weight = 2.0
    veto = True
    confidence = "data"

    def analyze(self, school: dict, profile: Profile) -> dict:
        reasons = []
        warnings = []

        min_rank = school.get("min_rank", 0)
        subjects_required = school.get("subjects_required", "")

        # 1. Rank data quality check
        if not min_rank:
            warnings.append(
                "No historical rank data — estimate only, "
                "high uncertainty. Treat as speculative."
            )

        # 2. Subject match check (hard veto)
        if subjects_required:
            # Decode xuanke string: each subject req maps to a code
            user_subjects = set(s.lower() for s in profile.subjects)
            required_lower = str(subjects_required).lower()
            # Check if all required subjects are in user's set
            # Simplified: check keyword presence
            subject_keywords = {
                "物理": "物理", "历史": "历史", "化学": "化学",
                "生物": "生物", "政治": "政治", "地理": "地理",
            }
            for cn, en in subject_keywords.items():
                if cn in required_lower and cn not in user_subjects:
                    warnings.append(
                        f"Subject mismatch: requires {cn} — not selected. "
                        "This school is INELIGIBLE."
                    )

        # 3. Admission rule check (专业清 = high risk)
        admit_rule = school.get("admit_rule", "")
        if "专业清" in str(admit_rule):
            warnings.append(
                "Admission uses 专业清 (major-first priority) — "
                "high risk of major reassignment. Verify acceptable majors."
            )
        elif "分数清" in str(admit_rule):
            reasons.append("分数清 (score-first) — favorable admission rule.")

        # 4. Charter restrictions
        charter = school.get("charter_notes", "")
        if charter:
            reasons.append("Charter restrictions noted — verify manually.")

        # Verdict
        has_ineligibility = any("INELIGIBLE" in w for w in warnings)
        if has_ineligibility:
            verdict, confidence = "reject", 1.0
        elif not min_rank:
            verdict, confidence = "reach", 0.4
        else:
            rank_gap = min_rank - profile.rank
            if rank_gap < -5000:
                verdict, confidence = "safety", 0.9
            elif rank_gap < 3000:
                verdict, confidence = "match", 0.8
            else:
                verdict, confidence = "reach", 0.6

        if not reasons and not warnings:
            reasons.append("Verification passed — no issues detected.")

        return {
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "warnings": warnings,
        }
