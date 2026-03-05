from unittest.mock import MagicMock
import pytest


def make_mock_project(path="group/repo", branch="main", archived=False, ns_kind="group"):
    p = MagicMock()
    p.path_with_namespace = path
    p.default_branch = branch
    p.archived = archived
    p.namespace = {"kind": ns_kind}
    return p


def make_mock_commit(committed_date, author_email="dev@example.com"):
    c = MagicMock()
    c.committed_date = committed_date
    c.author_email = author_email
    return c


@pytest.fixture
def mock_project():
    return make_mock_project()


@pytest.fixture
def project_factory():
    return make_mock_project


@pytest.fixture
def commit_factory():
    return make_mock_commit


@pytest.fixture
def mock_gl(mock_project):
    gl = MagicMock()
    gl.projects.list.return_value = [mock_project]
    return gl
