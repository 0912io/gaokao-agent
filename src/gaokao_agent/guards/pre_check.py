"""Pre-execution guard — validates input before pipeline runs."""

from ..config import Profile


class PreCheck:
    """Validates student profile before pipeline execution.

    Hard gates (block pipeline):
        - Missing any of the 4 required fields

    Soft warnings (allow but flag):
        - Unusual score range
        - Unknown province
    """

    VALID_PROVINCES = {
        "北京", "天津", "上海", "重庆",
        "河北", "山西", "辽宁", "吉林", "黑龙江",
        "江苏", "浙江", "安徽", "福建", "江西", "山东",
        "河南", "湖北", "湖南", "广东", "海南", "四川",
        "贵州", "云南", "陕西", "甘肃", "青海",
        "广西", "内蒙古", "西藏", "宁夏", "新疆",
    }

    VALID_SUBJECTS = {"物理", "历史", "化学", "生物", "政治", "地理"}

    SCORE_RANGE = (100, 750)

    def validate_profile(self, profile: Profile
                         ) -> tuple:  # (valid: bool, issues: list)
        """Check a profile for completeness and validity.

        Returns:
            (ok, issues) — ok=True means profile can proceed.
        """
        issues = []

        # Hard checks: required fields
        valid, missing = profile.validate()
        if not valid:
            issues.extend(f"missing_{m}" for m in missing)

        # Soft checks: province
        if profile.province and profile.province not in self.VALID_PROVINCES:
            issues.append(f"unknown_province:{profile.province}")

        # Soft checks: score range
        lo, hi = self.SCORE_RANGE
        if not (lo <= profile.score <= hi):
            issues.append(f"score_out_of_range:{profile.score}")

        # Soft checks: subjects
        invalid_subs = [
            s for s in profile.subjects
            if s not in self.VALID_SUBJECTS
        ]
        if invalid_subs:
            issues.append(f"invalid_subjects:{invalid_subs}")

        # Hard failures = "missing_*" issues
        hard_failures = [i for i in issues if i.startswith("missing_")]

        return (len(hard_failures) == 0, issues)
