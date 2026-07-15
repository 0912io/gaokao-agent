"""CLI entry point for gaokao-agent."""

import json
import sys

import click

from . import GaokaoAgent
from .config import Profile
from .data.demo_source import DemoDataSource


@click.group()
@click.version_option(version="0.1.0", prog_name="gaokao-agent")
def main():
    """Gaokao Agent — Multi-Agent Collaborative Decision Framework.

    A council of 10 specialized AI agents analyzes college admission
    options using weighted voting, veto power, and multi-source data
    cross-validation.
    """
    pass


@main.command()
def demo():
    """Run demo with built-in fictional data (no setup needed)."""
    click.echo("=" * 60)
    click.echo("  Gaokao Agent — DEMO Mode")
    click.echo("=" * 60)
    click.echo()

    agent = GaokaoAgent()
    profile = Profile(
        province="陕西", score=520, rank=85000,
        subjects=["物理", "化学", "生物"],
        preferences=["冲学校", "捡漏"],
    )

    click.echo(f"Profile: {profile.province} | "
               f"score={profile.score} | rank={profile.rank} | "
               f"subjects={','.join(profile.subjects)}")
    click.echo(f"Track: {profile.track}")
    click.echo()

    # Pre-check
    from .guards.pre_check import PreCheck
    pc = PreCheck()
    ok, issues = pc.validate_profile(profile)
    if not ok:
        click.echo(f"Profile validation FAILED: {issues}")
        sys.exit(1)
    click.echo(f"Pre-check: PASSED")
    click.echo()

    # Load schools
    schools = agent.data_source.get_schools(profile)
    click.echo(f"Schools loaded: {len(schools)}")
    for s in schools:
        click.echo(f"  - {s['name']} ({s.get('label', '无标签')}) "
                   f"min_rank={s.get('min_rank', 'N/A')}")
    click.echo()
    click.echo(f"Agents in council: {len(agent.council.agents)}")
    for a in agent.council.agents:
        veto_mark = " [VETO]" if a.veto else ""
        click.echo(f"  - {a.name} (weight={a.weight}){veto_mark}")
    click.echo()

    # Run deliberation
    click.echo("Deliberating...")
    result = agent.pipeline.run(profile, agent.data_source)

    click.echo()
    click.echo("=" * 60)
    click.echo("  RESULTS")
    click.echo("=" * 60)
    click.echo(f"Phase: {result.phase}")
    click.echo(f"Errors: {result.errors or 'none'}")
    click.echo(f"Recommendations: {len(result.recommendations)}")
    click.echo(f"Risks: {len(result.risks)}")
    click.echo()

    for rec in result.recommendations:
        school_id = rec["school_id"]
        consensus = rec["consensus"]
        click.echo(f"  [{consensus.upper()}] {school_id}")
        for agent_name, v in rec.get("verdicts", {}).items():
            click.echo(f"      {agent_name}: {v.get('verdict', '?')} "
                       f"(conf={v.get('confidence', 0):.1f})")

    click.echo()
    click.echo("Demo complete. Try: gaokao-agent run --help")


@main.command()
@click.option("--province", required=True, help="Province name (e.g. 北京, 广东)")
@click.option("--score", required=True, type=int, help="Total gaokao score")
@click.option("--rank", required=True, type=int, help="Provincial rank (位次)")
@click.option("--subjects", required=True, help="Subjects, comma-separated (e.g. 物理,化学,生物)")
@click.option("--gender", default="", help="Optional: 男/女")
@click.option("--format", "output_format", default="json",
              type=click.Choice(["json", "table"]), help="Output format")
@click.option("--verbose", is_flag=True, help="Verbose output")
def run(province, score, rank, subjects, gender, output_format, verbose):
    """Run full analysis with a student profile."""
    from .config import Settings

    profile = Profile(
        province=province,
        score=score,
        rank=rank,
        subjects=[s.strip() for s in subjects.split(",")],
        gender=gender,
    )

    settings = Settings(verbose=verbose, output_format=output_format)
    agent = GaokaoAgent(settings=settings)

    # For demo, always use demo data
    click.echo(json.dumps({"status": "running", "profile": profile.__dict__},
                          ensure_ascii=False, default=str))

    result = agent.run(profile)

    if output_format == "json":
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        click.echo(f"Phase: {result.phase}")
        click.echo(f"Recommendations: {len(result.recommendations)}")
        for rec in result.recommendations:
            click.echo(f"  [{rec['consensus']}] {rec['school_id']}")


@main.command()
def list_agents():
    """List all available council agents."""
    agent = GaokaoAgent()
    click.echo("Agents in council:")
    for a in agent.council.agents:
        veto = " [VETO]" if a.veto else ""
        click.echo(f"  {a.name:<20} weight={a.weight:<4} "
                   f"confidence={a.confidence:<10}{veto}")


if __name__ == "__main__":
    main()
