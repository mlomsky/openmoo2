# vim: set ts=4 sw=4 et: coding=UTF-8

import math
import pytest

from openmoo2.objects.race import Race, CANONICAL_RACES
from openmoo2.objects.empire import Empire, VALID_COLORS, VALID_PERSONALITIES, VALID_OBJECTIVES
from openmoo2.objects.galaxy import Galaxy
from openmoo2.objects.system import StarSystem


@pytest.fixture(autouse=True)
def clear_star_registry():
    StarSystem._systems.clear()
    yield
    StarSystem._systems.clear()


@pytest.fixture
def human():
    return CANONICAL_RACES['Human']


@pytest.fixture
def psilon():
    return CANONICAL_RACES['Psilon']


@pytest.fixture
def basic_empire(human):
    return Empire(human, 'Emperor Jones', 'blue')


class TestEmpireInit:

    def test_basic_creation(self, human):
        e = Empire(human, 'Caesar', 'red')
        assert e.race is human
        assert e.emperor_name == 'Caesar'
        assert e.color == 'red'

    def test_defaults(self, basic_empire):
        assert basic_empire.homeworld is None
        assert basic_empire.homeworld_planet is None
        assert basic_empire.treasury == 0
        assert basic_empire.explored_systems == set()
        assert basic_empire.personality is None
        assert basic_empire.objective is None

    def test_all_colors_valid(self, human):
        for color in VALID_COLORS:
            Empire(human, 'X', color)

    def test_invalid_color(self, human):
        with pytest.raises(ValueError):
            Empire(human, 'X', 'mauve')

    def test_invalid_personality(self, human):
        with pytest.raises(ValueError):
            Empire(human, 'X', 'red', personality='crazy')

    def test_invalid_objective(self, human):
        with pytest.raises(ValueError):
            Empire(human, 'X', 'red', objective='conqueror')

    def test_valid_personality(self, human):
        for p in VALID_PERSONALITIES:
            e = Empire(human, 'X', 'red', personality=p)
            assert e.personality == p

    def test_valid_objective(self, human):
        for o in VALID_OBJECTIVES:
            e = Empire(human, 'X', 'red', objective=o)
            assert e.objective == o

    def test_race_must_be_race_instance(self):
        with pytest.raises(TypeError):
            Empire('Human', 'X', 'red')

    def test_empty_emperor_name(self, human):
        with pytest.raises(ValueError):
            Empire(human, '', 'red')

    def test_repr(self, basic_empire):
        r = repr(basic_empire)
        assert 'Human' in r
        assert 'blue' in r


class TestHomeworldPlacement:

    def _make_galaxy_with_empires(self, num_players=2, size='tiny', seed=42):
        g = Galaxy(size=size, num_players=num_players, seed=seed)
        g.generate()
        colors = list(VALID_COLORS)
        races = list(CANONICAL_RACES.values())
        empires = [
            Empire(races[i], f'Emperor {i}', colors[i])
            for i in range(num_players)
        ]
        g.place_empires(empires)
        return g, empires

    def test_all_empires_get_homeworlds(self):
        _, empires = self._make_galaxy_with_empires(num_players=3)
        for e in empires:
            assert e.homeworld is not None
            assert e.homeworld_planet is not None

    def test_homeworlds_are_distinct_systems(self):
        _, empires = self._make_galaxy_with_empires(num_players=4)
        homeworld_names = [e.homeworld.name for e in empires]
        assert len(homeworld_names) == len(set(homeworld_names))

    def test_no_empire_on_orion(self):
        g, empires = self._make_galaxy_with_empires()
        for e in empires:
            assert e.homeworld.special == 'homeworld'

    def test_no_empire_on_black_hole(self):
        _, empires = self._make_galaxy_with_empires()
        for e in empires:
            assert e.homeworld.color != 'black'

    def test_homeworld_planet_is_homeworld_special(self):
        _, empires = self._make_galaxy_with_empires()
        for e in empires:
            assert e.homeworld_planet.special == 'homeworld'
            assert e.homeworld_planet.homeworld is True

    def test_homeworld_planet_is_terran_environment(self):
        g = Galaxy(size='tiny', num_players=2, seed=42)
        g.generate()
        human = CANONICAL_RACES['Human']
        empires = [Empire(human, f'Emp {i}', list(VALID_COLORS)[i]) for i in range(2)]
        g.place_empires(empires)
        for e in empires:
            assert e.homeworld_planet.environment == 'terran'

    def test_aquatic_race_gets_ocean_homeworld(self):
        g = Galaxy(size='tiny', num_players=1, seed=42)
        g.generate()
        trilarian = CANONICAL_RACES['Trilarian']
        empire = Empire(trilarian, 'Sea Lord', 'blue')
        g.place_empires([empire])
        assert empire.homeworld_planet.environment == 'ocean'

    def test_large_homeworld_race_gets_huge_planet(self):
        g = Galaxy(size='tiny', num_players=1, seed=42)
        g.generate()
        bulrathi = CANONICAL_RACES['Bulrathi']
        empire = Empire(bulrathi, 'Bear King', 'green')
        g.place_empires([empire])
        assert empire.homeworld_planet.size == 'huge'

    def test_homeworlds_spread_apart(self):
        g, empires = self._make_galaxy_with_empires(num_players=4, size='medium', seed=7)
        min_hw_dist = min(
            math.hypot(
                empires[i].homeworld.x - empires[j].homeworld.x,
                empires[i].homeworld.y - empires[j].homeworld.y,
            )
            for i in range(len(empires))
            for j in range(i + 1, len(empires))
        )
        # Homeworlds should be meaningfully separated
        assert min_hw_dist > g._min_star_distance * 2

    def test_empire_count_mismatch_raises(self):
        g = Galaxy(size='tiny', num_players=2, seed=42)
        g.generate()
        human = CANONICAL_RACES['Human']
        with pytest.raises(ValueError):
            g.place_empires([Empire(human, 'Solo', 'red')])  # 1 instead of 2

    def test_explored_systems_contains_homeworld(self):
        _, empires = self._make_galaxy_with_empires()
        for e in empires:
            assert e.homeworld.name in e.explored_systems

    def test_place_empires_before_generate_raises(self):
        g = Galaxy(size='tiny', num_players=1)
        human = CANONICAL_RACES['Human']
        with pytest.raises(RuntimeError):
            g.place_empires([Empire(human, 'X', 'red')])
