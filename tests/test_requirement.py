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
        r1.add_sub_requirement(r2)
        assert r1.depth == 0
        assert r2.depth == 1

    def test_has_descendant(self):
        r1 = Requirement('Flask')
        r2 = Requirement('bidict')
        assert not r1.has_descendant(r2)
        r1.add_sub_requirement(r2)
        assert r1.has_descendant(r2)

    def test_equality(self):
        r1 = Requirement('Flask')
        r2 = Requirement('Flask')
        r3 = Requirement('bidict')
        assert r1 == r2
        assert r1 != r3
        assert len({r1, r2, r3}) == 2
