from concurrent.futures.thread import ThreadPoolExecutor
from pprint import pp
from typing import List, Dict

import requests
from packaging.markers import Marker, UndefinedEnvironmentName
from packaging.requirements import Requirement

REPOSITORY_URL = 'https://www.pypi.org'


class Resolver:
    def __init__(self, requirement: Requirement):
        self._requirement = requirement
        self._extras = self._requirement.extras
        self._dependencies: Dict[Requirement, Dict] = {}

    def fetch_dependencies(self) -> Dict[Requirement, Dict]:
        # Adding the \n removes the extra time it takes to flush the buffer, when another message could have already
        # been printed.
        print(f"Fetching deps for {str(self._requirement)}...\n", end='')
        json: dict = requests.get(f"{REPOSITORY_URL}/pypi/{self._requirement.name}/json").json()
        deps: List[str] = json['info']['requires_dist']

        if deps and len(deps) > 0:
            reqs = [Requirement(dep) for dep in deps]
            reqs = [req for req in reqs if not req.marker or self.evaluate_marker(req.marker)]
            with ThreadPoolExecutor() as executor:
                executor.map(lambda req: self._dependencies.__setitem__(req, Resolver(req).fetch_dependencies()), reqs)
        return self._dependencies

    def evaluate_marker(self, marker: Marker) -> bool:
        for extra in self._extras:
            try:
                if marker.evaluate({'extra': extra}):
                    return True
            except UndefinedEnvironmentName:
                return False
        return False


if __name__ == '__main__':
    pp(Resolver(Requirement('sphinx')).fetch_dependencies())
