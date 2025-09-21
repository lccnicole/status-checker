import subprocess, sys, os, json, pathlib

def run_cli(args):
    # Install the package in editable mode for the test run
    return subprocess.run([sys.executable, "-m", "status_checker.cli"] + args, capture_output=True, text=True)

def test_cli_help():
    p = run_cli(["--help"])
    assert p.returncode == 0
    assert "Check reachability" in p.stdout or "Usage" in p.stdout

import json
from typer.testing import CliRunner
from status_checker.cli import main
from status_checker.providers import github as gh, gitlab as gls

runner = CliRunner()

def test_cli_json_worst_exit(monkeypatch):
    # GitHub OK (none), GitLab degraded (minor) -> overall exit code should be 1
    monkeypatch.setattr(gh, "fetch_summary", lambda timeout=8.0: {
        "status": {"indicator": "none", "description": "OK"}
    })
    monkeypatch.setattr(gls, "fetch_summary", lambda timeout=8.0: {
        "status": {"indicator": "minor", "description": "GitLab Pages: Degraded Performance"}
    })

    result = runner.invoke(main, ["--format", "json"])
    assert result.exit_code == 1
    rows = json.loads(result.stdout)
    assert rows[0]["provider"] == "github"
    assert rows[1]["provider"] == "gitlab"
    assert any(r["indicator"] == "minor" for r in rows)

def test_cli_targets_github_only_ok(monkeypatch):
    # Only github requested, and it's green -> exit code 0 and one row
    monkeypatch.setattr(gh, "fetch_summary", lambda timeout=8.0: {
        "status": {"indicator": "none", "description": "OK"}
    })

    result = runner.invoke(main, ["--targets", "github", "--format", "json"])
    assert result.exit_code == 0
    rows = json.loads(result.stdout)
    assert len(rows) == 1
    assert rows[0]["provider"] == "github"
    assert rows[0]["indicator"] == "none"
