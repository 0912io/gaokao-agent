"""Tests for council voting engine."""

import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaokao_agent.council import Council
from gaokao_agent.council.personas import (
    StrategistAgent, DetectiveAgent, SafetyAuditorAgent,
    VerifierAgent, ALL_AGENTS,
)
from gaokao_agent.config import Profile


SAMPLE_SCHOOL = {
    "id": "test-001",
    "name": "测试大学",
    "min_rank": 90000,
    "majors": ["计算机科学", "软件工程"],
    "subjects_required": "物理+化学",
    "label": "985",
    "city": "北京",
    "city_level": 1,
    "type": "公办",
    "tuition": 5000,
    "cleanliness": 0.95,
    "transfer_policy": "较容易",
    "is_new": False,
    "is_new_school": False,
    "is_cross_new": False,
    "new_major": False,
    "upgraded": False,
    "enrollment_change": 0.1,
    "order_class": False,
    "supplementary_history": False,
    "admit_rule": "分数清",
    "rank_trend": [92000, 91000, 90000],
}

SAMPLE_PROFILE = Profile(
    province="陕西", score=500, rank=85000,
    subjects=["物理", "化学", "生物"],
)


def test_council_initialization():
    """Council should accept agents."""
    council = Council(auto_load=False)
    council.add(StrategistAgent())
    council.add(DetectiveAgent())
    assert len(council.agents) == 2


def test_council_deliberation():
    """Council should produce verdicts for all agents."""
    council = Council(auto_load=False)
    council.add(StrategistAgent())
    council.add(DetectiveAgent())
    council.add(SafetyAuditorAgent())
    council.add(VerifierAgent())
    assert len(council.agents) == 4

    results = council.deliberate([SAMPLE_SCHOOL], SAMPLE_PROFILE)
    school_results = results.get("test-001", {})
    assert len(school_results) == 4
    assert "strategist" in school_results
    assert "detective" in school_results


def test_consensus_with_safety():
    """Elite school with high cleanliness should get match or safety."""
    council = Council()
    for agent_cls in ALL_AGENTS:
        council.add(agent_cls())

    results = council.deliberate([SAMPLE_SCHOOL], SAMPLE_PROFILE)
    votes = results.get("test-001", {})
    consensus = council.consensus(votes)
    assert consensus in ("match", "safety", "reach")


def test_veto_mechanism():
    """Safety auditor should veto dangerous schools."""
    council = Council(auto_load=False)
    council.add(StrategistAgent())
    council.add(SafetyAuditorAgent())

    dangerous_school = {**SAMPLE_SCHOOL}
    dangerous_school["cleanliness"] = 0.2
    dangerous_school["majors"] = ["采矿工程"]
    dangerous_school["label"] = ""  # Not elite

    results = council.deliberate([dangerous_school], SAMPLE_PROFILE)
    votes = results.get("test-001", {})
    consensus = council.consensus(votes)
    assert consensus == "high_risk"


def test_remove_agent():
    """Should be able to remove agents by name."""
    council = Council(auto_load=False)
    council.add(StrategistAgent())
    council.add(DetectiveAgent())
    assert len(council.agents) == 2
    council.remove("strategist")
    assert len(council.agents) == 1
    assert council.agents[0].name == "detective"


if __name__ == "__main__":
    test_council_initialization()
    test_council_deliberation()
    test_consensus_with_safety()
    test_veto_mechanism()
    test_remove_agent()
    print("All council tests passed!")
