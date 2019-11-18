import logging
from concurrent.futures.thread import ThreadPoolExecutor
from functools import reduce
from pprint import pp
from typing import List, Dict, Optional, Set

import requests
from packaging.markers import Marker, UndefinedEnvironmentName
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from snek.requirement import Requirement

REPOSITORY_URL = 'https://pypi.org'

log = logging.getLogger(__name__)


# TODO: 'Actions' to perform install/uninstall/update/other tasks
# TODO: Lock file so we don't need to resolve every time. Put a hash in the lockfile of the requirements
#       manifest so we know when to expire it
# TODO: Record dependencies in lock file even if they're not compatible with current environment
# TODO: Check installed package versions (from pip freeze) so you can skip them if needed
# TODO: Abstract out the repository you're using to fetch metadata
class Resolver:
    """
    TODO: Everything described here.
    This is a process that requires several phases:

    1. Find compatible versions for the root requirement.

    2. Starting from the largest compatible version: get a list of sub-requirements, then for each sub-requirement, get
       a list of compatible versions.

    3. For each sub-requirement, starting at the largest compatible version, repeat this process of getting candidate
       versions recursively, until there are no more sub-requirements. If there are no compatible versions of any
       sub-requirement, throw an error to change the best compatible version of its parent and try again. If there are
       no more candidate versions in the parent, throw an error to change the best compatible version of the parent's
       parent, and so on. If there are no more candidate versions to test at the top of the tree, throw another error.

    4. While performing this process, it is possible to encounter a circular dependency, a sub-requirement with the same
       package name as one elsewhere in the dependency tree. If this occurs:
         - Intersect the candidate versions for the new dependency with the candidate versions for the existing one. If
           there is at least one compatible version between them, then we can keep the dependency. Merge the specifier
           of the circular dependency with that of the existing one and remove the circular dependency from the tree.
         - If there are no compatible versions between the two dependencies, throw an error to change the version of the
           circular dependency's parent and try again.

    5. Once this has finished, if we've encountered any circular dependencies, we need to recalculate their
       sub-requirements, since the best compatible version may have changed. Repeat steps 2-4 for requirements whose
       best candidate versions have changed after being merged.

    6. Now we should have a tree of many dependencies, each with a list of one or more compatible candidate versions.
       There should be no obvious conflicts. Starting from the deepest dependencies, install the best candidate version
       for each one using pip install --no-deps

    Note: Some packages on PyPI have no dependencies listed, but do contain some install_requires in their setup.py.
    If that setup.py requires a different version of another package that you've already installed, running the setup.py
    will OVERWRITE your version of that other package with the version required by setup.py. If you install BOTH the
    packages at the same time, one with setup.py (package A) and another version of a package it depends on (package B),
    pip will display an error warning the user that the version of package B they install will not be compatible with
    the version of package B that package A depends on. This is the default behavior of poetry, but it does not display
    the error from pip.
    """

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
