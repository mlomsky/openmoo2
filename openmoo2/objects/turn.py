# vim: set ts=4 sw=4 et: coding=UTF-8


class TurnResult:
    """Summary of everything that happened in one game turn."""

    def __init__(self, turn_number):
        self.turn_number = turn_number
        self.colony_reports = {}   # empire → [colony report dict, ...]
        self.arrivals = {}         # empire → [Ship, ...]  (ships that arrived this turn)

    def total_research(self, empire):
        return sum(r['research'] for r in self.colony_reports.get(empire, []))

    def total_bc(self, empire):
        return sum(r['bc'] for r in self.colony_reports.get(empire, []))

    def new_colonists(self, empire):
        return sum(r['new_colonists'] for r in self.colony_reports.get(empire, []))


class TurnManager:
    """
    Drives the game loop.

    Register empires and their colonies, then call process_turn() once per
    game turn. Each turn:
      1. Every colony calculates its outputs and applies population growth.
      2. BC from each colony is added to the empire's treasury.
      3. Research from each colony is added to the empire's research_accumulated.
    """

    def __init__(self):
        self.turn = 0
        self._empires = []

    def register_empire(self, empire):
        """Add an empire to the turn order."""
        if empire in self._empires:
            raise ValueError(f'Empire {empire!r} already registered')
        self._empires.append(empire)

    def add_colony(self, empire, colony):
        """Add a colony to an already-registered empire mid-game."""
        if empire not in self._empires:
            raise ValueError(f'Empire {empire!r} not registered')
        empire.colonies.append(colony)

    def process_turn(self):
        """Advance the game by one turn and return a TurnResult."""
        self.turn += 1
        result = TurnResult(self.turn)

        for empire in self._empires:
            # Colonies — read from empire.colonies so mid-game additions are live
            reports = []
            for colony in empire.colonies:
                report = colony.process_turn()
                empire.treasury += report['bc']
                empire.research_accumulated += report['research']
                reports.append(report)
            result.colony_reports[empire] = reports

            # Ships
            arrived = []
            for ship in empire.ships:
                if ship.advance_turn():
                    arrived.append(ship)
                    empire.explored_systems.add(ship.location.name)
            result.arrivals[empire] = arrived

        return result

    @property
    def empires(self):
        return list(self._empires)
