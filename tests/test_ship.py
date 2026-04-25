# vim: set ts=4 sw=4 et: coding=UTF-8

import math
import pytest

from openmoo2.objects.empire import Empire
from openmoo2.objects.galaxy import Galaxy
from openmoo2.objects.race import CANONICAL_RACES
from openmoo2.objects.ship import Ship, SHIP_SPEED, SHIP_TYPES
from openmoo2.objects.system import StarSystem
from openmoo2.objects.turn import TurnManager


@pytest.fixture(autouse=True)
def clear_registry():
    StarSystem._systems.clear()
    yield
    StarSystem._systems.clear()


@pytest.fixture
def star_a():
    return StarSystem('Alpha', 'yellow', x=0.0, y=0.0)


@pytest.fixture
def star_b():
    return StarSystem('Beta', 'red', x=30.0, y=40.0)   # distance = 50 units


@pytest.fixture
def human():
    return CANONICAL_RACES['Human']


@pytest.fixture
def empire(human):
    e = Empire(human, 'Jones', 'blue')
    e.ships = []
    return e


@pytest.fixture
def scout(empire, star_a):
    return Ship('scout', empire, star_a)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestShipInit:

    def test_valid_types(self, empire, star_a):
        for t in SHIP_TYPES:
            Ship(t, empire, star_a)

    def test_invalid_type(self, empire, star_a):
        with pytest.raises(ValueError):
            Ship('battleship', empire, star_a)

    def test_starts_orbiting(self, scout):
        assert scout.is_orbiting
        assert not scout.is_traveling
        assert scout.destination is None
        assert scout.eta == 0

    def test_travel_fraction_zero_when_orbiting(self, scout):
        assert scout.travel_fraction == 0.0

    def test_galaxy_pos_at_origin(self, scout, star_a):
        assert scout.galaxy_pos == (star_a.x, star_a.y)

    def test_repr(self, scout, star_a):
        r = repr(scout)
        assert 'scout' in r
        assert star_a.name in r

    def test_display_name(self, scout):
        assert 'Scout' in scout.display_name
        assert 'Human' in scout.display_name


# ---------------------------------------------------------------------------
# Speed
# ---------------------------------------------------------------------------

class TestShipSpeed:

    def test_scout_faster_than_colony_ship(self, empire, star_a):
        scout = Ship('scout', empire, star_a)
        colony = Ship('colony_ship', empire, star_a)
        assert scout.speed > colony.speed

    def test_speed_values(self, empire, star_a):
        for ship_type, expected_speed in SHIP_SPEED.items():
            s = Ship(ship_type, empire, star_a)
            assert s.speed == expected_speed


# ---------------------------------------------------------------------------
# Set destination / ETA
# ---------------------------------------------------------------------------

class TestDestination:

    def test_set_destination(self, scout, star_a, star_b):
        scout.set_destination(star_b)
        assert scout.is_traveling
        assert scout.destination is star_b
        assert not scout.is_orbiting

    def test_eta_correct(self, scout, star_a, star_b):
        # distance = 50, scout speed = 6 → ceil(50/6) = 9 turns
        scout.set_destination(star_b)
        assert scout.eta == math.ceil(50 / scout.speed)

    def test_set_destination_same_system_noop(self, scout, star_a):
        scout.set_destination(star_a)
        assert scout.is_orbiting

    def test_cancel_orders(self, scout, star_b):
        scout.set_destination(star_b)
        scout.cancel_orders()
        assert scout.is_orbiting
        assert scout.destination is None
        assert scout.eta == 0

    def test_can_reassign_destination(self, empire, star_a, star_b):
        star_c = StarSystem('Gamma', 'blue', x=10.0, y=0.0)
        s = Ship('scout', empire, star_a)
        s.set_destination(star_b)
        s.set_destination(star_c)
        assert s.destination is star_c


# ---------------------------------------------------------------------------
# Advance / movement
# ---------------------------------------------------------------------------

class TestMovement:

    def test_advance_when_orbiting_returns_false(self, scout):
        assert scout.advance_turn() is False

    def test_advance_does_not_move_orbiting_ship(self, scout, star_a):
        scout.advance_turn()
        assert scout.location is star_a

    def test_ship_arrives_after_eta_turns(self, scout, star_b):
        scout.set_destination(star_b)
        eta = scout.eta
        for _ in range(eta - 1):
            assert scout.advance_turn() is False
        arrived = scout.advance_turn()
        assert arrived is True

    def test_ship_at_destination_after_arrival(self, scout, star_b):
        scout.set_destination(star_b)
        eta = scout.eta
        for _ in range(eta):
            scout.advance_turn()
        assert scout.location is star_b
        assert scout.is_orbiting

    def test_travel_fraction_increases(self, scout, star_b):
        scout.set_destination(star_b)
        fracs = []
        while scout.is_traveling:
            fracs.append(scout.travel_fraction)
            scout.advance_turn()
        # Fractions should be monotonically increasing
        assert all(fracs[i] <= fracs[i+1] for i in range(len(fracs)-1))
        assert fracs[0] == 0.0

    def test_galaxy_pos_interpolates(self, scout, star_a, star_b):
        scout.set_destination(star_b)
        scout.advance_turn()
        gx, gy = scout.galaxy_pos
        # After 1 turn, ship should be somewhere between A and B
        assert star_a.x < gx < star_b.x or star_a.x > gx > star_b.x or gx == star_a.x
        assert gx != star_b.x or gy != star_b.y  # not yet arrived

    def test_minimum_one_turn_journey(self, empire):
        # Even adjacent stars take at least 1 turn
        near = StarSystem('Near', 'red', x=0.0, y=0.0)
        very_near = StarSystem('VeryNear', 'orange', x=0.1, y=0.0)
        s = Ship('scout', empire, near)
        s.set_destination(very_near)
        assert s.eta >= 1


# ---------------------------------------------------------------------------
# TurnManager integration
# ---------------------------------------------------------------------------

class TestShipInTurnManager:

    def _setup(self):
        StarSystem._systems.clear()
        g = Galaxy(size='tiny', num_players=2, seed=42)
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

    def test_empires_start_with_ships(self):
        _, e1, e2, _ = self._setup()
        assert len(e1.ships) == 2
        assert len(e2.ships) == 2

    def test_starting_ships_are_correct_types(self):
        _, e1, _, _ = self._setup()
        types = {s.ship_type for s in e1.ships}
        assert 'scout' in types
        assert 'colony_ship' in types

    def test_arrivals_reported_in_turn_result(self):
        g, e1, e2, tm = self._setup()
        scout = next(s for s in e1.ships if s.ship_type == 'scout')
        # Send to the closest non-homeworld star
        target = next(
            s for s in g.systems
            if s is not e1.homeworld and s.color != 'black'
        )
        scout.set_destination(target)
        eta = scout.eta

        result = None
        for _ in range(eta):
            result = tm.process_turn()

        assert scout in result.arrivals[e1]

    def test_arrival_adds_to_explored(self):
        g, e1, _, tm = self._setup()
        scout = next(s for s in e1.ships if s.ship_type == 'scout')
        target = next(s for s in g.systems if s is not e1.homeworld and s.color != 'black')
        scout.set_destination(target)
        for _ in range(scout.eta):
            tm.process_turn()
        assert target.name in e1.explored_systems

    def test_no_arrivals_when_orbiting(self):
        _, e1, _, tm = self._setup()
        result = tm.process_turn()
        assert result.arrivals[e1] == []
