import logging
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Optional, Set, Dict, Union, List

from packaging.markers import Marker

from snek import utils
from snek.repository import Repository
from snek.requirement import Requirement

REPOSITORY_URL = 'https://pypi.org'

log = logging.getLogger(__name__)


# TODO: 'Actions' to perform install/uninstall/update/other tasks
# TODO: Lock file so we don't need to resolve every time. Put a hash in the lockfile of the requirements
#       manifest so we know when to expire it
# TODO: Record dependencies in lock file even if they're not compatible with current environment
# TODO: Check installed package versions (from pip freeze) so you can skip them if needed
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

    def __init__(self, requirement: Optional[Requirement] = None, extras: Optional[Set[str]] = None,
                 dependencies: Optional[List[Requirement]] = None, repository: Optional[Repository] = None):
        if extras is None:
            extras: Set[str] = set()
        if dependencies is None:
            dependencies: List[Requirement] = []
        if repository is None:
            repository = Repository()

        self.dependencies = dependencies
        self._requirement = requirement
        self._extras = extras
        self._repository = repository
        if requirement:
            self._extras: Set[str] = requirement.extras

    def resolve(self, stringify_keys=False) -> Dict[Union[Requirement, str], Dict]:
        if self.dependencies:
            # TODO: Resolve each of the given dependencies
            pass
        else:
            log.debug(f"Populating {self._requirement}")
            self._repository.populate_requirement(self._requirement)

            current_version = utils.convert_to_version(self._requirement.project_metadata['info']['version'])
            if current_version != self._requirement.best_candidate_version:
                self._requirement.project_metadata = self._repository.get_package_info(self._requirement.name,
                                                                                       self._requirement.best_candidate_version)
            requires_dist: list = self._requirement.project_metadata['info']['requires_dist']

            if requires_dist and len(requires_dist) > 0:
                with ThreadPoolExecutor() as executor:
                    executor.map(self.resolve_sub_requirement, requires_dist)
        if stringify_keys:
            return {str(self._requirement): self._requirement.descendants(stringify_keys=True)}
        else:
            return {self._requirement: self._requirement.descendants()}

    def resolve_sub_requirement(self, sub_req_string):
        sub_requirement = Requirement(sub_req_string, depth=self._requirement.depth + 1)

        if not self.check_marker_for_extra(sub_requirement.marker):
            log.warning(f"Ignoring {sub_requirement}.")
        elif sub_requirement.name in map(lambda r: r.name, sub_requirement.ancestors()):
            chain = reversed(list(map(str, sub_requirement.ancestors())))
            log.warning(
                f"Circular dependency detected: {' -> '.join(chain)} -> {sub_requirement}")
        else:
            sub_resolver = Resolver(Requirement(sub_req_string, depth=self._requirement.depth + 1))
            sub_resolver.resolve()
            self._requirement.add_sub_requirement(sub_resolver._requirement)

    def check_marker_for_extra(self, marker: Optional[Marker]) -> bool:
        if 'extra' not in str(marker):
            return True
        for extra in self._extras:
            if f"extra==\"{extra}\"" in str(marker).replace(' ', ''):
                return True
        return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # Suppress debug messages from urllib3
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

    resolver = Resolver(Requirement('Flask[dev]'))
    import json

    print(json.dumps(resolver.resolve(stringify_keys=True), sort_keys=True, indent=4))
