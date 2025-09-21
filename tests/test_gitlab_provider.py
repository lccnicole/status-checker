import httpx
import pytest
from status_checker.providers import gitlab as gls

HOMEPAGE_GREEN = """
<html><body>
  <h1>All Systems Operational</h1>
  <ul class="components">
    <li><span class="name">GitLab Pages</span>
        <span class="component-status">Operational</span></li>
  </ul>
</body></html>
"""

HOMEPAGE_PAGES_DEGRADED = """
<html><body>
  <h1>Status</h1>
  <ul class="components">
    <li><span class="name">GitLab Pages</span>
        <span class="component-status">Degraded Performance</span></li>
  </ul>
</body></html>
"""

class DummyResp:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=None)

class DummyClient:
    def __init__(self, responses):
        self._responses = responses
        self._i = 0
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def get(self, url):
        # return next queued response
        resp = self._responses[self._i]
        self._i += 1
        return resp

def test_gitlab_homepage_green(monkeypatch):
    # Our provider only uses homepage in the latest simplified version
    def fake_client(*a, **kw):
        return DummyClient([DummyResp(HOMEPAGE_GREEN)])
    monkeypatch.setattr(gls.httpx, "Client", fake_client)

    out = gls.fetch_summary(timeout=1.0)
    assert out["status"]["indicator"] == "none"
    assert out["status"]["description"] == "All Systems Operational"

def test_gitlab_pages_degraded(monkeypatch):
    def fake_client(*a, **kw):
        return DummyClient([DummyResp(HOMEPAGE_PAGES_DEGRADED)])
    monkeypatch.setattr(gls.httpx, "Client", fake_client)

    out = gls.fetch_summary(timeout=1.0)
    assert out["status"]["indicator"] == "minor"
    assert "GitLab Pages" in out["status"]["description"]
