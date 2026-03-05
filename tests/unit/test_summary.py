import pytest
from claude_md_audit.summary import print_summary, _truthy


# ---------------------------------------------------------------------------
# _truthy
# ---------------------------------------------------------------------------

def test_truthy_bool_true():
    assert _truthy(True) is True


def test_truthy_bool_false():
    assert _truthy(False) is False


def test_truthy_string_true():
    assert _truthy("true") is True


def test_truthy_string_false():
    assert _truthy("false") is False


def test_truthy_string_true_capitalized():
    assert _truthy("True") is True


def test_truthy_string_true_with_whitespace():
    assert _truthy("  True  ") is True


def test_truthy_string_false_mixed_case():
    assert _truthy("FALSE") is False


# ---------------------------------------------------------------------------
# print_summary — bucket counts
# ---------------------------------------------------------------------------

def _row(path, has_either, is_stale, recent_commit_count=5, days=10, authors=2):
    return {
        "project_path": path,
        "has_either": has_either,
        "is_stale": is_stale,
        "recent_commit_count": recent_commit_count,
        "days_since_last_commit": days,
        "unique_contributors_90d": authors,
    }


def test_print_summary_empty(capsys):
    print_summary([])
    out = capsys.readouterr().out
    assert "0" in out
    assert "Top 20" not in out


def test_print_summary_all_healthy(capsys):
    rows = [_row(f"group/repo{i}", has_either=True, is_stale=False) for i in range(3)]
    print_summary(rows)
    out = capsys.readouterr().out
    assert "3" in out
    assert "Top 20" not in out


def test_print_summary_all_needs_grooming(capsys):
    rows = [_row(f"group/repo{i}", has_either=False, is_stale=False) for i in range(4)]
    print_summary(rows)
    out = capsys.readouterr().out
    assert "4" in out
    assert "Top 20" in out


def test_print_summary_all_artifact(capsys):
    rows = [_row(f"group/repo{i}", has_either=True, is_stale=True) for i in range(2)]
    print_summary(rows)
    out = capsys.readouterr().out
    assert "2" in out


def test_print_summary_all_legacy(capsys):
    rows = [_row(f"group/repo{i}", has_either=False, is_stale=True) for i in range(5)]
    print_summary(rows)
    out = capsys.readouterr().out
    assert "5" in out
    assert "Top 20" not in out


def test_print_summary_mixed_buckets(capsys):
    rows = [
        _row("a/healthy", has_either=True, is_stale=False),
        _row("a/grooming", has_either=False, is_stale=False, recent_commit_count=10),
        _row("a/artifact", has_either=True, is_stale=True),
        _row("a/legacy", has_either=False, is_stale=True),
    ]
    print_summary(rows)
    out = capsys.readouterr().out
    assert "a/grooming" in out


# ---------------------------------------------------------------------------
# print_summary — top-20 ranking
# ---------------------------------------------------------------------------

def test_print_summary_top20_sorted_by_recent_commits(capsys):
    rows = [
        _row("group/low", has_either=False, is_stale=False, recent_commit_count=1, days=5),
        _row("group/high", has_either=False, is_stale=False, recent_commit_count=100, days=5),
        _row("group/mid", has_either=False, is_stale=False, recent_commit_count=50, days=5),
    ]
    print_summary(rows)
    out = capsys.readouterr().out
    # high should appear before mid, which appears before low
    assert out.index("group/high") < out.index("group/mid")
    assert out.index("group/mid") < out.index("group/low")


def test_print_summary_top20_capped_at_20(capsys):
    rows = [
        _row(f"group/repo{i:02d}", has_either=False, is_stale=False, recent_commit_count=i, days=5)
        for i in range(25)
    ]
    print_summary(rows)
    out = capsys.readouterr().out
    # repo24 (highest) should appear, repo00 (lowest, rank 25) should not
    assert "group/repo24" in out
    assert "group/repo00" not in out


def test_print_summary_excludes_none_days(capsys):
    rows = [
        _row("group/has-days", has_either=False, is_stale=False, recent_commit_count=99, days=5),
        {
            "project_path": "group/no-days",
            "has_either": False,
            "is_stale": False,
            "recent_commit_count": 999,
            "days_since_last_commit": None,
            "unique_contributors_90d": 1,
        },
    ]
    print_summary(rows)
    out = capsys.readouterr().out
    assert "group/has-days" in out
    assert "group/no-days" not in out


def test_print_summary_excludes_empty_string_days(capsys):
    rows = [
        {
            "project_path": "group/empty-days",
            "has_either": False,
            "is_stale": False,
            "recent_commit_count": 999,
            "days_since_last_commit": "",
            "unique_contributors_90d": 1,
        },
    ]
    print_summary(rows)
    out = capsys.readouterr().out
    assert "group/empty-days" not in out
