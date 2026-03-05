import gitlab
import gitlab.exceptions
from datetime import datetime, timedelta, timezone

FILES_TO_CHECK = ["CLAUDE.md", "AGENTS.md"]
STALE_DAYS = 90


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
