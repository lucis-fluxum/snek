from __future__ import annotations
import threading
from typing import Set

from packaging import requirements


class Requirement(requirements.Requirement):
    def __init__(self, *args, depth=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.RLock()
        self.depth = depth
        self._parent: Requirement = None
        self._children: Set[Requirement] = set()

    def __eq__(self, other: Requirement) -> bool:
        return self.__hash__() == other.__hash__()

    def __hash__(self) -> int:
        return str(self).__hash__()

    def __repr__(self) -> str:
        return f"<Requirement '{self}', depth: {self.depth}>"

    def add_sub_requirement(self, req: Requirement) -> Requirement:
        new_req = Requirement(str(req))
        with self.lock:
            new_req._parent = self
            new_req.depth = self.depth + 1
            self._children.add(new_req)
        return new_req

    def has_child(self, req: Requirement) -> bool:
        with self.lock:
            if req in self._children:
                return True
            for child in self._children:
                if child.has_child(req):
                    return True
        return False
