# claude-md-audit

Scans all GitLab group projects for `CLAUDE.md` / `AGENTS.md` presence, writes a CSV report, and prints a bucketed summary.

## Project structure

```
main.py                        # Entry point; orchestrates project iteration and CSV output
claude_md_audit/
  argparse.py                  # CLI argument parser (build_parser / parse_args)
  env.py                       # Environment variables (LOG_LEVEL)
  gitlab.py                    # check_files(), get_activity_stats() — pure project logic
  logging.py                   # Logging setup (log-with-context)
  logging_cli_formatter.py     # Custom CLI log formatter
  summary.py                   # print_summary(), _truthy() — console report
tests/
  conftest.py                  # Shared fixtures: mock_project, project_factory, commit_factory, mock_gl
  unit/                        # Fast, no-credentials tests
  integration/                 # Live API tests, skipped without GITLAB_TOKEN
```

## Running

```bash
# Requires a .python-gitlab.cfg with a [nearpod] section
python main.py
```

Output: `claude_md_audit.csv` + console summary.

Environment variables:
- `LOG_LEVEL` — log verbosity (default: `INFO`)

## Tests

```bash
# Install test deps (one-time)
uv pip install -e ".[test]"

# Unit tests — no credentials needed
pytest tests/unit/ -v

# Integration tests — requires GITLAB_TOKEN + .python-gitlab.cfg
GITLAB_TOKEN=<token> pytest tests/integration/ -v -m integration
```

## Key design notes

- `main(gl=None)` accepts an injected GL client so unit tests can pass a mock without touching the network.
- `check_files` and `get_activity_stats` in `gitlab.py` take plain project objects — easy to mock with `MagicMock`.
- `print_summary` is a pure function over a list of dicts — also trivially testable.
- `_truthy()` in `summary.py` coerces CSV-round-tripped booleans (`"True"/"False"` strings) back to `bool`.
- Stale threshold is 90 days (`STALE_DAYS` in `gitlab.py`).

## Docker

```bash
docker build -t claude-md-audit .
docker run --rm -v ~/.python-gitlab.cfg:/root/.python-gitlab.cfg claude-md-audit
```
