from __future__ import annotations
import json, time
from typing import List, Optional, Dict, Any
import typer
from rich.table import Table
from rich.console import Console

from .status_mode import summarize
from .providers import github as gh
from .providers import gitlab as gls  # homepage-based GitLab provider

app = typer.Typer(
    add_completion=False,
    help="Provider status for GitHub and GitLab (official status pages).",
)

def _parse_targets(targets: Optional[str]) -> List[str]:
    if not targets:
        return ["github", "gitlab"]
    return [t.strip().lower() for t in targets.split(",") if t.strip()]

@app.callback(invoke_without_command=True)
def _root(
    targets: Optional[str] = typer.Option(None, "--targets", help="Comma list: github,gitlab"),
    output_format: str = typer.Option("table", "--format", case_sensitive=False, help="table|json"),
    timeout: float = typer.Option(8.0, "--timeout", min=2.0, help="HTTP timeout seconds"),
):
    """
    Single-command CLI: fetch provider status and print table or JSON.
    """
    chosen = _parse_targets(targets)
    rows: List[Dict[str, Any]] = []
    exit_codes: List[int] = []

    def fetch_one(name: str, fn):
        start = time.perf_counter()
        try:
            s = fn(timeout=timeout)
            latency_ms = int((time.perf_counter() - start) * 1000)
            ind = s["status"]["indicator"]
            desc = s["status"]["description"]
            _, code = summarize(name, ind, desc)
            rows.append(
                {
                    "provider": name,
                    "indicator": ind,
                    "description": desc,
                    "latency_ms": latency_ms,
                    "source": "official",
                }
            )
            exit_codes.append(code)
        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            rows.append(
                {
                    "provider": name,
                    "indicator": "error",
                    "description": f"{type(e).__name__}: {e}",
                    "latency_ms": latency_ms,
                    "source": "official",
                }
            )
            exit_codes.append(1)  # degraded on fetch error

    if "github" in chosen:
        fetch_one("github", gh.fetch_summary)
    if "gitlab" in chosen:
        fetch_one("gitlab", gls.fetch_summary)

    if output_format.lower() == "json":
        typer.echo(json.dumps(rows, indent=2))
    else:
        t = Table(title="Provider Status")
        t.add_column("Provider")
        t.add_column("Indicator")
        t.add_column("Description")
        t.add_column("Latency(ms)", justify="right")
        t.add_column("Source")
        for r in rows:
            t.add_row(
                r["provider"],
                r["indicator"],
                r["description"] or "-",
                str(r["latency_ms"]),
                r.get("source", "official"),
            )
        Console().print(t)

    # Exit with the worst code across providers (0 ok, 1 degraded/error, 2 major/critical)
    raise typer.Exit(max(exit_codes) if exit_codes else 1)

# ---- exports / entrypoints ----
def entrypoint():
    # used by console_scripts in pyproject.toml
    app()

# expose the Typer app as `main` for tests (runner.invoke(main, ...))
main = app

if __name__ == "__main__":
    # Allow: python -m status_checker.cli --help
    app()
