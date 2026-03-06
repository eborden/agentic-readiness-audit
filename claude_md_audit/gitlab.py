import re
import gitlab
import gitlab.exceptions
from datetime import datetime, timedelta, timezone

FILES_TO_CHECK = ["CLAUDE.md", "AGENTS.md"]
STALE_DAYS = 90

TEST_DIR_NAMES = {"tests", "test", "spec", "__tests__", "e2e", "integration", "specs"}
TEST_CONFIG_FILES = {"phpunit.xml", "phpunit.xml.dist"}
CI_CONFIG_FILES = {
    ".gitlab-ci.yml", "Jenkinsfile", ".travis.yml",
    "azure-pipelines.yml", ".circleci", ".github",
}
COVERAGE_CONFIG_FILES = {
    ".coveragerc", ".nycrc", ".nycrc.json", "jest.config.js", "jest.config.ts",
    "jest.config.mjs", "jest.config.cjs",
    "codecov.yml", ".codecov.yml", ".istanbul.yml", "sonar-project.properties",
}
_TEST_FILE_PATTERNS = [
    re.compile(r"^test_.+"),
    re.compile(r".+_test\.[^.]+$"),
    re.compile(r".+\.test\.[^.]+$"),
    re.compile(r".+\.spec\.[^.]+$"),
]


def _is_test_file(name: str) -> bool:
    return any(p.match(name) for p in _TEST_FILE_PATTERNS)


def _has_test_signals(entries: list) -> bool:
    for entry in entries:
        name = entry.get("name", "")
        etype = entry.get("type", "")
        if etype == "tree" and name in TEST_DIR_NAMES:
            return True
        if etype == "blob" and _is_test_file(name):
            return True
        if etype == "blob" and name in TEST_CONFIG_FILES:
            return True
    return False


def _has_ci_config(entries: list) -> bool:
    names = {e.get("name", "") for e in entries}
    return bool(names & CI_CONFIG_FILES)


def _has_coverage_config(entries: list) -> bool:
    names = {e.get("name", "") for e in entries}
    return bool(names & COVERAGE_CONFIG_FILES)


def get_test_maturity(project) -> str:
    """Return a test maturity tier: none | has_tests | automated | measured."""
    ref = project.default_branch or "main"

    try:
        root_entries = project.repository_tree(ref=ref)
    except gitlab.exceptions.GitlabGetError:
        return "none"

    has_tests = _has_test_signals(root_entries)

    if not has_tests:
        try:
            recursive_entries = project.repository_tree(
                ref=ref, recursive=True, per_page=500, get_all=False
            )
        except gitlab.exceptions.GitlabGetError:
            recursive_entries = []
        has_tests = _has_test_signals(recursive_entries)

    if not has_tests:
        return "none"

    has_ci = _has_ci_config(root_entries)
    if not has_ci:
        return "has_tests"

    # For .gitlab-ci.yml, verify a "test" keyword is present in the file
    root_names = {e.get("name", "") for e in root_entries}
    if ".gitlab-ci.yml" in root_names:
        try:
            ci_file = project.files.get(file_path=".gitlab-ci.yml", ref=ref)
            content = ci_file.decode()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
            if "test" not in content:
                return "has_tests"
        except gitlab.exceptions.GitlabGetError:
            return "has_tests"
    # For other CI configs, their presence is sufficient evidence of test automation

    if _has_coverage_config(root_entries):
        return "measured"

    # PHPUnit embeds coverage config inside phpunit.xml — check file content
    for phpunit_name in ("phpunit.xml", "phpunit.xml.dist"):
        if phpunit_name in root_names:
            try:
                pf = project.files.get(file_path=phpunit_name, ref=ref)
                content = pf.decode()
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="ignore")
                if "coverage" in content:
                    return "measured"
            except gitlab.exceptions.GitlabGetError:
                pass

    return "automated"


def check_files(project) -> dict[str, bool]:
    """Check which target files exist in the project's default branch root."""
    ref = project.default_branch or "main"
    result = {}
    for filename in FILES_TO_CHECK:
        try:
            project.files.get(file_path=filename, ref=ref)
            result[filename] = True
        except gitlab.exceptions.GitlabGetError:
            result[filename] = False
    return result


def get_activity_stats(project) -> dict:
    """Return commit activity stats for the project's default branch."""
    ref = project.default_branch or "main"
    now = datetime.now(timezone.utc)
    since_date = (now - timedelta(days=STALE_DAYS)).isoformat()

    try:
        recent = project.commits.list(ref_name=ref, per_page=1, get_all=False)
    except gitlab.exceptions.GitlabGetError:
        return {
            "last_commit_date": None,
            "days_since_last_commit": None,
            "recent_commit_count": 0,
            "unique_contributors_90d": 0,
            "is_stale": True,
        }

    if not recent:
        return {
            "last_commit_date": None,
            "days_since_last_commit": None,
            "recent_commit_count": 0,
            "unique_contributors_90d": 0,
            "is_stale": True,
        }

    last_commit = recent[0]
    last_date = datetime.fromisoformat(last_commit.committed_date)
    days_ago = (now - last_date).days

    try:
        window_commits = project.commits.list(ref_name=ref, since=since_date, all=True)
    except gitlab.exceptions.GitlabGetError:
        window_commits = []

    contributors = {c.author_email for c in window_commits}

    return {
        "last_commit_date": last_date.date().isoformat(),
        "days_since_last_commit": days_ago,
        "recent_commit_count": len(window_commits),
        "unique_contributors_90d": len(contributors),
        "is_stale": days_ago > STALE_DAYS,
    }
