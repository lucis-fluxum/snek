import pytest

from snek.requirement import Requirement


class TestRequirement:
    def test_new_requirement(self):
        with pytest.raises(TypeError):
            # Inherits behavior from packaging.requirements
            Requirement()
        r = Requirement('Flask')
        assert r.parent() is None
        assert len(r.children()) == 0

    def test_equality(self):
        r1 = Requirement('Flask')
        r2 = Requirement('Flask')
        r3 = Requirement('bidict')
        assert r1 == r2
        assert r1 != r3
        assert len({r1, r2, r3}) == 2

    def test_add_sub_requirement(self):
        r1 = Requirement('Flask')
        r2 = Requirement('bidict')
        assert r1.parent() is None and r2.parent() is None
        assert len(r1.children()) == 0 and len(r2.children()) == 0
        r1.add_sub_requirement(r2)
        assert r1.parent() is None and r2.parent() == r1
        assert len(r1.children()) == 1 and len(r2.children()) == 0

    def test_has_descendant(self):
        r1 = Requirement('Flask')
        r2 = Requirement('bidict')
        assert not r1.has_descendant(r2)
        r1.add_sub_requirement(r2)
        assert r1.has_descendant(r2)

    # TODO: Test ancestors, descendants
