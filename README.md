# agentic-readiness-audit

Scans all GitLab group projects for `CLAUDE.md` / `AGENTS.md` presence and test maturity, writes a CSV report, and prints a bucketed summary.

## Quick start

```bash
# Requires a .python-gitlab.cfg with a [nearpod] section
python main.py
```

Output: `agentic_readiness_audit.csv` + console summary.

## Tests

```bash
uv pip install -e ".[test]"
pytest tests/unit/ -v
```
