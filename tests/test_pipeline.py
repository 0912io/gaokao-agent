"""Tests for pipeline orchestration."""

import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaokao_agent import GaokaoAgent
from gaokao_agent.config import Profile


def test_profile_validation():
    """Profile validation should catch missing fields."""
    # Missing all fields
    p = Profile(province="", score=0, rank=0, subjects=[])
    ok, missing = p.validate()
    assert not ok
    assert "province" in missing
    assert "score" in missing
    assert "rank" in missing

    # Valid profile
    p = Profile(province="陕西", score=500, rank=80000,
                subjects=["物理", "化学"])
    ok, missing = p.validate()
    assert ok


def test_track_inference():
    """Track should be inferred from subjects."""
    p = Profile(province="陕西", score=500, rank=80000,
                subjects=["物理", "化学"])
    assert p.track == "physics"

    p = Profile(province="陕西", score=500, rank=80000,
                subjects=["历史", "政治"])
    assert p.track == "history"


def test_demo_pipeline():
    """Demo pipeline should complete without errors."""
    agent = GaokaoAgent()
    profile = Profile(
        province="陕西", score=520, rank=85000,
        subjects=["物理", "化学", "生物"],
    )
    result = agent.run(profile)
    assert result.phase == "OUTPUT_DELIVERED"
    assert len(result.errors) == 0
    assert len(result.recommendations) > 0
    assert len(result.risks) >= 0


def test_pipeline_stages_match_the_work():
    """Phase names follow profile, data, council, assembly, then output checks."""
    agent = GaokaoAgent()
    profile = Profile(
        province="陕西", score=520, rank=85000,
        subjects=["物理", "化学", "生物"],
    )
    result = agent.run(profile)
    history = [step["to"] for step in agent.pipeline.sm.state["phase_history"]]
    assert history == [
        "CONSTRAINTS_COLLECTED",
        "DATA_ACQUIRED",
        "DELIBERATED",
        "PLAN_GENERATED",
        "OUTPUT_DELIVERED",
    ]
    assert result.phase == "OUTPUT_DELIVERED"
    assert not hasattr(agent.pipeline, "pe")


def test_run_with_kwargs_when_profile_omitted():
    """Omitting profile builds one from kwargs and still runs the pipeline."""
    fields = dict(
        province="陕西", score=520, rank=85000,
        subjects=["物理", "化学", "生物"],
    )
    via_profile = GaokaoAgent().run(Profile(**fields))
    via_kwargs = GaokaoAgent().run(**fields)
    assert via_kwargs.profile.province == fields["province"]
    assert via_kwargs.profile.score == fields["score"]
    assert via_kwargs.profile.rank == fields["rank"]
    assert via_kwargs.profile.subjects == fields["subjects"]
    assert via_kwargs.phase == "OUTPUT_DELIVERED"
    assert via_kwargs.errors == []
    assert via_kwargs.recommendations == via_profile.recommendations
    assert via_kwargs.risks == via_profile.risks

    rejected = GaokaoAgent().run(province="", score=0, rank=0, subjects=[])
    assert rejected.phase == "REJECTED"
    assert rejected.recommendations == []
    assert rejected.errors
    assert "profile_invalid" in rejected.errors[0]


def test_council_loaded():
    """Council should have all 10 agents by default."""
    agent = GaokaoAgent()
    assert len(agent.council.agents) == 10

    # Check veto agents
    veto_agents = [a for a in agent.council.agents if a.veto]
    assert len(veto_agents) == 3  # safety, verifier, quality


if __name__ == "__main__":
    test_profile_validation()
    test_track_inference()
    test_demo_pipeline()
    test_pipeline_stages_match_the_work()
    test_run_with_kwargs_when_profile_omitted()
    test_council_loaded()
    print("All tests passed!")
