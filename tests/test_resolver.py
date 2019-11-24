import json

import pytest
from packaging.markers import Marker

from snek.requirement import Requirement
from snek.resolver import Resolver
from tests.conftest import mock_repository_json, load_fixture

FLASK_GRAPH = json.loads(load_fixture('resolver/Flask_dependency_graph.json'))
FLASK_DEV_GRAPH = json.loads(load_fixture('resolver/Flask[dev]_dependency_graph.json'))
FLASK_TEST_GRAPH = json.loads(load_fixture('resolver/Flask[test]_dependency_graph.json'))
FLASK_DOCS_GRAPH = json.loads(load_fixture('resolver/Flask[docs]_dependency_graph.json'))
FLASK_ALL_EXTRAS_GRAPH = json.loads(load_fixture('resolver/Flask[dev, docs, test]_dependency_graph.json'))


class TestResolver:
    @pytest.mark.parametrize('req_str, expected_graph',
                             [('Flask', FLASK_GRAPH),
                              ('Flask[dev]', FLASK_DEV_GRAPH),
                              ('Flask[test]', FLASK_TEST_GRAPH),
                              ('Flask[docs]', FLASK_DOCS_GRAPH),
                              ('Flask[dev, docs, test]', FLASK_ALL_EXTRAS_GRAPH)])
    def test_resolve(self, mocker, req_str, expected_graph):
        mock_repository_json(mocker)
        resolver = Resolver(Requirement(req_str))
        dep_graph = resolver.resolve(stringify_keys=True)
        assert dep_graph == expected_graph

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
