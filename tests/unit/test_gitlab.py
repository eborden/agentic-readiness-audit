import pytest
from freezegun import freeze_time
from unittest.mock import MagicMock
import gitlab.exceptions

from agentic_readiness_audit.gitlab import check_files, get_activity_stats


# ---------------------------------------------------------------------------
# check_files
# ---------------------------------------------------------------------------

def test_check_files_found(mock_project):
    mock_project.files.get.return_value = MagicMock()
    result = check_files(mock_project)
    assert result["CLAUDE.md"] is True
    assert result["AGENTS.md"] is True


def test_check_files_missing(mock_project):
    mock_project.files.get.side_effect = gitlab.exceptions.GitlabGetError("not found", 404)
    result = check_files(mock_project)
    assert result["CLAUDE.md"] is False
    assert result["AGENTS.md"] is False


def test_check_files_mixed(mock_project):
    def _get(file_path, ref):
        if file_path == "CLAUDE.md":
            return MagicMock()
        raise gitlab.exceptions.GitlabGetError("not found", 404)

    mock_project.files.get.side_effect = _get
    result = check_files(mock_project)
    assert result["CLAUDE.md"] is True
    assert result["AGENTS.md"] is False


def test_check_files_none_branch_falls_back_to_main(mock_project):
    mock_project.default_branch = None
    mock_project.files.get.return_value = MagicMock()
    check_files(mock_project)
    # Verify "main" was used as ref
    calls = mock_project.files.get.call_args_list
    for call in calls:
        assert call.kwargs.get("ref") == "main" or call[1].get("ref") == "main"


# ---------------------------------------------------------------------------
# get_activity_stats
# ---------------------------------------------------------------------------

@freeze_time("2026-03-05T00:00:00Z")
def test_get_activity_stats_commits_list_error(mock_project):
    mock_project.commits.list.side_effect = gitlab.exceptions.GitlabGetError("error", 500)
    result = get_activity_stats(mock_project)
    assert result["last_commit_date"] is None
    assert result["days_since_last_commit"] is None
    assert result["recent_commit_count"] == 0
    assert result["unique_contributors_90d"] == 0
    assert result["is_stale"] is True


@freeze_time("2026-03-05T00:00:00Z")
def test_get_activity_stats_empty_commits(mock_project):
    mock_project.commits.list.return_value = []
    result = get_activity_stats(mock_project)
    assert result["last_commit_date"] is None
    assert result["days_since_last_commit"] is None
    assert result["recent_commit_count"] == 0
    assert result["unique_contributors_90d"] == 0
    assert result["is_stale"] is True


@freeze_time("2026-03-05T00:00:00Z")
def test_get_activity_stats_recent_commit_not_stale(mock_project, commit_factory):
    recent_commit = commit_factory("2026-02-20T12:00:00+00:00", "alice@example.com")
    window_commit = commit_factory("2026-02-20T12:00:00+00:00", "alice@example.com")

    def _list(**kwargs):
        if kwargs.get("per_page") == 1:
            return [recent_commit]
        return [window_commit]

    mock_project.commits.list.side_effect = _list
    result = get_activity_stats(mock_project)
    assert result["is_stale"] is False
    assert result["days_since_last_commit"] == 12  # 2026-03-05 00:00 minus 2026-02-20 12:00 = 12.5 → 12
    assert result["last_commit_date"] == "2026-02-20"


@freeze_time("2026-03-05T00:00:00Z")
def test_get_activity_stats_old_commit_stale(mock_project, commit_factory):
    old_commit = commit_factory("2025-11-01T00:00:00+00:00", "dev@example.com")

    def _list(**kwargs):
        if kwargs.get("per_page") == 1:
            return [old_commit]
        return []

    mock_project.commits.list.side_effect = _list
    result = get_activity_stats(mock_project)
    assert result["is_stale"] is True
    assert result["days_since_last_commit"] > 90


@freeze_time("2026-03-05T00:00:00Z")
def test_get_activity_stats_unique_contributors(mock_project, commit_factory):
    recent_commit = commit_factory("2026-02-20T12:00:00+00:00", "alice@example.com")
    c1 = commit_factory("2026-02-20T12:00:00+00:00", "alice@example.com")
    c2 = commit_factory("2026-02-21T12:00:00+00:00", "bob@example.com")
    c3 = commit_factory("2026-02-22T12:00:00+00:00", "charlie@example.com")

    def _list(**kwargs):
        if kwargs.get("per_page") == 1:
            return [recent_commit]
        return [c1, c2, c3]

    mock_project.commits.list.side_effect = _list
    result = get_activity_stats(mock_project)
    assert result["unique_contributors_90d"] == 3
    assert result["recent_commit_count"] == 3


@freeze_time("2026-03-05T00:00:00Z")
def test_get_activity_stats_deduplicates_contributors(mock_project, commit_factory):
    recent_commit = commit_factory("2026-02-20T12:00:00+00:00", "alice@example.com")
    c1 = commit_factory("2026-02-20T12:00:00+00:00", "alice@example.com")
    c2 = commit_factory("2026-02-21T12:00:00+00:00", "alice@example.com")

    def _list(**kwargs):
        if kwargs.get("per_page") == 1:
            return [recent_commit]
        return [c1, c2]

    mock_project.commits.list.side_effect = _list
    result = get_activity_stats(mock_project)
    assert result["unique_contributors_90d"] == 1
    assert result["recent_commit_count"] == 2


@freeze_time("2026-03-05T00:00:00Z")
def test_get_activity_stats_window_error_falls_back(mock_project, commit_factory):
    recent_commit = commit_factory("2026-02-20T12:00:00+00:00", "alice@example.com")

    call_count = [0]

    def _list(**kwargs):
        call_count[0] += 1
        if kwargs.get("per_page") == 1:
            return [recent_commit]
        raise gitlab.exceptions.GitlabGetError("error", 500)

    mock_project.commits.list.side_effect = _list
    result = get_activity_stats(mock_project)
    assert result["last_commit_date"] == "2026-02-20"
    assert result["recent_commit_count"] == 0
    assert result["unique_contributors_90d"] == 0


@freeze_time("2026-03-05T00:00:00Z")
def test_get_activity_stats_none_branch_falls_back_to_main(mock_project, commit_factory):
    mock_project.default_branch = None
    recent_commit = commit_factory("2026-02-20T12:00:00+00:00", "alice@example.com")

    def _list(**kwargs):
        if kwargs.get("per_page") == 1:
            return [recent_commit]
        return []

    mock_project.commits.list.side_effect = _list
    result = get_activity_stats(mock_project)
    # Should not raise; verify ref_name="main" was used in the first call
    first_call_kwargs = mock_project.commits.list.call_args_list[0][1]
    assert first_call_kwargs.get("ref_name") == "main"
