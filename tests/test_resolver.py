import json
import sys

import pytest
from packaging.markers import Marker
from packaging.requirements import Requirement

from snek.resolver import Resolver
from tests.conftest import load_fixture

FLASK_REQUIREMENTS = {'Werkzeug>=0.15', 'Jinja2>=2.10.1', 'itsdangerous>=0.24', 'click>=5.1'}
FLASK_DEV_REQUIREMENTS = FLASK_REQUIREMENTS.union({'pytest; extra == "dev"', 'coverage; extra == "dev"',
                                                   'tox; extra == "dev"',
                                                   'sphinx; extra == "dev"', 'pallets-sphinx-themes; extra == "dev"',
                                                   'sphinxcontrib-log-cabinet; extra == "dev"',
                                                   'sphinx-issues; extra == "dev"'})
FLASK_DOCS_REQUIREMENTS = FLASK_REQUIREMENTS.union({'sphinx; extra == "docs"', 'pallets-sphinx-themes; extra == "docs"',
                                                    'sphinxcontrib-log-cabinet; extra == "docs"',
                                                    'sphinx-issues; extra == "docs"'})
FLASK_ALL_REQUIREMENTS = FLASK_REQUIREMENTS.union(FLASK_DEV_REQUIREMENTS).union(FLASK_DOCS_REQUIREMENTS)


def mock_fetch_requirement(mocker):
    mocker.patch('snek.resolver.Resolver.fetch_metadata',
                 side_effect=lambda name: json.loads(load_fixture(f"json/pypi_{name}.json")))


class TestResolver:
    @pytest.mark.parametrize('req_str, extras, expected_reqs',
                             [('Flask', {}, FLASK_REQUIREMENTS),
                              ('Flask[dev]', {'dev'}, FLASK_DEV_REQUIREMENTS),
                              ('Flask[docs]', {'docs'}, FLASK_DOCS_REQUIREMENTS),
                              ('Flask[dev, docs]', {'dev', 'docs'}, FLASK_ALL_REQUIREMENTS)])
    def test_get_sub_requirements(self, mocker, req_str, extras, expected_reqs):
        mock_fetch_requirement(mocker)
        resolver = Resolver(extras=extras)
        requirements = map(str, resolver.get_sub_requirements(Requirement(req_str)))
        assert set(requirements) == expected_reqs

    def test_evaluate_extra(self):
        resolver_no_extra = Resolver()
        assert not resolver_no_extra.evaluate_marker(Marker("extra == 'dev'"))
        resolver_one_extra = Resolver(extras={'dev'})
        assert resolver_one_extra.evaluate_marker(Marker("extra == 'dev'"))
        assert not resolver_one_extra.evaluate_marker(Marker("extra == 'another'"))
        resolver_multi_extra = Resolver(extras={'dev', 'test', 'another'})
        for extra in ['dev', 'test', 'another']:
            assert resolver_multi_extra.evaluate_marker(Marker(f"extra == '{extra}'"))

    def test_evaluate_marker(self):
        resolver = Resolver()
        assert resolver.evaluate_marker(None)
        windows_marker = Marker('sys_platform=="win32"')
        if sys.platform == 'win32':
            assert resolver.evaluate_marker(windows_marker)
        else:
            assert not resolver.evaluate_marker(windows_marker)

    def test_get_compatible_versions(self, mocker):
        mock_fetch_requirement(mocker)
        resolver = Resolver()
        assert len(resolver.get_compatible_versions(Requirement('Flask'))) == 32
        assert len(resolver.get_compatible_versions(Requirement('Flask'),
                                                    Requirement('Flask > 1.0'))) == 6
        assert len(resolver.get_compatible_versions(Requirement('Flask'),
                                                    Requirement('Flask > 1.0'),
                                                    Requirement('Flask <= 1.1'))) == 5
        assert len(resolver.get_compatible_versions(Requirement('Flask'),
                                                    Requirement('Flask ~= 1.0'))) == 7
        assert len(resolver.get_compatible_versions(Requirement('Flask > 1'),
                                                    Requirement('Flask < 1'))) == 0

    def test_dont_add_existing_requirement(self):
        resolver = Resolver(dependencies=[Requirement('Flask')])
        assert len(resolver.dependencies) == 1
        resolver.add_new_requirement(Requirement('Flask'))
        assert len(resolver.dependencies) == 1

    def test_add_new_requirement(self, mocker):
        mock_fetch_requirement(mocker)
        resolver = Resolver()
        assert len(resolver.dependencies) == 0
        resolver.add_new_requirement(Requirement('Flask'))
        assert len(resolver.dependencies) == 6

    def test_add_new_requirement_many_sub_requirements(self, mocker):
        mock_fetch_requirement(mocker)
        resolver = Resolver(extras={'dev'})
        resolver.add_new_requirement(Requirement('Flask'))
        assert len(resolver.dependencies) == 62

    def test_add_new_requirement_on_init(self, mocker):
        mock_fetch_requirement(mocker)
        resolver = Resolver(Requirement('Flask'))
        assert len(resolver.dependencies) == 6
        resolver = Resolver(Requirement('Flask[dev]'))
        assert len(resolver.dependencies) == 62
