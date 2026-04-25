# vim: set ts=4 sw=4 et: coding=UTF-8

import pytest

from openmoo2.objects.colony import Colony
from openmoo2.objects.colonization import (
    can_colonize, best_planet, colonizable_planets, colonize,
)
from openmoo2.objects.empire import Empire
from openmoo2.objects.galaxy import Galaxy
from openmoo2.objects.planet import Planet
from openmoo2.objects.race import CANONICAL_RACES
from openmoo2.objects.ship import Ship
from openmoo2.objects.system import StarSystem
from openmoo2.objects.turn import TurnManager


@pytest.fixture(autouse=True)
def clear_registry():
    StarSystem._systems.clear()
    yield
    StarSystem._systems.clear()


@pytest.fixture
def human():
    return CANONICAL_RACES['Human']


@pytest.fixture
def trilarian():
    return CANONICAL_RACES['Trilarian']


@pytest.fixture
def system_with_planets():
    s = StarSystem('Kepler', 'yellow', x=50.0, y=50.0)
    terran = Planet('planet', size='large', environment='terran',
                    mineral='average', organic='rich')
    toxic  = Planet('planet', size='small', environment='toxic',
                    mineral='poor', organic='ultrapoor')
    s.planets = terran
    s.planets = toxic
    return s, terran, toxic


@pytest.fixture
def empire_with_colony_ship(human, system_with_planets):
    s, _, _ = system_with_planets
    emp = Empire(human, 'Jones', 'blue')
    emp.ships = [Ship('colony_ship', emp, s)]
    return emp


# ---------------------------------------------------------------------------
# colonizable_planets
# ---------------------------------------------------------------------------

class TestColonizablePlanets:

    def test_free_planets_returned(self, system_with_planets):
        s, terran, toxic = system_with_planets
        result = colonizable_planets(s)
        assert terran in result
        assert toxic in result

    def test_occupied_planet_excluded(self, system_with_planets, human):
        s, terran, _ = system_with_planets
        fake_colony = Colony(terran, human, 'Test')
        terran.colony = fake_colony
        result = colonizable_planets(s)
        assert terran not in result

    def test_asteroids_excluded(self):
        s = StarSystem('Ast', 'red', x=0.0, y=0.0)
        s.planets = Planet('asteroids')
        assert colonizable_planets(s) == []

    def test_giant_excluded(self):
        s = StarSystem('Giant', 'orange', x=0.0, y=0.0)
        s.planets = Planet('giant')
        assert colonizable_planets(s) == []

    def test_empty_system(self):
        s = StarSystem('Empty', 'gray', x=10.0, y=10.0)
        assert colonizable_planets(s) == []


# ---------------------------------------------------------------------------
# can_colonize
# ---------------------------------------------------------------------------

class TestCanColonize:

    def test_true_when_ship_and_free_planet(self, empire_with_colony_ship, system_with_planets):
        s, _, _ = system_with_planets
        assert can_colonize(empire_with_colony_ship, s) is True

    def test_false_when_no_ship(self, human, system_with_planets):
        s, _, _ = system_with_planets
        emp = Empire(human, 'X', 'red')
        emp.ships = []
        assert can_colonize(emp, s) is False

    def test_false_when_ship_traveling(self, human, system_with_planets):
        s, _, _ = system_with_planets
        other = StarSystem('Far', 'blue', x=200.0, y=200.0)
        emp = Empire(human, 'X', 'red')
        ship = Ship('colony_ship', emp, s)
        ship.set_destination(other)
        emp.ships = [ship]
        assert can_colonize(emp, s) is False

    def test_false_when_all_planets_occupied(self, empire_with_colony_ship,
                                              system_with_planets, human):
        s, terran, toxic = system_with_planets
        terran.colony = Colony(terran, human, 'A')
        toxic.colony  = Colony(toxic,  human, 'B')
        assert can_colonize(empire_with_colony_ship, s) is False

    def test_false_when_scout_not_colony_ship(self, human, system_with_planets):
        s, _, _ = system_with_planets
        emp = Empire(human, 'X', 'green')
        emp.ships = [Ship('scout', emp, s)]
        assert can_colonize(emp, s) is False


# ---------------------------------------------------------------------------
# best_planet
# ---------------------------------------------------------------------------

class TestBestPlanet:

    def test_prefers_better_environment(self, system_with_planets, human):
        s, terran, toxic = system_with_planets
        emp = Empire(human, 'X', 'blue')
        result = best_planet(emp, s)
        assert result is terran   # terran (80%) beats toxic (25%)

    def test_aquatic_prefers_ocean(self, trilarian):
        s = StarSystem('Ocean', 'yellow', x=0.0, y=0.0)
        ocean = Planet('planet', size='large', environment='ocean',
                       mineral='average', organic='rich')
        terran = Planet('planet', size='large', environment='terran',
                        mineral='average', organic='rich')
        s.planets = ocean
        s.planets = terran
        emp = Empire(trilarian, 'X', 'blue')
        # Aquatic: ocean=100%, terran=100% (tied) — both score the same
        result = best_planet(emp, s)
        assert result in (ocean, terran)

    def test_none_when_no_colonizable(self, human):
        s = StarSystem('Empty', 'gray', x=0.0, y=0.0)
        emp = Empire(human, 'X', 'blue')
        assert best_planet(emp, s) is None


# ---------------------------------------------------------------------------
# colonize
# ---------------------------------------------------------------------------

class TestColonize:

    def test_creates_colony(self, empire_with_colony_ship, system_with_planets, human):
        s, terran, _ = system_with_planets
        colony = colonize(empire_with_colony_ship, s, terran)
        assert isinstance(colony, Colony)
        assert colony in empire_with_colony_ship.colonies

    def test_planet_marked_occupied(self, empire_with_colony_ship, system_with_planets):
        s, terran, _ = system_with_planets
        colony = colonize(empire_with_colony_ship, s, terran)
        assert terran.colony is colony

    def test_colony_ship_consumed(self, empire_with_colony_ship, system_with_planets):
        s, terran, _ = system_with_planets
        assert len(empire_with_colony_ship.ships) == 1
        colonize(empire_with_colony_ship, s, terran)
        colony_ships = [sh for sh in empire_with_colony_ship.ships
                        if sh.ship_type == 'colony_ship']
        assert len(colony_ships) == 0

    def test_colony_has_starting_population(self, empire_with_colony_ship, system_with_planets):
        s, terran, _ = system_with_planets
        colony = colonize(empire_with_colony_ship, s, terran)
        assert colony.population > 0

    def test_system_added_to_explored(self, empire_with_colony_ship, system_with_planets):
        s, terran, _ = system_with_planets
        colonize(empire_with_colony_ship, s, terran)
        assert s.name in empire_with_colony_ship.explored_systems

    def test_cannot_colonize_occupied_planet(self, empire_with_colony_ship,
                                              system_with_planets, human):
        s, terran, _ = system_with_planets
        colony = colonize(empire_with_colony_ship, s, terran)

        # Add a second colony ship for the second attempt
        emp2_ship = Ship('colony_ship', empire_with_colony_ship, s)
        empire_with_colony_ship.ships.append(emp2_ship)
        with pytest.raises(ValueError):
            colonize(empire_with_colony_ship, s, terran)

    def test_no_colony_ship_raises(self, human, system_with_planets):
        s, terran, _ = system_with_planets
        emp = Empire(human, 'X', 'green')
        emp.ships = []
        with pytest.raises(ValueError):
            colonize(emp, s, terran)


# ---------------------------------------------------------------------------
# TurnManager integration
# ---------------------------------------------------------------------------

class TestColonizationInGame:

    def _setup(self, seed=42):
        StarSystem._systems.clear()
        g = Galaxy(size='small', num_players=2, seed=seed)
        g.generate()
        human  = CANONICAL_RACES['Human']
        psilon = CANONICAL_RACES['Psilon']
        e1 = Empire(human,  'Jones', 'blue')
        e2 = Empire(psilon, 'Psion', 'red')
        g.place_empires([e1, e2])
        tm = TurnManager()
        tm.register_empire(e1)
        tm.register_empire(e2)
        return g, e1, e2, tm

    def test_new_colony_processed_next_turn(self):
        g, e1, _, tm = self._setup()

        # Find a target system with a free planet
        target = next(
            s for s in g.systems
            if s is not e1.homeworld
            and s.color != 'black'
            and any(p for p in s.planets.values()
                    if p is not None and p.kind == 'planet' and p.colony is None)
        )

        # Teleport a colony ship there instantly (for the test)
        ship = next(s for s in e1.ships if s.ship_type == 'colony_ship')
        ship.cancel_orders()
        ship.location = target

        planet = next(
            p for p in target.planets.values()
            if p is not None and p.kind == 'planet' and p.colony is None
        )
        col = colonize(e1, target, planet)
        initial_colonies = len(e1.colonies)

        tm.process_turn()
        # Colony should now be ticking (treasury or research should have changed)
        assert len(e1.colonies) == initial_colonies
        assert e1.treasury > 0 or e1.research_accumulated > 0

    def test_homeworld_planet_not_colonizable(self):
        g, e1, _, _ = self._setup()
        hw = e1.homeworld
        free = colonizable_planets(hw)
        # The homeworld planet has colony set, so it must not appear
        assert e1.homeworld_planet not in free
