"""Cross-validator — multi-source data consistency checker.

Compares rank/score data from multiple sources and flags discrepancies.
Standalone helper. Pipeline.run does not call it: each school comes from
one data source and has no paired rank/score observations to compare.
"""

from typing import List, Tuple


class CrossValidator:
    """Validates data consistency across multiple sources.

    Classification:
        deviation < 5%   → PASS
        deviation 5-10%  → WARN (use, but flag)
        deviation > 10%  → REJECT
    """

    RANK_THRESHOLD_WARN = 0.05
    RANK_THRESHOLD_REJECT = 0.10
    SCORE_THRESHOLD_WARN = 3
    SCORE_THRESHOLD_REJECT = 8

    def validate_rank(self, source_a: dict, source_b: dict
                      ) -> Tuple[bool, float, str]:
        """Compare rank data from two sources.

        Args:
            source_a: {"name": "excel", "rank": 115000, "year": 2025}
            source_b: {"name": "api", "rank": 113500, "year": 2025}

        Returns:
            (ok, deviation, message)
        """
        rank_a = source_a.get("rank", 0)
        rank_b = source_b.get("rank", 0)
        name_a = source_a.get("name", "source_a")
        name_b = source_b.get("name", "source_b")

        if not rank_a or not rank_b:
            return False, 1.0, f"Missing rank data: {name_a}={rank_a}, {name_b}={rank_b}"

        deviation = abs(rank_a - rank_b) / max(rank_b, 1)

        if deviation < self.RANK_THRESHOLD_WARN:
            return True, deviation, f"PASS: {name_a}({rank_a}) vs {name_b}({rank_b}) = {deviation:.1%}"
        elif deviation < self.RANK_THRESHOLD_REJECT:
            return True, deviation, f"WARN: {name_a}({rank_a}) vs {name_b}({rank_b}) = {deviation:.1%} (>5%)"
        else:
            return False, deviation, f"REJECT: {name_a}({rank_a}) vs {name_b}({rank_b}) = {deviation:.1%} (>10%)"

    def validate_score(self, source_a: dict, source_b: dict
                       ) -> Tuple[bool, int, str]:
        """Compare score data from two sources."""
        score_a = source_a.get("score", 0)
        score_b = source_b.get("score", 0)
        name_a = source_a.get("name", "source_a")
        name_b = source_b.get("name", "source_b")

        diff = abs(score_a - score_b)

        if diff <= self.SCORE_THRESHOLD_WARN:
            return True, diff, f"PASS: {name_a}({score_a}) vs {name_b}({score_b}) = {diff}分"
        elif diff <= self.SCORE_THRESHOLD_REJECT:
            return True, diff, f"WARN: {name_a}({score_a}) vs {name_b}({score_b}) = {diff}分 (>3分)"
        else:
            return False, diff, f"REJECT: {name_a}({score_a}) vs {name_b}({score_b}) = {diff}分 (>8分)"

    def validate_school(self, sources: List[dict]) -> dict:
        """Cross-validate a school across N sources.

        Args:
            sources: List of {"name": str, "rank": int, "score": int, "year": int}

        Returns:
            {"valid": bool, "used": [...], "excluded": [...], "warnings": [...]}
        """
        valid = []
        excluded = []
        warnings = []

        for i, src_a in enumerate(sources):
            for j, src_b in enumerate(sources):
                if j <= i:
                    continue
                ok, dev, msg = self.validate_rank(src_a, src_b)
                if ok:
                    if "WARN" in msg:
                        warnings.append(msg)
                    if src_a not in valid:
                        valid.append(src_a)
                    if src_b not in valid:
                        valid.append(src_b)
                else:
                    excluded.append({"reason": msg, "source": src_b})

        return {
            "valid": len(valid) >= 1,
            "used": valid,
            "excluded": excluded,
            "warnings": warnings,
        }
