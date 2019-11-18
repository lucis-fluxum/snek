import pytest

from snek.requirement import Requirement


class TestRequirement:
    def test_new_requirement(self):
        with pytest.raises(TypeError):
            # Inherits behavior from packaging.requirements
            Requirement()
        r = Requirement('Flask')
        assert r.depth == 0

    def test_add_sub_requirement(self):
        r1 = Requirement('Flask')
        r2 = Requirement('bidict')
        assert r1.depth == 0
        assert r2.depth == 0
        r2 = r1.add_sub_requirement(r2)
        assert r1.depth == 0
        assert r2.depth == 1

    def test_has_child(self):
        r1 = Requirement('Flask')
        r2 = Requirement('bidict')
        assert not r1.has_child(r2)
        r2 = r1.add_sub_requirement(r2)
        assert r1.has_child(r2)
