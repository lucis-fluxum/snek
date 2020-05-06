import json
import os


def load_fixture(filename):
    with open(os.path.join(os.path.dirname(__file__), 'fixtures', filename), 'r') as f:
        return f.read()


def mock_repository_json(mocker):
    mocker.patch('snek.repository.Repository.get_package_info',
                 side_effect=lambda name, version=None: json.loads(load_fixture(f"pypi/pypi_{name.lower()}.json")))
