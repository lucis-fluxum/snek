from typing import Union

from packaging.version import Version, LegacyVersion, InvalidVersion


def convert_to_version(version: str) -> Union[Version, LegacyVersion]:
    try:
        return Version(version)
    except InvalidVersion:
        return LegacyVersion(version)
