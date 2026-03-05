import os
import pytest
import gitlab


@pytest.fixture(scope="session")
def live_gl():
    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        pytest.skip("GITLAB_TOKEN not set")
    return gitlab.Gitlab.from_config("nearpod")


@pytest.fixture(scope="session")
def live_project(live_gl):
    for p in live_gl.projects.list(per_page=10):
        if not p.archived and p.namespace["kind"] == "group":
            return p
    pytest.skip("No suitable live project found")
