import logging
from typing import List, Dict, Optional

import requests
from packaging.markers import Marker, UndefinedEnvironmentName
from packaging.requirements import Requirement
from packaging.version import Version

REPOSITORY_URL = 'https://pypi.org'

log = logging.getLogger(__name__)


class Resolver:
    def __init__(self, requirement: Requirement, dependencies: List[Requirement] = []):
        self._requirement = requirement
        self._extras = requirement.extras
        self._dependencies: List[Requirement] = dependencies

    def get_requirements(self) -> List[Requirement]:
        metadata = self.fetch_requirement(self._requirement.name)
        requires_dist: List[str] = metadata['info']['requires_dist']
        if requires_dist and len(requires_dist) > 0:
            reqs = [Requirement(dep) for dep in requires_dist]
            return [req for req in reqs if not req.marker or self.evaluate_marker(req.marker)]
        else:
            return []

    def fetch_requirement(self, name: str) -> dict:
        return requests.get(f"{REPOSITORY_URL}/pypi/{name}/json").json()

    def add_new_requirement(self, new_requirement: Requirement):
        if not self.evaluate_marker(new_requirement.marker):
            log.warning(f"Incompatible marker: {new_requirement.marker}")
            return

        for existing_requirement in self._dependencies:
            if existing_requirement.name.lower() == new_requirement.name.lower():
                compatible_versions = self.get_compatible_versions(existing_requirement, new_requirement)
                log.debug(f"{new_requirement.name}: {compatible_versions}")
                if compatible_versions:
                    existing_requirement.specifier = existing_requirement.specifier & new_requirement.specifier
                    log.debug(f"Requirement added: {str(existing_requirement)}")
                else:
                    log.critical(f"No compatible versions found for {new_requirement.name}.")

    def get_compatible_versions(self, existing_requirement, new_requirement):
        available_versions: Dict[str, list] = self.fetch_requirement(existing_requirement.name)['releases']
        return [Version(v) for v in available_versions
                if v in existing_requirement.specifier & new_requirement.specifier]

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


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    r = Resolver(Requirement('Flask[dev]'))
    r._dependencies = r.get_requirements()
    r.add_new_requirement(Requirement('Werkzeug <= 0.15.6; extra == "dev"'))
