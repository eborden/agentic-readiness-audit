import csv
import pytest
from unittest.mock import MagicMock, patch

import main as main_module
from main import main, FIELDNAMES
from tests.conftest import make_mock_project, make_mock_commit


def _file_status(has_claude=False, has_agents=False):
    return {"CLAUDE.md": has_claude, "AGENTS.md": has_agents}


def _activity(stale=False, days=10, count=5, contributors=2, date="2026-02-20"):
    return {
        "last_commit_date": date,
        "days_since_last_commit": days,
        "recent_commit_count": count,
        "unique_contributors_90d": contributors,
        "is_stale": stale,
    }


def _make_gl(*projects):
    gl = MagicMock()
    gl.projects.list.return_value = list(projects)
    return gl


def test_archived_project_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_FILE", str(tmp_path / "out.csv"))
    archived = make_mock_project(path="group/archived", archived=True)
    gl = _make_gl(archived)

    with patch("main.check_files") as mock_check, \
         patch("main.get_activity_stats") as mock_stats, \
         patch("main.print_summary"), \
         patch("main.parse_args"), \
         patch("main.setup_logging"):
        main(gl=gl)
        mock_check.assert_not_called()
        mock_stats.assert_not_called()


def test_user_namespace_project_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_FILE", str(tmp_path / "out.csv"))
    user_proj = make_mock_project(path="user/personal", ns_kind="user")
    gl = _make_gl(user_proj)

    with patch("main.check_files") as mock_check, \
         patch("main.get_activity_stats") as mock_stats, \
         patch("main.print_summary"), \
         patch("main.parse_args"), \
         patch("main.setup_logging"):
        main(gl=gl)
        mock_check.assert_not_called()
        mock_stats.assert_not_called()


def test_group_project_produces_row(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_FILE", str(tmp_path / "out.csv"))
    proj = make_mock_project(path="group/repo", branch="main")
    gl = _make_gl(proj)

    with patch("main.check_files", return_value=_file_status(has_claude=True)) as mock_check, \
         patch("main.get_activity_stats", return_value=_activity()) as mock_stats, \
         patch("main.print_summary") as mock_summary, \
         patch("main.parse_args"), \
         patch("main.setup_logging"):
        main(gl=gl)
        mock_check.assert_called_once_with(proj)
        mock_stats.assert_called_once_with(proj)
        rows = mock_summary.call_args[0][0]
        assert len(rows) == 1
        assert rows[0]["project_path"] == "group/repo"
        assert rows[0]["has_claude_md"] is True


def test_csv_written_with_correct_headers_and_row(tmp_path, monkeypatch):
    out_file = tmp_path / "out.csv"
    monkeypatch.setattr(main_module, "OUTPUT_FILE", str(out_file))
    proj = make_mock_project(path="group/myrepo", branch="develop")
    gl = _make_gl(proj)

    with patch("main.check_files", return_value=_file_status(has_claude=True, has_agents=False)), \
         patch("main.get_activity_stats", return_value=_activity(days=7, count=3)), \
         patch("main.print_summary"), \
         patch("main.parse_args"), \
         patch("main.setup_logging"):
        main(gl=gl)

    with open(out_file, newline="") as f:
        reader = csv.DictReader(f)
        written_rows = list(reader)

    assert reader.fieldnames == FIELDNAMES
    assert len(written_rows) == 1
    assert written_rows[0]["project_path"] == "group/myrepo"
    assert written_rows[0]["default_branch"] == "develop"
    assert written_rows[0]["has_claude_md"] == "True"
    assert written_rows[0]["days_since_last_commit"] == "7"


def test_mixed_projects_two_rows(tmp_path, monkeypatch):
    out_file = tmp_path / "out.csv"
    monkeypatch.setattr(main_module, "OUTPUT_FILE", str(out_file))
    group1 = make_mock_project(path="group/a")
    group2 = make_mock_project(path="group/b")
    archived = make_mock_project(path="group/archived", archived=True)
    user = make_mock_project(path="user/personal", ns_kind="user")
    gl = _make_gl(group1, group2, archived, user)

    with patch("main.check_files", return_value=_file_status()), \
         patch("main.get_activity_stats", return_value=_activity()), \
         patch("main.print_summary"), \
         patch("main.parse_args"), \
         patch("main.setup_logging"):
        main(gl=gl)

    with open(out_file, newline="") as f:
        written_rows = list(csv.DictReader(f))

    assert len(written_rows) == 2
    paths = {r["project_path"] for r in written_rows}
    assert paths == {"group/a", "group/b"}
