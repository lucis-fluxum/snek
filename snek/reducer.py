import itertools
from typing import Optional, Dict, Set, List

from snek.repository import Repository
from snek.requirement import Requirement


class Reducer:
    def __init__(self, repository: Optional[Repository] = None):
        if repository is None:
            repository = Repository()
        self._repository = repository

    def reduce(self, dependencies: Dict[Requirement, Dict]):
        flattened_dependencies: Set[Requirement] = set(filter(Reducer.is_compatible, Reducer.flatten(dependencies)))
        grouped_dependencies = itertools.groupby(flattened_dependencies, lambda req: req.name)
        names: List[str] = []
        groups: List[List[Requirement]] = []
        for name, group in grouped_dependencies:
            names.append(name)
            groups.append(list(group))
        return names, groups

    @staticmethod
    def flatten(dependencies: Dict[Requirement, Dict]) -> Set[Requirement]:
        result: Set[Requirement] = set()
        for key in dependencies.keys():
            result.add(key)
        for value in dependencies.values():
            [result.add(dep) for dep in Reducer.flatten(value)]
        return result

    @staticmethod
    def is_compatible(requirement: Requirement) -> bool:
        if requirement.marker is None:
            return True

        if requirement.parent():
            extras = requirement.parent().extras
            for extra in extras:
                if requirement.marker.evaluate({'extra': extra}):
                    return True
            return False
        else:
            return requirement.marker.evaluate({'extra': ''})


if __name__ == '__main__':
    import pprint
    from snek.resolver import Resolver

    resolver = Resolver()
    reducer = Reducer()
    pprint.pp(reducer.reduce(resolver.resolve_many({Requirement('Flask[dev]'), Requirement('docker-compose')})))
