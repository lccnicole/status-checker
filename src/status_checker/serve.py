from __future__ import annotations
import os, time, json
from typing import List, Dict, Any
from fastapi import FastAPI
from .providers import github as gh
from .providers import gitlab as gls
from .status_mode import summarize

app = FastAPI(title="status-checker")

def _run_check(targets: List[str], timeout: float) -> Dict[str, Any]:
    rows = []
    exit_codes = []

    def fetch_one(name: str, fn):
        start = time.perf_counter()
        try:
            s = fn(timeout=timeout)
            latency_ms = int((time.perf_counter() - start) * 1000)
            ind = s["status"]["indicator"]
            desc = s["status"]["description"]
            _, code = summarize(name, ind, desc)
            rows.append({
                "provider": name,
                "indicator": ind,
                "description": desc,
                "latency_ms": latency_ms,
                "source": "official",
            })
            exit_codes.append(code)
        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            rows.append({
                "provider": name,
                "indicator": "error",
                "description": f"{type(e).__name__}: {e}",
                "latency_ms": latency_ms,
                "source": "official",
            })
            exit_codes.append(1)

    if "github" in targets: fetch_one("github", gh.fetch_summary)
    if "gitlab" in targets: fetch_one("gitlab", gls.fetch_summary)

    return {"results": rows, "exit_code": max(exit_codes) if exit_codes else 1}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/status")
def status(targets: str | None = None, timeout: float = 8.0):
    chosen = [t.strip().lower() for t in (targets or os.getenv("TARGETS", "github,gitlab")).split(",") if t.strip()]
    t = float(os.getenv("TIMEOUT", timeout))
    return _run_check(chosen, t)
