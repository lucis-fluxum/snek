import logging
from typing import Optional, Set, Dict, Union, List

from snek import utils
from snek.repository import Repository
from snek.requirement import Requirement
from snek.utils import parallel_map

REPOSITORY_URL = 'https://pypi.org'

log = logging.getLogger(__name__)


class CircularDependencyError(RuntimeError):
    pass


# TODO: Add a timeout when resolving dependencies to retry a parallel job, sometimes it just hangs
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

    def __init__(self, repository: Optional[Repository] = None):
        if repository is None:
            repository = Repository()
        self._repository = repository

    def resolve_many(self, requirements: Set[Requirement], stringify_keys=False) -> Dict[Union[Requirement, str], Dict]:
        graphs = parallel_map(lambda req: self.resolve(req, stringify_keys=stringify_keys), requirements)
        result: Dict[Union[Requirement, str], Dict] = {}
        [result.update(graph) for graph in graphs]
        return result

    def resolve(self, requirement: Requirement, stringify_keys=False) -> Dict[Union[Requirement, str], Dict]:
        log.debug(f"Populating {requirement}")

        # Grab metadata, list of compatible versions, and determine largest compatible version for the requirement
        self._repository.populate_requirement(requirement)

        current_version = utils.convert_to_version(requirement.project_metadata['info']['version'])

        # If the metadata's current version is not the same as the largest compatible version, replace the metadata with
        # that of the largest compatible version's metadata.
        if current_version != requirement.best_candidate_version:
            requirement.project_metadata = self._repository.get_package_info(requirement.name,
                                                                             requirement.best_candidate_version)

        # Grab sub-dependencies of the requirement from its metadata
        requires_dist: Optional[List[str]] = requirement.project_metadata['info']['requires_dist']

        if requires_dist and len(requires_dist) > 0:
            sub_requirements = [Requirement(sub_req, parent=requirement) for sub_req in requires_dist]
            parallel_map(self.resolve_sub_requirement, sub_requirements)

        # TODO: Extract to a utility method?
        if stringify_keys:
            return {str(requirement): requirement.descendants(stringify_keys=True)}
        else:
            return {requirement: requirement.descendants()}

    def resolve_sub_requirement(self, sub_requirement: Requirement):
        # Check extras on the sub-requirement in case we don't need it after all
        if Resolver.should_ignore(sub_requirement):
            log.debug(f"Ignoring {sub_requirement}.")
            return

        # Check for a circular dependency >:(
        if sub_requirement.name in map(lambda r: r.name, sub_requirement.ancestors()):
            chain = reversed(list(map(str, sub_requirement.ancestors())))
            log.warning(
                f"Circular dependency detected: {' -> '.join(chain)} -> {sub_requirement}")
            raise CircularDependencyError

        self.resolve(sub_requirement)
        # Finalize the sub-requirement by adding it to the parent requirement
        sub_requirement.parent().add_sub_requirement(sub_requirement)

    @staticmethod
    def should_ignore(sub_requirement: Requirement):
        if 'extra' not in str(sub_requirement.marker):
            return False

        for extra in sub_requirement.parent().extras:
            if f"extra==\"{extra}\"" in str(sub_requirement.marker).replace(' ', ''):
                return False
        return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # Suppress debug messages from urllib3
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

    import json
    print(json.dumps(Resolver().resolve(Requirement('docker-compose'), stringify_keys=True), sort_keys=True, indent=4))
