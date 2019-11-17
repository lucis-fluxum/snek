import sys

import pytest
from packaging.markers import Marker
from packaging.requirements import Requirement

from snek.resolver import Resolver

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


@pytest.fixture
def make_resolver():
    return lambda name: Resolver(Requirement(name))


class TestResolver:
    @pytest.mark.parametrize('req_str, expected_reqs',
                             [('Flask', FLASK_REQUIREMENTS), ('Flask[dev]', FLASK_DEV_REQUIREMENTS),
                              ('Flack[docs]', FLASK_DOCS_REQUIREMENTS), ('Flask[dev, docs]', FLASK_ALL_REQUIREMENTS)])
    def test_get_requirements(self, mocker, make_resolver, pypi_flask_json, req_str, expected_reqs):
        resolver = make_resolver(req_str)
        mocker.patch.object(resolver, 'fetch_requirement', return_value=pypi_flask_json)
        requirements = map(str, resolver.get_requirements())
        assert set(requirements) == expected_reqs

    def test_evaluate_extra(self, make_resolver):
        resolver_no_extra = make_resolver('Flask')
        assert not resolver_no_extra.evaluate_marker(Marker("extra == 'dev'"))
        resolver_one_extra = make_resolver('Flask[dev]')
        assert resolver_one_extra.evaluate_marker(Marker("extra == 'dev'"))
        assert not resolver_one_extra.evaluate_marker(Marker("extra == 'another'"))
        resolver_multi_extra = make_resolver('Flask[dev, test, another]')
        for extra in ['dev', 'test', 'another']:
            assert resolver_multi_extra.evaluate_marker(Marker(f"extra == '{extra}'"))

    def test_evaluate_marker(self, make_resolver):
        resolver = make_resolver('Flask')
        assert resolver.evaluate_marker(None)
        windows_marker = Marker('sys_platform=="win32"')
        if sys.platform == 'win32':
            assert resolver.evaluate_marker(windows_marker)
        else:
            assert not resolver.evaluate_marker(windows_marker)
