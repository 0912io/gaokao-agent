"""Tests for Profile.validate and Profile.track."""

from gaokao_agent.config import Profile


def test_validate_reports_each_missing_field():
    """Each required field is named when it is empty or non-positive."""
    profile = Profile(province="", score=0, rank=0, subjects=[])
    ok, missing = profile.validate()
    assert ok is False
    assert missing == ["province", "score", "rank", "subjects"]

    only_subjects = Profile(
        province="陕西", score=500, rank=80000, subjects=[],
    )
    ok, missing = only_subjects.validate()
    assert ok is False
    assert missing == ["subjects"]

    only_score = Profile(
        province="陕西", score=-1, rank=80000, subjects=["物理"],
    )
    ok, missing = only_score.validate()
    assert ok is False
    assert missing == ["score"]


def test_validate_accepts_complete_profile():
    """A province, positive score and rank, and subjects are enough."""
    profile = Profile(
        province="陕西", score=520, rank=85000,
        subjects=["物理", "化学", "生物"],
    )
    ok, missing = profile.validate()
    assert ok is True
    assert missing == []


def test_track_from_subjects():
    """Physics wins over history; neither subject leaves the track unknown."""
    physics = Profile(
        province="陕西", score=500, rank=80000,
        subjects=["物理", "化学"],
    )
    assert physics.track == "physics"

    both = Profile(
        province="陕西", score=500, rank=80000,
        subjects=["历史", "物理"],
    )
    assert both.track == "physics"

    history = Profile(
        province="陕西", score=500, rank=80000,
        subjects=["历史", "政治"],
    )
    assert history.track == "history"

    unknown = Profile(
        province="陕西", score=500, rank=80000,
        subjects=["化学", "生物"],
    )
    assert unknown.track == "unknown"


if __name__ == "__main__":
    test_validate_reports_each_missing_field()
    test_validate_accepts_complete_profile()
    test_track_from_subjects()
    print("All profile tests passed!")
