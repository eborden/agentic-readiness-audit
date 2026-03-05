import pytest
from claude_md_audit.gitlab import check_files, get_activity_stats


@pytest.mark.integration
def test_check_files_live(live_project):
    result = check_files(live_project)
    assert "CLAUDE.md" in result
    assert "AGENTS.md" in result
    assert isinstance(result["CLAUDE.md"], bool)
    assert isinstance(result["AGENTS.md"], bool)


@pytest.mark.integration
def test_get_activity_stats_live(live_project):
    result = get_activity_stats(live_project)
    assert "last_commit_date" in result
    assert "days_since_last_commit" in result
    assert "recent_commit_count" in result
    assert "unique_contributors_90d" in result
    assert "is_stale" in result
    assert isinstance(result["is_stale"], bool)
    assert isinstance(result["recent_commit_count"], int)
    assert isinstance(result["unique_contributors_90d"], int)
