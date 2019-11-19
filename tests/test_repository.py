from snek.repository import Repository
from snek.requirement import Requirement
from tests.conftest import mock_repository_json


class TestRepository:
    def test_get_compatible_versions(self, mocker):
        mock_repository_json(mocker)
        repo = Repository()
        assert len(repo.get_compatible_versions(Requirement('Flask'))) == 32
        assert len(repo.get_compatible_versions(Requirement('Flask'),
                                                Requirement('Flask > 1.0'))) == 6
        assert len(repo.get_compatible_versions(Requirement('Flask'),
                                                Requirement('Flask > 1.0'),
                                                Requirement('Flask <= 1.1'))) == 5
        assert len(repo.get_compatible_versions(Requirement('Flask'),
                                                Requirement('Flask ~= 1.0'))) == 7
        assert len(repo.get_compatible_versions(Requirement('Flask > 1'),
                                                Requirement('Flask < 1'))) == 0
