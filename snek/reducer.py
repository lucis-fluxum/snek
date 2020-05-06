from typing import Optional, Dict, Set

from snek.repository import Repository
from snek.requirement import Requirement


class Reducer:
    def __init__(self, repository: Optional[Repository] = None):
        if repository is None:
            repository = Repository()
        self._repository = repository

    def reduce(self, dependencies: Set[Requirement]):
        flattened_dependencies = Set[Requirement]
        # TODO: Un-nest the requirements
