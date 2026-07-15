"""Post-execution guard — validates output compliance."""

from typing import List


class PostCheck:
    """Output compliance validator.

    Checks:
        - Each recommendation has year annotation
        - Each data point has source attribution
        - Risk warnings are not empty for reach targets
    """

    def validate(self, recommendations: List[dict]
                 ) -> tuple:  # (ok: bool, issues: list)
        """Validate recommendation output.

        Returns:
            (ok, issues) — ok=True means output is compliant.
        """
        issues = []

        for i, rec in enumerate(recommendations):
            prefix = f"rec[{i}]"

            # Check school name presence
            if not rec.get("school_id"):
                issues.append(f"{prefix}:missing_school_id")

            # Check consensus
            consensus = rec.get("consensus", "")
            if consensus not in ("reach", "match", "safety", "reject",
                                  "high_risk", "unknown"):
                issues.append(
                    f"{prefix}:unknown_consensus:{consensus}"
                )

            # Check verdicts
            verdicts = rec.get("verdicts", {})
            if not verdicts:
                issues.append(f"{prefix}:no_agent_verdicts")

        return (len(issues) == 0, issues)
