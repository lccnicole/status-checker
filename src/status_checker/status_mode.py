from __future__ import annotations
from typing import Tuple, Dict

STATUS_TO_CODE: Dict[str, int] = {
    "none": 0,
    "minor": 1,
    "major": 2,
    "critical": 2,
    "maintenance": 0,  # optional
}

def summarize(provider: str, indicator: str, description: str) -> Tuple[str, int]:
    code = STATUS_TO_CODE.get(indicator, 1)  # treat unknown as degraded
    text = f"{provider}: {indicator.upper()} – {description}"
    return text, code

