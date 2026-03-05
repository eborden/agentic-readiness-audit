import csv
import gitlab
from claude_md_audit.argparse import parse_args
from claude_md_audit.gitlab import check_files, get_activity_stats
from claude_md_audit.logging import setup_logging
from claude_md_audit.summary import print_summary

OUTPUT_FILE = "claude_md_audit.csv"
FIELDNAMES = [
    "project_path",
    "default_branch",
    "has_claude_md",
    "has_agents_md",
    "has_either",
    "last_commit_date",
    "days_since_last_commit",
    "recent_commit_count",
    "unique_contributors_90d",
    "is_stale",
]


def main(gl=None):
    parse_args()
    setup_logging("main")

    if gl is None:
        gl = gitlab.Gitlab.from_config("nearpod")
    rows = []

    for project in gl.projects.list(all=True):
        if project.archived or project.namespace["kind"] == "user":
            continue

        file_status = check_files(project)
        activity = get_activity_stats(project)
        rows.append({
            "project_path": project.path_with_namespace,
            "default_branch": project.default_branch or "main",
            "has_claude_md": file_status["CLAUDE.md"],
            "has_agents_md": file_status["AGENTS.md"],
            "has_either": file_status["CLAUDE.md"] or file_status["AGENTS.md"],
            **activity,
        })

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print_summary(rows)


if __name__ == "__main__":
    main()
