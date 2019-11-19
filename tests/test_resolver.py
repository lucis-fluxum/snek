import sys

import pytest
from packaging.markers import Marker

from snek.requirement import Requirement
from snek.resolver import Resolver
from tests.conftest import mock_repository_json

FLASK_REQUIREMENTS = {'Werkzeug>=0.15', 'Jinja2>=2.10.1', 'itsdangerous>=0.24', 'click>=5.1'}
# This includes a version of Flask itself
FLASK_REQUIREMENTS_VERSIONS = ['1.1.1', '0.16.0', '2.10.3', '1.1.1', '1.1.0', '7.0']
FLASK_DEV_REQUIREMENTS = FLASK_REQUIREMENTS.union({'pytest; extra == "dev"', 'coverage; extra == "dev"',
                                                   'tox; extra == "dev"',
                                                   'sphinx; extra == "dev"', 'pallets-sphinx-themes; extra == "dev"',
                                                   'sphinxcontrib-log-cabinet; extra == "dev"',
                                                   'sphinx-issues; extra == "dev"'})
# This includes versions for requirements of sub-requirements
FLASK_DEV_REQUIREMENTS_VERSIONS = ['1.1.1', '0.16.0', '2.10.3', '1.1.1', '1.1.0', '7.0', '5.2.4', '1.8.0', '19.2',
                                   '2.4.5', '1.13.0', '19.3.0', '7.2.0', '1.3.0', '0.13.0', '0.1.7', '4.5.4', '3.14.1',
                                   '16.7.7', '0.10.0', '3.0.12', '2.2.1', '1.0.1', '1.0.1', '1.0.1', '1.0.2', '1.1.3',
                                   '1.0.2', '2.4.2', '0.15.2', '2.0.0', '2.7.0', '2019.3', '0.7.12', '1.1.0', '2.22.0',
                                   '3.0.4', '2.8', '1.25.7', '2019.9.11', '41.6.0', '1.2.2', '0.23', '0.6.0', '2.2.1',
                                   '1.0.1', '1.2.0']
FLASK_DOCS_REQUIREMENTS = FLASK_REQUIREMENTS.union({'sphinx; extra == "docs"', 'pallets-sphinx-themes; extra == "docs"',
                                                    'sphinxcontrib-log-cabinet; extra == "docs"',
                                                    'sphinx-issues; extra == "docs"'})
FLASK_ALL_REQUIREMENTS = FLASK_REQUIREMENTS.union(FLASK_DEV_REQUIREMENTS).union(FLASK_DOCS_REQUIREMENTS)


class TestResolver:
    # TODO: Re-use this code to test new resolving logic
    # @pytest.mark.parametrize('req_str, extras, expected_reqs',
    #                          [('Flask', {}, FLASK_REQUIREMENTS),
    #                           ('Flask[dev]', {'dev'}, FLASK_DEV_REQUIREMENTS),
    #                           ('Flask[docs]', {'docs'}, FLASK_DOCS_REQUIREMENTS),
    #                           ('Flask[dev, docs]', {'dev', 'docs'}, FLASK_ALL_REQUIREMENTS)])
    # def test_get_sub_requirements(self, mocker, req_str, extras, expected_reqs):
    #     mock_repository_json(mocker)
    #     resolver = Resolver(extras=extras)
    #     requirements = map(str, resolver.get_sub_requirements(Requirement(req_str)))
    #     assert set(requirements) == expected_reqs

    def test_evaluate_extra(self):
        resolver_no_extra = Resolver()
        assert not resolver_no_extra.check_marker_for_extra(Marker("extra == 'dev'"))
        resolver_one_extra = Resolver(extras={'dev'})
        assert resolver_one_extra.check_marker_for_extra(Marker("extra == 'dev'"))
        assert not resolver_one_extra.check_marker_for_extra(Marker("extra == 'another'"))
        resolver_multi_extra = Resolver(extras={'dev', 'test', 'another'})
        for extra in ['dev', 'test', 'another']:
            assert resolver_multi_extra.check_marker_for_extra(Marker(f"extra == '{extra}'"))

    # TODO: Evaluate the marker when deciding exactly what to install
    # def test_evaluate_marker(self):
    #     resolver = Resolver()
    #     assert resolver.test_evaluate_marker(None)
    #     windows_marker = Marker('sys_platform=="win32"')
    #     if sys.platform == 'win32':
    #         assert resolver.test_evaluate_marker(windows_marker)
    #     else:
    #         assert not resolver.test_evaluate_marker(windows_marker)

    # TODO: Replace these tests with the following:
    #       - Don't add existing requirement: store list of dependencies in a set
    #       - Add new requirement: just resolve and maybe compare contents of the dependency tree instead of length
    #       - Same for new requirement with many dependencies
    #       - Also have a test for circular dependencies
    # def test_dont_add_existing_requirement(self, mocker):
    #     mock_repository_json(mocker)
    #     resolver = Resolver(dependencies=[Requirement('Flask')])
    #     assert len(resolver.dependencies) == 1
    #     resolver.add_new_requirement(Requirement('Flask'))
    #     assert len(resolver.dependencies) == 1
    #
    # def test_add_new_requirement(self, mocker):
    #     mock_repository_json(mocker)
    #     resolver = Resolver()
    #     assert len(resolver.dependencies) == 0
    #     resolver.add_new_requirement(Requirement('Flask'))
    #     assert len(resolver.dependencies) == 6
    #
    # def test_add_new_requirement_many_sub_requirements(self, mocker):
    #     mock_repository_json(mocker)
    #     resolver = Resolver(extras={'dev'})
    #     resolver.add_new_requirement(Requirement('Flask'))
    #     assert len(resolver.dependencies) == 47
    #
    # def test_add_new_requirement_on_init(self, mocker):
    #     mock_repository_json(mocker)
    #     resolver = Resolver(Requirement('Flask'))
    #     assert len(resolver.dependencies) == 6
    #     resolver = Resolver(Requirement('Flask[dev]'))
    #     assert len(resolver.dependencies) == 47

    # TODO: This comes later, after we are able to actually resolve all the dependencies
    # def test_get_best_versions(self, mocker):
    #     mock_repository_json(mocker)
    #     resolver = Resolver(Requirement('Flask'))
    #     best_versions = map(str, resolver.get_best_versions())
    #     assert list(best_versions) == FLASK_REQUIREMENTS_VERSIONS
    #
    #     resolver = Resolver(Requirement('Flask[dev]'))
    #     best_versions = list(map(str, resolver.get_best_versions()))
    #     assert best_versions == FLASK_DEV_REQUIREMENTS_VERSIONS
