import logging
from concurrent.futures.thread import ThreadPoolExecutor
from functools import reduce
from pprint import pp
from typing import List, Dict, Optional, Set

import requests
from packaging.markers import Marker, UndefinedEnvironmentName
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

REPOSITORY_URL = 'https://pypi.org'

log = logging.getLogger(__name__)


class Resolver:
    @staticmethod
    def fetch_metadata(name: str, version: Optional[Version] = None) -> dict:
        if version:
            response = requests.get(f"{REPOSITORY_URL}/pypi/{name}/{version}/json")
        else:
            response = requests.get(f"{REPOSITORY_URL}/pypi/{name}/json")
        if response:
            return response.json()
        else:
            raise RuntimeError(f"Package not found: {name}")

    @staticmethod
    def get_compatible_versions(*requirements: Requirement):
        if not requirements:
            raise RuntimeError('No requirements given.')
        name = requirements[0].name
        available_versions: Dict[str, list] = Resolver.fetch_metadata(name)['releases']
        merged_requirements = reduce(SpecifierSet.__and__, map(lambda r: r.specifier, requirements))
        return [Version(v) for v in available_versions if v in merged_requirements]

    @staticmethod
    def get_best_version(requirement: Requirement):
        return max(Resolver.get_compatible_versions(requirement))

    def __init__(self, requirement: Optional[Requirement] = None, extras: Optional[Set[str]] = None,
                 dependencies: Optional[List[Requirement]] = None):
        if extras is None:
            extras: Set[str] = set()
        if dependencies is None:
            dependencies: List[Requirement] = []

        self.dependencies = dependencies
        self._requirement = requirement
        self._extras = extras
        if requirement:
            self._extras: Set[str] = requirement.extras
            self.add_new_requirement(requirement)

    def get_sub_requirements(self, requirement: Requirement) -> List[Requirement]:
        metadata = Resolver.fetch_metadata(requirement.name, Resolver.get_best_version(requirement))
        requires_dist: List[str] = metadata['info']['requires_dist']
        if requires_dist and len(requires_dist) > 0:
            reqs = [Requirement(dep) for dep in requires_dist]
            return [req for req in reqs if not req.marker or self.evaluate_marker(req.marker)]
        else:
            return []

    def add_new_requirement(self, new_requirement: Requirement):
        if not self.evaluate_marker(new_requirement.marker):
            log.warning(f"Incompatible marker: {new_requirement.marker}, ignoring {new_requirement}")
            return

        if new_requirement.name not in map(lambda r: r.name, self.dependencies):
            log.debug(f"Adding {new_requirement}...")
            if Resolver.get_compatible_versions(new_requirement):
                self.dependencies.append(new_requirement)
                self.add_sub_requirements(new_requirement)
            else:
                raise RuntimeError(f"No compatible versions found for {new_requirement.name}.")
        else:
            for existing_requirement in self.dependencies:
                if existing_requirement.name.lower() == new_requirement.name.lower():
                    compatible_versions = Resolver.get_compatible_versions(existing_requirement, new_requirement)
                    log.debug(f"Compatible versions for {new_requirement.name}: {compatible_versions}")
                    if compatible_versions:
                        existing_requirement.specifier = existing_requirement.specifier & new_requirement.specifier
                        log.debug(f"Requirement updated: {str(existing_requirement)}")
                        return
                    else:
                        raise RuntimeError(f"No compatible versions found for {new_requirement.name}.")

    def add_sub_requirements(self, requirement: Requirement):
        for sub_requirement in self.get_sub_requirements(requirement):
            if self.evaluate_marker(sub_requirement.marker):
                sub_requirement.marker = None
                sub_resolver = Resolver(sub_requirement, dependencies=self.dependencies)
                self.dependencies = sub_resolver.dependencies

    def evaluate_marker(self, marker: Optional[Marker]) -> bool:
        try:
            return marker is None or marker.evaluate()
        except UndefinedEnvironmentName:
            for extra in self._extras:
                try:
                    if marker.evaluate({'extra': extra}):
                        return True
                except UndefinedEnvironmentName:
                    return False
            return False

    def get_best_versions(self) -> List[Version]:
        with ThreadPoolExecutor() as executor:
            return list(executor.map(Resolver.get_best_version, self.dependencies))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # Suppress debug messages from urllib3
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

    resolver = Resolver(Requirement('notebook[test]==5.0.0'))
    print('Finding best versions...')
    pp(list(zip(resolver.dependencies, resolver.get_best_versions())))
