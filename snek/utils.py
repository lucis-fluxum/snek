from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Union

from packaging.version import Version, LegacyVersion, InvalidVersion


def convert_to_version(version: str) -> Union[Version, LegacyVersion]:
    try:
        return Version(version)
    except InvalidVersion:
        return LegacyVersion(version)


def parallel_map(function, iterable):
    results = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(function, item) for item in iterable}
        for future in as_completed(futures):
            if future.exception():
                raise future.exception()
            else:
                results.append(future.result())
    return results
