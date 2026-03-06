import gitlab.exceptions
from unittest.mock import MagicMock
import pytest

from claude_md_audit.gitlab import get_test_maturity


# ---------------------------------------------------------------------------
# Cycle 1 — none tier
# ---------------------------------------------------------------------------

def test_none_when_root_tree_empty(mock_project):
    mock_project.repository_tree.return_value = []
    assert get_test_maturity(mock_project) == "none"


# ---------------------------------------------------------------------------
# Cycle 2 — has_tests tier
# ---------------------------------------------------------------------------

def test_has_tests_when_test_dir_at_root_no_ci(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "tests", "type": "tree"},
    ]
    assert get_test_maturity(mock_project) == "has_tests"


def test_has_tests_when_spec_dir_at_root_no_ci(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "spec", "type": "tree"},
    ]
    assert get_test_maturity(mock_project) == "has_tests"


def test_has_tests_when_test_file_at_root_no_ci(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "test_main.py", "type": "blob"},
    ]
    assert get_test_maturity(mock_project) == "has_tests"


def test_has_tests_when_spec_file_at_root_no_ci(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "app.spec.js", "type": "blob"},
    ]
    assert get_test_maturity(mock_project) == "has_tests"


def test_has_tests_when_suffix_test_file_no_ci(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "main_test.go", "type": "blob"},
    ]
    assert get_test_maturity(mock_project) == "has_tests"


# ---------------------------------------------------------------------------
# Cycle 3 — fallback recursive scan
# ---------------------------------------------------------------------------

def test_has_tests_via_recursive_fallback(mock_project):
    def _tree(**kwargs):
        if kwargs.get("recursive"):
            return [{"name": "test_app.py", "type": "blob", "path": "src/test_app.py"}]
        return [{"name": "src", "type": "tree"}]
    mock_project.repository_tree.side_effect = _tree
    assert get_test_maturity(mock_project) == "has_tests"


def test_none_when_no_test_signals_recursive(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "src", "type": "tree"},
        {"name": "README.md", "type": "blob"},
    ]
    assert get_test_maturity(mock_project) == "none"


# ---------------------------------------------------------------------------
# Cycle 4 — automated tier
# ---------------------------------------------------------------------------

def test_automated_when_ci_contains_test_keyword(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "tests", "type": "tree"},
        {"name": ".gitlab-ci.yml", "type": "blob"},
    ]
    ci_file = MagicMock()
    ci_file.decode.return_value = b"stages:\n  - test\n"
    mock_project.files.get.return_value = ci_file
    assert get_test_maturity(mock_project) == "automated"


def test_has_tests_when_ci_lacks_test_keyword(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "tests", "type": "tree"},
        {"name": ".gitlab-ci.yml", "type": "blob"},
    ]
    ci_file = MagicMock()
    ci_file.decode.return_value = b"stages:\n  - build\n  - deploy\n"
    mock_project.files.get.return_value = ci_file
    assert get_test_maturity(mock_project) == "has_tests"


def test_automated_when_non_gitlab_ci_present(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "tests", "type": "tree"},
        {"name": "Jenkinsfile", "type": "blob"},
    ]
    assert get_test_maturity(mock_project) == "automated"


# ---------------------------------------------------------------------------
# Cycle 5 — measured tier
# ---------------------------------------------------------------------------

def test_measured_when_coverage_config_present(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "tests", "type": "tree"},
        {"name": ".gitlab-ci.yml", "type": "blob"},
        {"name": ".coveragerc", "type": "blob"},
    ]
    ci_file = MagicMock()
    ci_file.decode.return_value = b"stages:\n  - test\n"
    mock_project.files.get.return_value = ci_file
    assert get_test_maturity(mock_project) == "measured"


def test_measured_when_jest_config_present(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "__tests__", "type": "tree"},
        {"name": "Jenkinsfile", "type": "blob"},
        {"name": "jest.config.js", "type": "blob"},
    ]
    assert get_test_maturity(mock_project) == "measured"


# ---------------------------------------------------------------------------
# Cycle 6 — error handling
# ---------------------------------------------------------------------------

def test_graceful_on_api_error(mock_project):
    mock_project.repository_tree.side_effect = gitlab.exceptions.GitlabGetError("err", 500)
    assert get_test_maturity(mock_project) == "none"


# ---------------------------------------------------------------------------
# Cycle A — phpunit.xml as test presence signal
# ---------------------------------------------------------------------------

def test_has_tests_when_phpunit_xml_at_root_no_ci(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "phpunit.xml", "type": "blob"},
    ]
    assert get_test_maturity(mock_project) == "has_tests"


# ---------------------------------------------------------------------------
# Cycle B — phpunit.xml.dist also detected
# ---------------------------------------------------------------------------

def test_has_tests_when_phpunit_xml_dist_at_root_no_ci(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "phpunit.xml.dist", "type": "blob"},
    ]
    assert get_test_maturity(mock_project) == "has_tests"


# ---------------------------------------------------------------------------
# Cycle C — phpunit.xml with coverage keyword → measured
# ---------------------------------------------------------------------------

def test_measured_when_phpunit_xml_has_coverage(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "phpunit.xml", "type": "blob"},
        {"name": ".gitlab-ci.yml", "type": "blob"},
    ]
    ci_file = MagicMock()
    ci_file.decode.return_value = b"stages:\n  - test\n"
    phpunit_file = MagicMock()
    phpunit_file.decode.return_value = b'<coverage processUncoveredFiles="true">'
    def _files_get(file_path, ref):
        if file_path == ".gitlab-ci.yml":
            return ci_file
        return phpunit_file
    mock_project.files.get.side_effect = _files_get
    assert get_test_maturity(mock_project) == "measured"


# ---------------------------------------------------------------------------
# Cycle D — phpunit.xml without coverage keyword stays automated
# ---------------------------------------------------------------------------

def test_automated_when_phpunit_xml_lacks_coverage(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "phpunit.xml", "type": "blob"},
        {"name": ".gitlab-ci.yml", "type": "blob"},
    ]
    ci_file = MagicMock()
    ci_file.decode.return_value = b"stages:\n  - test\n"
    phpunit_file = MagicMock()
    phpunit_file.decode.return_value = b'<phpunit><testsuites/></phpunit>'
    def _files_get(file_path, ref):
        if file_path == ".gitlab-ci.yml":
            return ci_file
        return phpunit_file
    mock_project.files.get.side_effect = _files_get
    assert get_test_maturity(mock_project) == "automated"


# ---------------------------------------------------------------------------
# Cycle E — jest.config.mjs detected as coverage config
# ---------------------------------------------------------------------------

def test_measured_when_jest_config_mjs_present(mock_project):
    mock_project.repository_tree.return_value = [
        {"name": "__tests__", "type": "tree"},
        {"name": "Jenkinsfile", "type": "blob"},
        {"name": "jest.config.mjs", "type": "blob"},
    ]
    assert get_test_maturity(mock_project) == "measured"
