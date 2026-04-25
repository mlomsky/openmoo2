
import pytest
from openmoo2.objects.system import StarSystem


class FakePlanet(object):
    def __init__(self, kind):
        self.kind = kind

    def __str__(self):
        return "Planeta : {}".format(self.kind)


class TestSystem(object):
    planetA = FakePlanet("asteroids")
    planetB = FakePlanet("giant")
    planetC = FakePlanet("planet")
    planetD = None
    blackhole = StarSystem("hole", "black")

    def test_black_hole(self):
        assert self.blackhole.name == 'hole'
        assert self.blackhole.color == "black"

    def test_blackhole_planetes(self):
        assert self.blackhole.planets == {x+1: None for x in range(StarSystem.max_planets)}

    def test_add_planet_black_hole(self):
        with pytest.raises(Exception):
            self.blackhole.planets = self.planetD

    def test_add_administrator(self):
        with pytest.raises(Exception):
            self.blackhole.administrator = "Pepa z depa"

    def test_star(self):
        star = StarSystem("foo", "orange")
        assert star.color == "orange"
        assert star.name == "foo"
        assert star.administrator is None
        assert star.planets == {}
        assert 'foo' in star._systems

    def test_star_add_planet(self):
        star = StarSystem("boo", "orange")
        star.planets = "one"
        assert star.planets == {1: 'one'}

    def test_star_add_many_planets(self):
        with pytest.raises(Exception):
            star = StarSystem("baz", "orange")
            for i in range(StarSystem.max_planets+1):
                star.planets = self.planetC

    def test_rename_star(self):
        star = StarSystem("fii", "orange")
        assert star.name == 'fii'
        star.name = "faa"
        assert star.name == "faa"
        assert "fii" not in star._systems

    def test_rename_star_wrongly(self):
        with pytest.raises(Exception):
            x = StarSystem._systems[1]
            self.blackhole.name = x

    def test_star_administrator(self):
        star = StarSystem("Terra", "orange")
        assert star.administrator is None
        star.administrator = "emperor"
        assert star.administrator == "emperor"
        del star.administrator
        assert star.administrator is None
