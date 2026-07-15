"""Role: City-industry matching analyst.

Evaluates the fit between a school's location and the student's
intended industry — some cities dominate specific sectors.
"""

from ..base import BaseAgent
from ...config import Profile


class IndustryMatcherAgent(BaseAgent):
    name = "industry_matcher"
    weight = 2.0
    confidence = "trend"

    CITY_INDUSTRY = {
        "北京": ["互联网", "AI", "金融", "教育", "文化"],
        "上海": ["金融", "外贸", "AI", "生物医药"],
        "深圳": ["硬件", "IoT", "AI", "金融科技"],
        "杭州": ["电商", "互联网", "AI", "云计算"],
        "成都": ["游戏", "军工", "互联网"],
        "西安": ["军工", "航天", "半导体"],
        "武汉": ["汽车", "光电子", "教育"],
        "南京": ["芯片", "汽车", "教育"],
        "广州": ["外贸", "汽车", "快消"],
        "苏州": ["制造业", "半导体", "生物医药"],
    }

    def analyze(self, school: dict, profile: Profile) -> dict:
        reasons = []
        warnings = []

        city = school.get("city", "")
        city_industries = self.CITY_INDUSTRY.get(city, [])
        preferences = profile.preferences or []

        # 1. City-industry match
        if city_industries:
            reasons.append(
                f"{city} industry strengths: {', '.join(city_industries[:3])}. "
                "Evaluate alignment with career goals."
            )
        else:
            reasons.append(
                f"{city} — no industry cluster data. "
                "Verify local job market alignment."
            )

        # 2. Preference matching
        industry_prefs = [p for p in preferences
                          if any(p in ind for ind in city_industries)]
        if industry_prefs:
            reasons.append(
                f"Preference-industry match: {', '.join(industry_prefs[:2])}"
            )

        # 3. Remote location flag
        city_level = school.get("city_level", 3)
        if city_level >= 5:
            warnings.append(
                f"Low-tier city ({city}) — limited industry ecosystem. "
                "Summer internships may require relocation."
            )

        # 4. Order-class program detection
        if school.get("order_class", False):
            reasons.append(
                "Order-class (订单班) program — direct industry pipeline, "
                "guaranteed employment in partner companies."
            )

        # Verdict
        if industry_prefs:
            verdict, confidence = "match", 0.8
        elif city_level >= 5:
            verdict, confidence = "reach", 0.6
        else:
            verdict, confidence = "match", 0.7

        return {
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "warnings": warnings,
        }
