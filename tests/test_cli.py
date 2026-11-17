"""CLI tests for demo, run, list-agents, and --version."""

import json

from click.testing import CliRunner

from gaokao_agent import __version__
from gaokao_agent.cli import main
from gaokao_agent.config import Settings
from gaokao_agent.engine.pipeline import Pipeline, PipelineResult


RUN_ARGS = [
    "--province", "陕西",
    "--score", "520",
    "--rank", "85000",
    "--subjects", "物理,化学,生物",
]


def test_settings_have_no_data_source_switch():
    """Presentation settings stay on the CLI and do not name a data backend."""
    settings = Settings(verbose=True, output_format="table")
    assert settings.verbose is True
    assert settings.output_format == "table"
    assert not hasattr(settings, "demo_mode")


def test_version():
    """--version prints the package version."""
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "gaokao-agent" in result.output
    assert __version__ in result.output


def test_list_agents():
    """list-agents prints the default council, including veto marks."""
    result = CliRunner().invoke(main, ["list-agents"])
    assert result.exit_code == 0
    assert "Agents in council:" in result.output
    assert result.output.count("weight=") == 10
    assert result.output.count("[VETO]") == 3
    assert "strategist" in result.output
    assert "synthesizer" in result.output


def test_demo_uses_pipeline_validation():
    """demo completes and does not print its own pre-check line."""
    result = CliRunner().invoke(main, ["demo"])
    assert result.exit_code == 0
    assert "DEMO Mode" in result.output
    assert "Pre-check" not in result.output
    assert "Phase: OUTPUT_DELIVERED" in result.output
    assert "Profile validation FAILED" not in result.output
    assert "Demo complete" in result.output


def test_demo_prints_failure_when_pipeline_rejects():
    """A pipeline rejection is printed and skips the results section."""
    original = Pipeline.run

    def fake_run(self, profile, data_source):
        return PipelineResult(
            profile=profile,
            phase="REJECTED",
            errors=["profile_invalid:['province']"],
        )

    Pipeline.run = fake_run
    try:
        result = CliRunner().invoke(main, ["demo"])
    finally:
        Pipeline.run = original

    assert result.exit_code == 1
    assert "Profile validation FAILED: profile_invalid:['province']" in result.output
    assert "RESULTS" not in result.output
    assert "Demo complete" not in result.output


def test_run_help_names_the_demo_data_source():
    """run help states that school data is the built-in demo source."""
    result = CliRunner().invoke(main, ["run", "--help"])
    assert result.exit_code == 0
    help_text = " ".join(result.output.split())
    assert "built-in demo data source" in help_text
    assert "no separate live data backend" in help_text
    assert "JSON status line" in help_text


def test_run_json_omits_status_line_unless_verbose():
    """JSON mode prints the result, and the status line only with --verbose."""
    quiet = CliRunner().invoke(main, ["run", *RUN_ARGS])
    assert quiet.exit_code == 0
    assert '"status": "running"' not in quiet.output
    payload = json.loads(quiet.output)
    assert payload["phase"] == "OUTPUT_DELIVERED"
    assert payload["profile"]["province"] == "陕西"
    assert payload["errors"] == []
    assert payload["recommendations"]

    verbose = CliRunner().invoke(main, ["run", "--verbose", *RUN_ARGS])
    assert verbose.exit_code == 0
    first, rest = verbose.output.split("\n", 1)
    status = json.loads(first)
    assert status["status"] == "running"
    assert status["profile"]["province"] == "陕西"
    assert status["profile"]["score"] == 520
    assert status["profile"]["subjects"] == ["物理", "化学", "生物"]
    body = json.loads(rest)
    assert body["phase"] == "OUTPUT_DELIVERED"
    assert body["recommendations"] == payload["recommendations"]


def test_run_table_omits_status_line_unless_verbose():
    """Table mode stays a table, with the status line only under --verbose."""
    quiet = CliRunner().invoke(main, ["run", "--format", "table", *RUN_ARGS])
    assert quiet.exit_code == 0
    assert '"status": "running"' not in quiet.output
    assert quiet.output.startswith("Phase: OUTPUT_DELIVERED\n")
    assert "Recommendations:" in quiet.output
    assert '"recommendations"' not in quiet.output

    verbose = CliRunner().invoke(main, [
        "run", "--verbose", "--format", "table", *RUN_ARGS,
    ])
    assert verbose.exit_code == 0
    status_line, table = verbose.output.split("\n", 1)
    status = json.loads(status_line)
    assert status["status"] == "running"
    assert status["profile"]["rank"] == 85000
    assert table.startswith("Phase: OUTPUT_DELIVERED\n")
    assert "Recommendations:" in table
    assert '"recommendations"' not in table


if __name__ == "__main__":
    test_settings_have_no_data_source_switch()
    test_version()
    test_list_agents()
    test_demo_uses_pipeline_validation()
    test_demo_prints_failure_when_pipeline_rejects()
    test_run_help_names_the_demo_data_source()
    test_run_json_omits_status_line_unless_verbose()
    test_run_table_omits_status_line_unless_verbose()
    print("All CLI tests passed!")
