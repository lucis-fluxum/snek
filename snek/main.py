import requests
from packaging.requirements import Requirement
from typing import Iterable

REPOSITORY_URL = 'https://www.pypi.org'

if __name__ == '__main__':
    package_name: str = 'flask'
    json: dict = requests.get(f"{REPOSITORY_URL}/pypi/{package_name}/json").json()
    deps: Iterable[str] = json['info']['requires_dist']
    reqs: Iterable[Requirement] = map(lambda dep: Requirement(dep), deps)
    for req in reqs:
        print(req)
