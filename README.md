# Status Checker

A simple CLI tool to check the official status of **GitHub** and **GitLab**.  
It fetches from each provider’s **status page** (JSON for GitHub, homepage banner for GitLab),  
and returns results in either table or JSON format.  

Supports exit codes so you can use it in CI/CD pipelines.

---

## Features

- **GitHub**: Uses [https://www.githubstatus.com/api/v2/summary.json](https://www.githubstatus.com/api/v2/summary.json).  
- **GitLab**: Scrapes the homepage banner at [status.gitlab.com](https://status.gitlab.com).  
  - Checks the top banner (`All Systems Operational` or current incident text).  
  - Normalizes results into the same schema as GitHub.  
- Output in **pretty table** or **JSON**.  
- Exit codes for automation:
  - `0` = Operational  
  - `1` = Minor/Degraded  
  - `2` = Major outage  
  - `3` = Unknown/error  

---

## Installation

Clone and install locally:

```bash
git clone https://github.com/yourname/status-checker.git
cd status-checker
python -m venv .venv
. .venv/bin/activate   # (or .venv\Scripts\activate on Windows)
pip install -e .
```

---

## Usage

```bash
# Default: check both providers, table output
status-checker --format table

# Only GitHub
status-checker --targets github --format table

# Only GitLab, in JSON
status-checker --targets gitlab --format json

# Adjust timeout
status-checker --timeout 10 --format table
```

### Example (table output)

```
Provider Status
┏━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Provider ┃ Indicator ┃ Description             ┃ Latency(ms) ┃ Source   ┃
┡━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ github   │ none      │ All Systems Operational │        1146 │ official │
│ gitlab   │ none      │ All Systems Operational │         679 │ official │
└──────────┴───────────┴─────────────────────────┴─────────────┴──────────┘
```

### Example (JSON output)

```json
[
  {
    "provider": "github",
    "indicator": "none",
    "description": "All Systems Operational",
    "latency_ms": 320,
    "source": "official"
  },
  {
    "provider": "gitlab",
    "indicator": "minor",
    "description": "Degraded performance",
    "latency_ms": 670,
    "source": "official"
  }
]
```

---

## Testing

Run unit tests with:

```bash
pytest -q
```

---

## Docker

Build and run via Docker:

```bash
docker build -t status-checker .
docker run --rm status-checker --format table
```

---

## Assumptions & Limitations

- **No “reachability” mode**  
  I considered adding direct `ping`/HTTP reachability probes to GitHub/GitLab endpoints.  
  However, I excluded this to keep the project focused on *official provider status* rather than raw connectivity,  
  which can be misleading (e.g., a local firewall could block you even if the provider is fully operational).  
  

- **GitLab status via homepage, not RSS**  
  GitLab provides an **RSS feed** of incidents/maintenance, but it’s less structured and not guaranteed to  
  reflect the current top-level status at all times. Instead, this project uses the **status.gitlab.com homepage banner**,  
  which always shows the same “All Systems Operational” or “Degraded/Major Outage” message users see on the status page.  
  This keeps results consistent with GitHub’s official JSON summary.  

- **Exit codes simplified**  
  Exit codes are normalized:
  - `0` = Operational  
  - `1` = Minor/Degraded  
  - `2` = Major outage  
  - `3` = Unknown/error  

- **Scope limited to official public pages**  
  No authentication or private project health checks are included.

