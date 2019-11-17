import json
import os

import pytest


def load_fixture(filename):
    with open(os.path.join(os.path.dirname(__file__), 'fixtures', filename), 'r') as f:
        return f.read()


def mock_requests_json(mocker, json):
    return mocker.patch('snek.resolver.requests.get', return_value=mocker.Mock(**{'json.return_value': json}))


@pytest.fixture
def pypi_flask_json():
    return json.loads(load_fixture('pypi_Flask.json'))
