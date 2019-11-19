from __future__ import annotations

import threading
from typing import Set, Union, List

from packaging import requirements
from packaging.version import Version, LegacyVersion


class Requirement(requirements.Requirement):
    def __init__(self, *args, depth=0, project_metadata: dict = None, compatible_versions: list = None,
                 best_candidate_version: Union[Version, LegacyVersion] = None, **kwargs):
        super().__init__(*args, **kwargs)
        if compatible_versions is None:
            compatible_versions = []
        if project_metadata is None:
            project_metadata = {}

        self.lock = threading.RLock()
        self.depth = depth
        self.project_metadata = project_metadata
        self.compatible_versions = compatible_versions
        self.best_candidate_version = best_candidate_version
        self._parent: Requirement = None
        self._children: Set[Requirement] = set()

    def __eq__(self, other: Requirement) -> bool:
        return self.__hash__() == other.__hash__()

    def __hash__(self) -> int:
        return str(self).__hash__()

    def __repr__(self) -> str:
        return f"<Requirement '{self}', depth: {self.depth}>"

    # TODO: This changes the requirement passed in
    def add_sub_requirement(self, req: Requirement):
        with self.lock:
            req._parent = self
            req.depth = self.depth + 1
            self._children.add(req)

    def has_descendant(self, req: Requirement) -> bool:
        with self.lock:
            if req in self._children:
                return True
            for child in self._children:
                if child.has_descendant(req):
                    return True
        return False

    def ancestors(self):
        ancestors: List[Requirement] = []
        node = self
        while node._parent:
            ancestors.append(node._parent)
            node = node._parent
        return ancestors
