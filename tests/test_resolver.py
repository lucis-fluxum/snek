import sys

from packaging.markers import Marker
from packaging.requirements import Requirement

from snek.resolver import Resolver
from tests.conftest import mock_requests_json

FLASK_REQUIREMENTS = ['Werkzeug>=0.15', 'Jinja2>=2.10.1', 'itsdangerous>=0.24', 'click>=5.1']
FLASK_DEV_REQUIREMENTS = ['Werkzeug>=0.15', 'Jinja2>=2.10.1', 'itsdangerous>=0.24', 'click>=5.1',
                          'pytest; extra == "dev"', 'coverage; extra == "dev"', 'tox; extra == "dev"',
                          'sphinx; extra == "dev"', 'pallets-sphinx-themes; extra == "dev"',
                          'sphinxcontrib-log-cabinet; extra == "dev"', 'sphinx-issues; extra == "dev"']
FLASK_DOCS_REQUIREMENTS = ['Werkzeug>=0.15', 'Jinja2>=2.10.1', 'itsdangerous>=0.24', 'click>=5.1',
                           'sphinx; extra == "docs"', 'pallets-sphinx-themes; extra == "docs"',
                           'sphinxcontrib-log-cabinet; extra == "docs"', 'sphinx-issues; extra == "docs"']


class TestResolver:
    def test_get_requirements(self, mocker, pypi_flask_json):
        mock_requests_json(mocker, pypi_flask_json)
        resolver = Resolver(Requirement('Flask'))
        requirements = resolver.get_requirements()
        assert [str(r) for r in requirements] == FLASK_REQUIREMENTS

    def test_get_dev_requirements(self, mocker, pypi_flask_json):
        mock_requests_json(mocker, pypi_flask_json)
        resolver = Resolver(Requirement('Flask[dev]'))
        requirements = resolver.get_requirements()
        assert [str(r) for r in requirements] == FLASK_DEV_REQUIREMENTS

    def test_get_docs_requirements(self, mocker, pypi_flask_json):
        mock_requests_json(mocker, pypi_flask_json)
        resolver = Resolver(Requirement('Flask[docs]'))
        requirements = resolver.get_requirements()
        assert [str(r) for r in requirements] == FLASK_DOCS_REQUIREMENTS

    def test_evaluate_extra(self):
        resolver_no_extra = Resolver(Requirement('Flask'))
        resolver_one_extra = Resolver(Requirement('Flask[dev]'))
        resolver_multi_extra = Resolver(Requirement('Flask[dev, test, another]'))
        assert not resolver_no_extra.evaluate_marker(Marker("extra == 'dev'"))
        assert resolver_one_extra.evaluate_marker(Marker("extra == 'dev'"))
        assert not resolver_one_extra.evaluate_marker(Marker("extra == 'another'"))
        for extra in ['dev', 'test', 'another']:
            assert resolver_multi_extra.evaluate_marker(Marker(f"extra == '{extra}'"))

    def test_evaluate_marker(self):
        windows_marker = Marker('sys_platform=="win32"')
        resolver = Resolver(Requirement('Flask'))
        if sys.platform == 'win32':
            assert resolver.evaluate_marker(windows_marker)
        else:
            assert not resolver.evaluate_marker(windows_marker)
