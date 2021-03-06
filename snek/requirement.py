# For PEP 563 https://www.python.org/dev/peps/pep-0563/, remove for Python 4.0+
from __future__ import annotations

import threading
from typing import Set, Union, List, Dict, Optional

from packaging import requirements
from packaging.version import Version, LegacyVersion


class Requirement(requirements.Requirement):
    def __init__(self, *args, parent: Optional[Requirement] = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.lock = threading.RLock()
        self.project_metadata = dict()
        self.compatible_versions: List[Union[LegacyVersion, Version]] = []
        self.best_candidate_version: Optional[Union[LegacyVersion, Version]] = None
        self._parent: Optional[Requirement] = parent
        self._children: Set[Requirement] = set()

    def __eq__(self, other: Requirement) -> bool:
        return self.__hash__() == other.__hash__()

    def __hash__(self) -> int:
        return str(self).__hash__()

    def __repr__(self) -> str:
        return f"<Requirement '{self}'>"

    # TODO: This changes the requirement passed in
    def add_sub_requirement(self, req: Requirement):
        with self.lock:
            req._parent = self
            self._children.add(req)

    def has_descendant(self, req: Requirement) -> bool:
        with self.lock:
            if req in self._children:
                return True
            for child in self._children:
                if child.has_descendant(req):
                    return True
        return False

    def parent(self) -> Optional[Requirement]:
        return self._parent

    def children(self) -> Set[Requirement]:
        return self._children

    def ancestors(self) -> List[Requirement]:
        ancestors: List[Requirement] = []
        node = self
        while node._parent:
            ancestors.append(node._parent)
            node = node._parent
        return ancestors

    def descendants(self, stringify_keys: bool = False) -> Dict[Union[Requirement, str], Dict]:
        descendants = {}
        for child in self._children:
            if stringify_keys:
                descendants[str(child)] = child.descendants(stringify_keys=True)
            else:
                descendants[child] = child.descendants()
        return descendants
