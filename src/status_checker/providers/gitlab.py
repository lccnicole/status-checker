from __future__ import annotations
import httpx
import re
from html import unescape
from typing import TypedDict, Dict, Optional


class Summary(TypedDict):
    status: Dict[str, str]           # {"indicator": "...", "description": "..."}

URL = "https://status.gitlab.com/"
UA = {"User-Agent": "status-checker/1.0"}

# Map Statuspage component text -> our indicator
COMPONENT_MAP = {
    "operational": "none",
    "degraded performance": "minor",
    "partial outage": "major",
    "major outage": "critical",
}

def _fetch_homepage(timeout: float) -> str:
    with httpx.Client(timeout=timeout, headers=UA) as client:
        r = client.get(URL)
        r.raise_for_status()
        return r.text

def _banner_indicator_from_html(html: str) -> Optional[str]:
    """
    Very light heuristic from the homepage banner text.
    Returns 'none' if it clearly says 'All Systems Operational',
    else None (we'll fall back to component check).
    """
    if "All Systems Operational" in html:
        return "none"
    return None

def _component_status_from_html(html: str, component_name: str) -> Optional[str]:
    """
    Return the component status text for 'component_name', e.g. 'Operational',
    'Degraded Performance', 'Partial Outage', 'Major Outage'. None if not found.
    """
    li_re     = re.compile(r'<li[^>]*>(.*?)</li>', re.I | re.S)
    name_re   = re.compile(r'<[^>]*class="[^"]*name[^"]*"[^>]*>(.*?)</[^>]+>', re.I | re.S)
    status_re = re.compile(r'<[^>]*class="[^"]*(?:component-status|status|component__status)[^"]*"[^>]*>(.*?)</[^>]+>', re.I | re.S)

    target = component_name.strip().lower()
    for li in li_re.findall(html):
        n = name_re.search(li)
        s = status_re.search(li)
        if not n or not s:
            continue
        comp_name = unescape(re.sub(r'<[^>]+>', '', n.group(1))).strip()
        comp_stat = unescape(re.sub(r'<[^>]+>', '', s.group(1))).strip()
        if comp_name.lower() == target:
            return comp_stat
    return None

def fetch_summary(timeout: float = 8.0) -> Summary:
    """
    GitLab SaaS summary based on the public status homepage ONLY:
      1) If banner says 'All Systems Operational' -> green.
      2) Else, look at 'GitLab Pages' component and map its state.
      3) Else, conservative degraded result.

    Shape matches GitHub's summary keys.
    """
    html = _fetch_homepage(timeout)

    # 1) Banner check
    b = _banner_indicator_from_html(html)
    if b == "none":
        return {
            "status": {"indicator": "none", "description": "All Systems Operational"}
        }

    # 2) Component check (GitLab Pages)
    pages_status = _component_status_from_html(html, "GitLab Pages")
    if pages_status:
        pages_l = pages_status.strip().lower()
        ind = COMPONENT_MAP.get(pages_l)
        if ind is not None:
            desc = "GitLab Pages Operational" if ind == "none" else f"GitLab Pages: {pages_status}"
            return {
                "status": {"indicator": ind, "description": desc}
            }

    # 3) Conservative fallback if we couldn't parse specifics
    return {
        "status": {"indicator": "minor", "description": "Status page not green (no banner/Pages parse)"}
    }
