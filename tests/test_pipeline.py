"""Tests for pipeline orchestration."""

from gaokao_agent import GaokaoAgent
from gaokao_agent.config import Profile
from gaokao_agent.data.demo_source import DemoDataSource
from gaokao_agent.engine.pipeline import Pipeline


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


def test_default_run_leaves_memory_mcp_and_citation_gates_false():
    """A successful default run does not mark memory, MCP, or citations."""
    profile = Profile(
        province="陕西", score=520, rank=85000,
        subjects=["物理", "化学", "生物"],
    )

    def assert_gates(result, state_machine):
        gates = state_machine.state["execution_gates"]
        assert result.phase == "OUTPUT_DELIVERED"
        assert result.errors == []
        assert not gates.get("memory_loaded")
        assert not gates.get("mcp_called")
        assert not gates.get("citation_added")

    agent = GaokaoAgent()
    assert_gates(agent.run(profile), agent.pipeline.sm)

    pipeline = Pipeline()
    assert_gates(pipeline.run(profile, DemoDataSource()), pipeline.sm)


def test_council_loaded():
    """Council should have all 10 agents by default."""
    agent = GaokaoAgent()
    assert len(agent.council.agents) == 10

    # Check veto agents
    veto_agents = [a for a in agent.council.agents if a.veto]
    assert len(veto_agents) == 3  # safety, verifier, quality


if __name__ == "__main__":
    test_demo_pipeline()
    test_pipeline_stages_match_the_work()
    test_run_with_kwargs_when_profile_omitted()
    test_default_run_leaves_memory_mcp_and_citation_gates_false()
    test_council_loaded()
    print("All tests passed!")
