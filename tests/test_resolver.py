import json

import pytest

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
    def test_single_resolve(self, mocker, req_str, expected_graph):
        mock_repository_json(mocker)
        resolver = Resolver()
        dep_graph = resolver.resolve(Requirement(req_str), stringify_keys=True)
        assert dep_graph == expected_graph

    def test_multi_resolve(self, mocker):
        mock_repository_json(mocker)
        requirements = {Requirement(req) for req in ['Flask', 'Flask[dev]', 'Flask[test]']}
        resolver = Resolver()
        dep_graphs = resolver.resolve_many(requirements, stringify_keys=True)
        expected_graphs = {}
        expected_graphs.update(FLASK_GRAPH)
        expected_graphs.update(FLASK_DEV_GRAPH)
        expected_graphs.update(FLASK_TEST_GRAPH)
        assert dep_graphs == expected_graphs

    def test_evaluate_extra(self):
        req_no_extras = Requirement('test')
        req_one_extra = Requirement('test[dev]')
        req_multi_extra = Requirement('test[dev, test, another]')

        sub_req = Requirement("test2 ; extra == 'dev'", parent=req_no_extras)
        assert Resolver.should_ignore(sub_req)

        sub_req = Requirement("test2 ; extra == 'dev'", parent=req_one_extra)
        assert not Resolver.should_ignore(sub_req)
        sub_req = Requirement("test2 ; extra == 'another'", parent=req_one_extra)
        assert Resolver.should_ignore(sub_req)

        for extra in ['dev', 'test', 'another']:
            sub_req = Requirement(f"test2 ; extra == '{extra}'", parent=req_multi_extra)
            assert not Resolver.should_ignore(sub_req)

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
