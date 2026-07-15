"""Tests for pipeline orchestration."""

import sys
import os
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
    test_council_loaded()
    print("All tests passed!")
