"""Tests for the pipeline's profile pre-check."""

import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaokao_agent.config import Profile
from gaokao_agent.guards.pre_check import PreCheck


def _profile(**overrides):
    fields = dict(
        province="陕西", score=520, rank=85000,
        subjects=["物理", "化学", "生物"],
    )
    fields.update(overrides)
    return Profile(**fields)


def test_precheck_accepts_complete_profile():
    """A complete in-range profile has no issues and may proceed."""
    ok, issues = PreCheck().validate_profile(_profile())
    assert ok is True
    assert issues == []


def test_precheck_blocks_missing_fields():
    """Missing required fields are hard failures and still list soft issues."""
    ok, issues = PreCheck().validate_profile(
        Profile(province="", score=0, rank=0, subjects=[])
    )
    assert ok is False
    assert "missing_province" in issues
    assert "missing_score" in issues
    assert "missing_rank" in issues
    assert "missing_subjects" in issues
    assert "score_out_of_range:0" in issues
    assert not any(item.startswith("unknown_province:") for item in issues)


def test_precheck_soft_issues_do_not_block():
    """Unknown province, score range, and subject names are warnings."""
    ok, issues = PreCheck().validate_profile(_profile(
        province="火星",
        score=50,
        subjects=["物理", "音乐"],
    ))
    assert ok is True
    assert "unknown_province:火星" in issues
    assert "score_out_of_range:50" in issues
    assert "invalid_subjects:['音乐']" in issues


def test_precheck_score_bounds_are_inclusive():
    """100 and 750 are inside the range; the values beside them are not."""
    checker = PreCheck()
    assert checker.validate_profile(_profile(score=100)) == (True, [])
    assert checker.validate_profile(_profile(score=750)) == (True, [])

    low_ok, low_issues = checker.validate_profile(_profile(score=99))
    high_ok, high_issues = checker.validate_profile(_profile(score=751))
    assert low_ok is True
    assert high_ok is True
    assert low_issues == ["score_out_of_range:99"]
    assert high_issues == ["score_out_of_range:751"]


def test_precheck_missing_subjects_stays_hard_with_other_warnings():
    """A soft province warning does not hide a missing-subjects failure."""
    ok, issues = PreCheck().validate_profile(_profile(
        province="火星",
        subjects=[],
    ))
    assert ok is False
    assert issues == ["missing_subjects", "unknown_province:火星"]


if __name__ == "__main__":
    test_precheck_accepts_complete_profile()
    test_precheck_blocks_missing_fields()
    test_precheck_soft_issues_do_not_block()
    test_precheck_score_bounds_are_inclusive()
    test_precheck_missing_subjects_stays_hard_with_other_warnings()
    print("All pre-check tests passed!")
