import functools
import logging
from collections import defaultdict
from typing import Dict, Set, Union

from packaging.specifiers import SpecifierSet
from packaging.version import Version, LegacyVersion

from snek.requirement import Requirement

log = logging.getLogger(__name__)


class ReductionError(RuntimeError):
    pass


class Reducer:
    @staticmethod
    def reduce(dependencies: Dict[Requirement, Dict]):
        # Flatten the tree and pick only the requirements compatible with the current environment
        flattened_dependencies: Set[Requirement] = set(filter(Reducer.is_compatible, Reducer.flatten(dependencies)))
        # Group all versions of requirements by name
        # TODO: Tried to use itertools.groupby here, but it ended up losing a bunch of the requirements somehow :(
        grouped_dependencies = defaultdict(lambda: [])
        [grouped_dependencies[dep.name].append(dep) for dep in flattened_dependencies]

        # Combine the version specifiers for all the groups, then take the highest matching version
        versions: dict = {}
        for name, group in grouped_dependencies.items():
            group = list(group)
            specifier = functools.reduce(SpecifierSet.__and__, map(lambda r: r.specifier, group))
            possible_versions: Set[Union[Version, LegacyVersion]] = set()
            [possible_versions.add(version) for requirement in group for version in requirement.compatible_versions]
            log.debug(f"{name}: specifier '{specifier}', possible versions: {possible_versions}")
            filtered_versions = list(specifier.filter(possible_versions))
            if filtered_versions:
                versions[name] = max(filtered_versions)
            else:
                msg = f"Couldn't find a version for {name}. A dependency map is shown below:"
                for requirement in group:
                    chain = list(reversed(list(map(str, requirement.ancestors()))))
                    if len(chain) > 0:
                        msg += f"\n  {' -> '.join(chain)} -> {requirement}"
                    else:
                        msg += f"\n  {requirement}"
                raise ReductionError(msg)
        return versions

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

    logging.basicConfig(level=logging.DEBUG)
    # Suppress debug messages from urllib3
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

    resolver = Resolver()
    graph = resolver.resolve_many(
        {Requirement('Flask'), Requirement('jupyterlab'), Requirement('tornado==6.0.2')})
    pprint.pp(Reducer.reduce(graph))
