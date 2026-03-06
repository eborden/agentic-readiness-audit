# claude-md-audit

Scans all GitLab group projects for `CLAUDE.md` / `AGENTS.md` presence, writes a CSV report, and prints a bucketed summary.

## Project structure

```
main.py                        # Entry point; orchestrates project iteration and CSV output
claude_md_audit/
  argparse.py                  # CLI argument parser (build_parser / parse_args)
  env.py                       # Environment variables (LOG_LEVEL)
  gitlab.py                    # check_files(), get_activity_stats(), get_test_maturity() — pure project logic
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
- `check_files`, `get_activity_stats`, and `get_test_maturity` in `gitlab.py` take plain project objects — easy to mock with `MagicMock`.
- `print_summary` is a pure function over a list of dicts — also trivially testable.
- `_truthy()` in `summary.py` coerces CSV-round-tripped booleans (`"True"/"False"` strings) back to `bool`.
- Stale threshold is 90 days (`STALE_DAYS` in `gitlab.py`).

## Test maturity detection

`get_test_maturity()` classifies each repo into a tier: `none` → `has_tests` → `automated` → `measured`.

**Tier logic:**
1. **none** — no test directories, test files, or test framework configs found (checks root, then recursive fallback).
2. **has_tests** — test signals found but no CI config, or `.gitlab-ci.yml` lacks a `"test"` keyword.
3. **automated** — test signals + CI config confirmed (non-GitLab CI configs like `Jenkinsfile` need only exist).
4. **measured** — automated + coverage configuration detected.

**Detection constants** (all in `gitlab.py`):
- `TEST_DIR_NAMES` — directory names that signal test presence (`tests`, `spec`, `__tests__`, etc.).
- `TEST_CONFIG_FILES` — framework configs that signal test presence (`phpunit.xml`, `phpunit.xml.dist`).
- `_TEST_FILE_PATTERNS` — regex patterns for test files (`test_*.py`, `*.spec.js`, etc.).
- `CI_CONFIG_FILES` — CI system configs (`.gitlab-ci.yml`, `Jenkinsfile`, `.travis.yml`, etc.).
- `COVERAGE_CONFIG_FILES` — coverage tool configs (`.coveragerc`, `jest.config.{js,ts,mjs,cjs}`, `codecov.yml`, etc.).

**PHP-specific:** PHPUnit embeds coverage config inside `phpunit.xml` rather than a separate file. When the repo reaches the `automated` tier, `phpunit.xml`/`phpunit.xml.dist` content is fetched and checked for a `"coverage"` substring to promote to `measured`.

## Docker

```bash
docker build -t claude-md-audit .
docker run --rm -v ~/.python-gitlab.cfg:/root/.python-gitlab.cfg claude-md-audit
```
