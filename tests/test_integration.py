import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import link_app.app
from pytest_mock import MockerFixture
import pytest
import datetime
import requests
import jwt
pytest_plugins = ('pytest_asyncio')


def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture(scope="session")
def http_service(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("web", 8000)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=120.0, pause=1, check=lambda: is_responsive(url + '/docs')
    )
    return url


@pytest.mark.long
def test_url_register_user(http_service):
    status = 200
    response = requests.post(http_service + "/auth/register", json={'login': 'test_url_register_user', 'password': '1234'})

    assert response.status_code == status
    assert response.json()['token'] is not None


@pytest.mark.long
def test_url_login_user(http_service):

    status = 200
    response = requests.post(http_service + "/auth/register", json={'login': 'test_url_login_user', 'password': '1234'})

    response = requests.post(http_service + "/auth/login", json={'login': 'test_url_login_user', 'password': '1234'})

    assert response.status_code == status
    assert response.json()['token'] is not None
