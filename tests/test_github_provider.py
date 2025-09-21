import json
import types
import httpx
import pytest

from status_checker.providers import github as gh

class DummyResp:
    def __init__(self, json_obj, status_code=200):
        self._json = json_obj
        self.status_code = status_code
        self.text = json.dumps(json_obj)
    def json(self): return self._json
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=None)

def test_github_fetch_summary_ok(monkeypatch):
    data = {"status": {"indicator": "none", "description": "All Systems Operational"}}

    class DummyClient:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def get(self, url): return DummyResp(data, 200)

    monkeypatch.setattr(gh.httpx, "Client", DummyClient)

    out = gh.fetch_summary(timeout=1.0)
    assert out["status"]["indicator"] == "none"
    assert "Operational" in out["status"]["description"]
