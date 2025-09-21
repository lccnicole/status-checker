from __future__ import annotations
import httpx
from typing import TypedDict, Dict

class Summary(TypedDict):
    status: Dict[str, str]  # {"indicator": "none|minor|major|critical", "description": "..."}

URL = "https://www.githubstatus.com/api/v2/summary.json"
UA = {"User-Agent": "status-checker/1.0"}

def fetch_summary(timeout: float = 8.0) -> Summary:
    with httpx.Client(timeout=timeout, headers=UA) as client:
        r = client.get(URL)
        r.raise_for_status()
        data = r.json()
        # minimal validation
        ind = data["status"]["indicator"]
        desc = data["status"]["description"]
        return {
            "status": {"indicator": ind, "description": desc}
        }

