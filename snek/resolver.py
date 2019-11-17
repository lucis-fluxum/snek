from pprint import pp
from typing import List, Dict

import requests
from packaging.markers import Marker, UndefinedEnvironmentName
from packaging.requirements import Requirement

REPOSITORY_URL = 'https://pypi.org'


class Resolver:
    def __init__(self, requirement: Requirement):
        self._requirement = requirement
        self._extras = self._requirement.extras
        self._dependencies: Dict[Requirement, Dict] = {}

    def get_requirements(self) -> List[Requirement]:
        metadata: dict = requests.get(f"{REPOSITORY_URL}/pypi/{self._requirement.name}/json").json()
        requires_dist: List[str] = metadata['info']['requires_dist']
        if requires_dist and len(requires_dist) > 0:
            reqs = [Requirement(dep) for dep in requires_dist]
            return [req for req in reqs if not req.marker or self.evaluate_marker(req.marker)]
        else:
            return []

    def evaluate_marker(self, marker: Marker) -> bool:
        for extra in self._extras:
            try:
                if marker.evaluate({'extra': extra}):
                    return True
            except UndefinedEnvironmentName:
                return False
        return False


if __name__ == '__main__':
    pp(Resolver(Requirement('Flask[dev]')).get_requirements())
