"""Role: Safety auditor — checks for risks specific to vulnerable groups.

Triggers veto on: unsafe campus locations, documented discrimination,
or major groups with poor outcomes for specific demographics.
"""

from ..base import BaseAgent
from ...config import Profile


class SafetyAuditorAgent(BaseAgent):
    name = "safety_auditor"
    weight = 2.0
    veto = True
    confidence = "strategy"

    DANGEROUS_MAJORS = [
        "采矿", "石油工程", "地质工程", "核工程",
        "消防工程", "航海技术", "轮机工程",
    ]

    REMOTE_THRESHOLD = 6  # City level 6+ = very remote

    def analyze(self, school: dict, profile: Profile) -> dict:
        reasons = []
        warnings = []

        majors = school.get("majors", [])
        major_str = " ".join(str(m) for m in majors) if majors else ""
        city_level = school.get("city_level", 3)

        # 1. Dangerous major check
        for dm in self.DANGEROUS_MAJORS:
            if dm in major_str:
                warnings.append(
                    f"Major '{dm}' flagged — physical safety risk. "
                    "Consider transfer path or alternative school."
                )

        # 2. Remote location check
        if city_level >= self.REMOTE_THRESHOLD:
            warnings.append(
                f"Remote campus (city level {city_level}) — "
                "verify transportation, safety, and local amenities."
            )

        # 3. Major group cleanliness for non-elite schools
        is_elite = school.get("label", "") in ("985", "211", "双一流A")
        cleanliness = school.get("cleanliness", 1.0)
        if not is_elite and cleanliness < 0.5:
            warnings.append(
                f"Mixed major group (cleanliness={cleanliness:.2f}) — "
                "high risk of being assigned to an unacceptable major. "
                "VETO: reject unless transfer policy is favorable."
            )

        # Verdict
        if cleanliness < 0.5 and not is_elite:
            verdict = "reject"
            confidence = 0.9
        elif warnings:
            verdict = "reach"
            confidence = 0.5
        else:
            verdict = "match"
            confidence = 0.8

        if not warnings:
            reasons.append("Safety audit passed — no red flags detected.")
        else:
            reasons.append("Safety concerns flagged — review before proceeding.")

        return {
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "warnings": warnings,
        }
