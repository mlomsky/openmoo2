# vim: set ts=4 sw=4 et: coding=UTF-8

import pytest
from openmoo2.objects.colony import Colony
from openmoo2.objects.empire import Empire
from openmoo2.objects.galaxy import Galaxy
from openmoo2.objects.planet import Planet
from openmoo2.objects.race import CANONICAL_RACES
from openmoo2.objects.system import StarSystem
from openmoo2.objects.turn import TurnManager, TurnResult


@pytest.fixture(autouse=True)
def clear_registry():
    StarSystem._systems.clear()
    yield
    StarSystem._systems.clear()


@pytest.fixture
def terran():
    return Planet('planet', size='large', environment='terran',
                  mineral='average', organic='rich')


@pytest.fixture
def human():
    return CANONICAL_RACES['Human']


@pytest.fixture
def psilon():
    return CANONICAL_RACES['Psilon']


def make_empire(race, color):
    return Empire(race, f'Emperor of {race.name}', color)


def make_colony(planet, race, name='Test', farmers=3, workers=2, scientists=1):
    c = Colony(planet, race, name=name)
    c.set_population(farmers=farmers, workers=workers, scientists=scientists)
    return c


class TestTurnManager:

    def test_register_empire(self, human, terran):
        tm = TurnManager()
        empire = make_empire(human, 'blue')
        empire.colonies = [make_colony(terran, human)]
        tm.register_empire(empire)
        assert empire in tm.empires

    def test_register_same_empire_twice_raises(self, human, terran):
        tm = TurnManager()
        empire = make_empire(human, 'blue')
        empire.colonies = []
        tm.register_empire(empire)
        with pytest.raises(ValueError):
            tm.register_empire(empire)

    def test_add_colony_to_unregistered_raises(self, human, terran):
        tm = TurnManager()
        empire = make_empire(human, 'blue')
        empire.colonies = []
        with pytest.raises(ValueError):
            tm.add_colony(empire, make_colony(terran, human))

    def test_turn_increments(self, human, terran):
        tm = TurnManager()
        empire = make_empire(human, 'blue')
        empire.colonies = []
        tm.register_empire(empire)
        assert tm.turn == 0
        tm.process_turn()
        assert tm.turn == 1
        tm.process_turn()
        assert tm.turn == 2

    def test_bc_accumulates_in_treasury(self, human, terran):
        tm = TurnManager()
        empire = make_empire(human, 'blue')
        colony = make_colony(terran, human)
        empire.colonies = [colony]
        tm.register_empire(empire)

        result = tm.process_turn()
        assert empire.treasury == result.total_bc(empire)
        assert empire.treasury > 0

    def test_research_accumulates(self, psilon, terran):
        tm = TurnManager()
        empire = make_empire(psilon, 'red')
        colony = make_colony(terran, psilon, scientists=3, farmers=2, workers=1)
        empire.colonies = [colony]
        tm.register_empire(empire)

        tm.process_turn()
        assert empire.research_accumulated > 0

    def test_multiple_colonies_aggregate(self, human, psilon, terran):
        tm = TurnManager()
        empire = make_empire(human, 'green')
        c1 = make_colony(terran, human, name='A', farmers=3, workers=2, scientists=1)
        c2 = make_colony(terran, human, name='B', farmers=3, workers=2, scientists=1)
        empire.colonies = [c1, c2]
        tm.register_empire(empire)

        result = tm.process_turn()
        reports = result.colony_reports[empire]
        assert len(reports) == 2
        total_bc = sum(r['bc'] for r in reports)
        assert empire.treasury == total_bc

    def test_multiple_empires_independent(self, human, psilon, terran):
        tm = TurnManager()
        e1 = make_empire(human, 'blue')
        e2 = make_empire(psilon, 'red')
        e1.colonies = [make_colony(terran, human, name='X')]
        e2.colonies = [make_colony(terran, psilon, name='Y')]
        tm.register_empire(e1)
        tm.register_empire(e2)

        tm.process_turn()
        assert e1.treasury > 0
        assert e2.treasury > 0

    def test_add_colony_mid_game(self, human, terran):
        tm = TurnManager()
        empire = make_empire(human, 'blue')
        empire.colonies = [make_colony(terran, human, name='Home')]
        tm.register_empire(empire)
        tm.process_turn()
        treasury_after_1 = empire.treasury

        new_colony = make_colony(terran, human, name='New')
        tm.add_colony(empire, new_colony)
        tm.process_turn()

        # Second turn has 2 colonies contributing BC
        assert empire.treasury > treasury_after_1 * 2

    def test_turn_result_structure(self, human, terran):
        tm = TurnManager()
        empire = make_empire(human, 'blue')
        empire.colonies = [make_colony(terran, human)]
        tm.register_empire(empire)

        result = tm.process_turn()
        assert isinstance(result, TurnResult)
        assert result.turn_number == 1
        assert empire in result.colony_reports

    def test_result_helpers(self, human, terran):
        tm = TurnManager()
        empire = make_empire(human, 'blue')
        empire.colonies = [make_colony(terran, human, scientists=2, farmers=2, workers=2)]
        tm.register_empire(empire)

        result = tm.process_turn()
        assert result.total_bc(empire) >= 0
        assert result.total_research(empire) >= 0
        assert result.new_colonists(empire) >= 0


class TestTurnIntegration:
    """End-to-end: generate galaxy, place empires, run turns."""

    def test_full_game_start(self):
        g = Galaxy(size='tiny', num_players=2, seed=42)
        g.generate()
        human = CANONICAL_RACES['Human']
        psilon = CANONICAL_RACES['Psilon']
        e1 = Empire(human, 'Jones', 'blue')
        e2 = Empire(psilon, 'Psion', 'red')
        g.place_empires([e1, e2])

        tm = TurnManager()
        tm.register_empire(e1)
        tm.register_empire(e2)

        for _ in range(10):
            tm.process_turn()

        assert e1.treasury > 0
        assert e2.treasury > 0
        assert e2.research_accumulated > e1.research_accumulated  # Psilon have +1 science
        assert tm.turn == 10
