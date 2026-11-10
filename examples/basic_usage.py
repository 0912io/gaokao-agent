"""Basic usage example for gaokao-agent."""

from gaokao_agent import GaokaoAgent
from gaokao_agent.config import Profile


def main():
    # Create agent with default settings
    agent = GaokaoAgent()

    # Create a student profile
    profile = Profile(
        province="陕西",
        score=520,
        rank=85000,
        subjects=["物理", "化学", "生物"],
        preferences=["冲学校"],
    )

    # Run the pipeline
    result = agent.run(profile)

    # Print results
    print(f"Pipeline phase: {result.phase}")
    print(f"Errors: {result.errors}")
    print(f"Recommendations: {len(result.recommendations)}")
    print(f"Risks: {len(result.risks)}")
    print()

    for rec in result.recommendations:
        school_id = rec["school_id"]
        consensus = rec["consensus"]
        print(f"[{consensus.upper()}] {school_id}")
        for agent_name, v in rec.get("verdicts", {}).items():
            verdict = v.get("verdict", "?")
            confidence = v.get("confidence", 0)
            reasons = v.get("reasons", [])
            print(f"  {agent_name}: {verdict} (conf={confidence:.1f})")
            for r in reasons:
                print(f"    - {r}")
            print()


if __name__ == "__main__":
    main()
