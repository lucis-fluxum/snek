import json
import os

import pytest


def load_fixture(filename):
    with open(os.path.join(os.path.dirname(__file__), 'fixtures', filename), 'r') as f:
        return f.read()


def mock_repository_json(mocker):
    mocker.patch('snek.repository.Repository.get_package_info',
                 side_effect=lambda name, version=None: json.loads(load_fixture(f"json/pypi_{name.lower()}.json")))


@pytest.fixture
def pypi_flask_json():
    return json.loads(load_fixture('pypi_flask.json'))
