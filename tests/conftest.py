import os
import pytest


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "compose.yaml")


# Pin the project name to avoid creating multiple stacks
@pytest.fixture(scope="session")
def docker_compose_project_name() -> str:
    return "my-compose-project"


# Stop the stack before starting a new one
@pytest.fixture(scope="session")
def docker_setup_command():
    return ["down -v", "up --build -d"]