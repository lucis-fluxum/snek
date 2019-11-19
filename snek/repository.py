from functools import reduce
from typing import Optional, Set, Dict, List, Union

import requests
from packaging.specifiers import SpecifierSet
from packaging.version import Version, LegacyVersion

from snek import utils
from snek.requirement import Requirement


class PackageNotFoundError(RuntimeError):
    pass


class InvalidRequirementError(RuntimeError):
    pass


class Repository:
    DEFAULT_URL = 'https://pypi.org/pypi'

    def __init__(self, url=DEFAULT_URL):
        self.url = url

    def get_package_info(self, package_name: str, package_version: Optional[Version] = None) -> dict:
        if package_version:
            response = requests.get(f"{self.url}/{package_name.lower()}/{package_version}/json")
        else:
            response = requests.get(f"{self.url}/{package_name.lower()}/json")
        if response:
            return response.json()
        else:
            raise PackageNotFoundError(package_name, package_version)

    def get_package_releases(self, package_name: str) -> Dict[str, list]:
        return self.get_package_info(package_name)['releases']

    # Assumption: first requirement should have metadata or else I'll go and get it myself
    def get_compatible_versions(self, *requirements: Requirement) -> List[Union[LegacyVersion, Version]]:
        if not requirements:
            raise InvalidRequirementError('No requirements given.')
        names: Set[str] = set(map(lambda r: r.name.lower(), requirements))
        if len(names) > 1:
            raise InvalidRequirementError(f"Requirements must have the same package name. Names provided: {names}")

        name = names.pop()
        if requirements[0].project_metadata:
            all_versions = map(utils.convert_to_version, requirements[0].project_metadata['releases'].keys())
        else:
            all_versions = map(utils.convert_to_version, self.get_package_releases(name).keys())
        final_specifier = reduce(SpecifierSet.__and__, map(lambda r: r.specifier, requirements))
        return list(final_specifier.filter(all_versions))
