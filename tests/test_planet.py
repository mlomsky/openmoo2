# vim: set ts=4 sw=4 et: coding=UTF-8
"""
Test planet generator from objects/planet.py
"""

import pytest
from openmoo2.objects.planet import Planet


class FakeColony(object):

    def __init__(self, kind, owner):
        self.owner = owner
        self.kind = kind

    def __str__(self):
        return self.owner


class TestPlanet(object):
    outpost = FakeColony('outpost', 'Boo')
    colony = FakeColony('colony', 'Poo')

    def test_planet_wrong_type(self):
        with pytest.raises(Exception):
            Planet('foo')

    def test_planet_gravity_override(self):
        planetx = Planet('planet', size='huge', organic='rich', mineral='rich', environment='toxic', gravity='medium')
        assert planetx.gravity == 'medium'

    def test_gravity_heavy(self):
        planetx = Planet('planet', size='huge', organic='rich', mineral='rich', environment='toxic')
        assert planetx.gravity == 'heavy'

    def test_gravity_low(self):
        planetx = Planet('planet', size='tiny', organic='rich', mineral='poor', environment='toxic')
        assert planetx.gravity == 'low'

    def test_gravity_medium(self):
        planetx = Planet('planet', size='small', organic='rich', mineral='average', environment='toxic')
        assert planetx.gravity == 'medium'

    def test_gravity_del(self):
        planetx = Planet('planet', size='tiny', organic='rich', mineral='poor', environment='toxic')
        planetx.gravity = 'heavy'
        assert planetx.gravity == 'heavy'
        del planetx.gravity
        assert planetx.gravity == 'low'

    def test_read_gravity_giant(self):
        planetx = Planet('giant')
        assert planetx.gravity is None

    def test_read_gravity_asteroids(self):
        planetx = Planet('asteroids')
        assert planetx.gravity is None

    def test_set_gravity_giant(self):
        with pytest.raises(Exception):
            planetx = Planet('giant')
            planetx.gravity = 'heavy'

    def test_set_gravity_asteroids(self):
        with pytest.raises(Exception):
            planetx = Planet('asteroids')
            planetx.gravity = 'heavy'

    def test_set_gravity_asteroids2(self):
        planetx = Planet('asteroids')
        planetx.gravity = None
        assert planetx.gravity is None

    def test_set_gravity_correctly(self):
        planetx = Planet('planet', size='small', organic='rich', mineral='average', environment='toxic')
        gravity = ('low', 'medium', 'heavy')
        for i in gravity:
            planetx.gravity = i
            assert planetx.gravity == i

    def test_set_gravity_wrongly(self):
        with pytest.raises(Exception):
            planetx = Planet('planet', size='small', organic='rich', mineral='average', environment='toxic')
            planetx.gravity = 'jupajda'

    def test_bad_init_planet1(self):
        with pytest.raises(Exception):
            Planet('planet')

    def test_bad_init_planet2(self):
        with pytest.raises(Exception):
            Planet('planet', size='small')

    def test_bad_init_planet3(self):
        with pytest.raises(Exception):
            Planet('planet', size='small', organic='poor')

    def test_bad_init_planet4(self):
        with pytest.raises(Exception):
            Planet('planet', organic='poor', mineral='poor')

    def test_bad_init_planet5(self):
        with pytest.raises(Exception):
            Planet('planet', environment='toxic')

    def test_bad_init_planet6(self):
        with pytest.raises(Exception):
            Planet('planet', size='tiny', organic='poor', environment='toxic')

    def test_bad_init_planet7(self):
        with pytest.raises(Exception):
            Planet('planet', environment='toxic', mineral='rich', size='huge')

    def test_destroy_planet(self):
        planetx = Planet('planet', size='huge', organic='rich', mineral='rich', environment='toxic')
        assert planetx.kind == 'planet'
        planetx.destroy_planet()
        assert planetx.kind == 'asteroids'

    def test_create_planet_asteroids(self):
        planetx = Planet('asteroids')
        planetx.create_planet(size='medium', organic='average', mineral='rich', environment='barren')
        assert planetx.gravity == 'medium'

    def test_create_planet_giant(self):
        planetx = Planet('giant')
        planetx.create_planet(size='medium', organic='average', mineral='rich', environment='barren')
        assert planetx.gravity == 'medium'

    def test_create_planet_giant_outpost(self):
        planetx = Planet('giant')
        planetx.create_planet(
            size='medium',
            organic='average',
            mineral='rich',
            environment='barren',
            colony=self.outpost)
        assert planetx.gravity == 'medium'
        assert planetx.colony is None

    def test_create_planet_asteroids_gravity(self):
        planetx = Planet('asteroids')
        planetx.create_planet(size='medium', organic='average', mineral='rich', environment='barren', gravity='heavy')
        assert planetx.gravity == 'heavy'

    def test_create_planet_planet(self):
        with pytest.raises(Exception):
            planetx = Planet('planet', size='huge', organic='rich', mineral='rich', environment='toxic')
            planetx.create_planet(size='medium', organic='average', mineral='rich', environment='barren')

    def test_create_planet_missing_property1(self):
        with pytest.raises(Exception):
            planetx = Planet('asteroids')
            planetx.create_planet(size='medium', organic='average', mineral='rich')

    def test_create_planet_missing_property2(self):
        with pytest.raises(Exception):
            planetx = Planet('asteroids')
            planetx.create_planet(size='medium', mineral='rich', environment='barren')

    def test_create_planet_missing_property3(self):
        with pytest.raises(Exception):
            planetx = Planet('asteroids')
            planetx.create_planet(size='medium', organic='average', environment='barren')

    def test_create_planet_missing_property4(self):
        with pytest.raises(Exception):
            planetx = Planet('asteroids')
            planetx.create_planet(organic='average', mineral='rich', environment='barren')

    def test_create_planet_missing_property5(self):
        with pytest.raises(Exception):
            planetx = Planet('asteroids')
            planetx.create_planet()

    def test_colony_asteroids1(self):
        planetx = Planet('asteroids', colony=self.outpost)
        assert planetx.colony is None

    def test_colony_asteroids2(self):
        planetx = Planet('asteroids', colony=self.colony)
        assert planetx.colony is None

    def test_colony_set_asteroids(self):
        with pytest.raises(Exception):
            planetx = Planet('asteroids')
            planetx.colony = self.outpost

    def test_colony_set_asteroids2(self):
        with pytest.raises(Exception):
            planetx = Planet('asteroids')
            planetx.colony = self.colony

    def test_giant_outpost(self):
        planetx = Planet('giant', colony=self.outpost)
        assert planetx.colony.kind == 'outpost'

    def test_giant_colony(self):
        with pytest.raises(Exception):
            Planet('giant', colony=self.colony)

    def test_set_colony_giant(self):
        with pytest.raises(Exception):
            planetx = Planet('giant')
            planetx.colony = self.colony

    def test_planet_colony(self):
        planetx = Planet(
            'planet',
            size='small',
            organic='rich',
            mineral='average',
            environment='gaia',
            colony=self.colony)
        assert planetx.colony.kind == 'colony'

    def test_planet_outpost(self):
        planetx = Planet(
            'planet',
            size='small',
            organic='rich',
            mineral='average',
            environment='gaia',
            colony=self.outpost)
        assert planetx.colony.kind == 'outpost'

    def test_del_colony_planet(self):
        planetx = Planet(
            'planet',
            size='small',
            organic='rich',
            mineral='average',
            environment='gaia',
            colony=self.colony)
        del planetx.colony
        assert planetx.colony is None

    def test_del_outpost_giant(self):
        planetx = Planet('giant', colony=self.outpost)
        del planetx.colony
        assert planetx.colony is None

    def test_planet_strings_asteroids(self):
        planetx = Planet('asteroids')
        assert str(planetx) == 'This is asteroids field'

    def test_planet_strings_giant(self):
        planetx = Planet('giant')
        assert str(planetx) == 'This is gas giant planet'

    def test_planet_strings_giant_outpost(self):
        planetx = Planet('giant', colony=self.outpost)
        assert str(planetx) == 'This is gas giant planet with outpost: Boo'

    def test_planet_strings_planet(self):
        planetx = Planet('planet', size='small', organic='rich', mineral='average', environment='gaia')
        assert str(planetx) == 'Planet size: small gravity: medium with gaia environment\nHas average minerals and rich biology\n'

    def test_planet_strings_planet_outpost(self):
        planetx = Planet(
            'planet',
            size='small',
            organic='rich',
            mineral='average',
            environment='gaia',
            colony=self.outpost)
        assert str(planetx) == 'Planet size: small gravity: medium with gaia environment\nHas average minerals and rich biology\nHas Boo outpost'

    def test_planet_strings_planet_colony(self):
        planetx = Planet(
            'planet',
            size='small',
            organic='rich',
            mineral='average',
            environment='gaia',
            colony=self.colony)
        assert str(planetx) == 'Planet size: small gravity: medium with gaia environment\nHas average minerals and rich biology\nIs colonized:\n Poo'

    def test_planet_strings_planet_colony_special(self):
        planetx = Planet(
            'planet',
            size='small',
            organic='rich',
            mineral='average',
            environment='gaia',
            colony=self.colony,
            special="Orion")
        assert str(planetx) == 'Planet size: small gravity: medium with gaia environment\nHas average minerals and rich biology\nHas Orion special\nIs colonized:\n Poo'
