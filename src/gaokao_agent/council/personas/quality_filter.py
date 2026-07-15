"""Role: Major quality filter with forward-looking assessment.

Evaluates major quality: breadth vs. narrowness, 2030 outlook,
AI substitution risk, and transfer path availability.
"""

from ..base import BaseAgent
from ...config import Profile


class QualityFilterAgent(BaseAgent):
    name = "quality_filter"
    weight = 2.0
    veto = True
    confidence = "trend"

    NARROW_MAJORS = [
        "旅游管理", "酒店管理", "社会工作", "行政管理",
        "公共事业管理", "市场营销", "电子商务",
    ]

    HIGH_AI_RISK = [
        "翻译", "会计", "审计", "档案学",
    ]

    def analyze(self, school: dict, profile: Profile) -> dict:
        reasons = []
        warnings = []

        majors = school.get("majors", [])
        major_str = " ".join(str(m) for m in majors) if majors else ""
        transfer_policy = school.get("transfer_policy", "一般")

        # 1. Narrow major detection
        for nm in self.NARROW_MAJORS:
            if nm in major_str:
                warnings.append(
                    f"Narrow major '{nm}' — low industry barrier, "
                    "limited career mobility. Only accept if transfer "
                    "policy is favorable or school brand is strong."
                )

        # 2. AI substitution risk
        for risk_major in self.HIGH_AI_RISK:
            if risk_major in major_str:
                warnings.append(
                    f"'{risk_major}' faces high AI substitution risk "
                    "by 2030. Verify curriculum includes AI-resistant "
                    "skills (judgment, creativity, interpersonal)."
                )

        # 3. Transfer policy as safety valve
        if transfer_policy in ("容易", "较容易"):
            reasons.append(
                f"Transfer policy: {transfer_policy} — provides escape "
                "route if assigned to undesirable major."
            )
        elif transfer_policy in ("困难", "禁止"):
            warnings.append(
                f"Transfer policy: {transfer_policy} — no escape route. "
                "Must be certain about major acceptance."
            )

        # 4. Broad foundation preference
        is_broad = school.get("is_broad_foundation", True)
        if is_broad:
            reasons.append(
                "Broad foundation curriculum — better long-term "
                "adaptability vs. narrow skill training."
            )

        # Verdict
        has_narrow = any(nm in major_str for nm in self.NARROW_MAJORS)
        has_ai_risk = any(rm in major_str for rm in self.HIGH_AI_RISK)
        can_transfer = transfer_policy in ("容易", "较容易")

        if has_narrow and not can_transfer:
            verdict, confidence = "reject", 0.8
        elif has_ai_risk and not can_transfer:
            verdict, confidence = "reach", 0.4
        elif warnings:
            verdict, confidence = "reach", 0.5
        else:
            verdict, confidence = "match", 0.8

        if not reasons and not warnings:
            reasons.append("Major quality check passed — no issues.")

        return {
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "warnings": warnings,
        }
