# vim: set ts=4 sw=4 et: coding=UTF-8

import math

# Speed in galaxy-coordinate units per turn.
# Nearby stars are ~25-75 units apart in a medium galaxy.
SHIP_SPEED = {
    'scout':       6.0,
    'colony_ship': 4.0,
}

SHIP_TYPES = tuple(SHIP_SPEED.keys())


class Ship:
    """
    A ship belonging to an empire.

    State machine
    -------------
    Orbiting  : destination is None; location is the current StarSystem.
    Traveling : destination is set; location remains the *departure* system
                until arrival (so scouts still "came from" a known system).

    Movement
    --------
    Call advance_turn() once per game turn (done by TurnManager).
    Returns True on the turn the ship arrives at its destination.
    """

    def __init__(self, ship_type, owner, location):
        if ship_type not in SHIP_TYPES:
            raise ValueError(f'Unknown ship type "{ship_type}". Choose from {SHIP_TYPES}')
        self.ship_type  = ship_type
        self.owner      = owner
        self.location   = location   # StarSystem — always the current or departure system
        self.destination = None      # StarSystem or None

        self._origin        = None   # departure system (set when order is given)
        self._turns_total   = 0
        self._turns_traveled = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def speed(self):
        return SHIP_SPEED[self.ship_type]

    @property
    def is_traveling(self):
        return self.destination is not None

    @property
    def is_orbiting(self):
        return self.destination is None

    @property
    def eta(self):
        """Turns remaining until arrival (0 when orbiting)."""
        return max(0, self._turns_total - self._turns_traveled)

    @property
    def travel_fraction(self):
        """
        Progress through the current journey: 0.0 = just departed, 1.0 = arrived.
        Always 0.0 when orbiting.
        """
        if not self.is_traveling or self._turns_total == 0:
            return 0.0
        return min(1.0, self._turns_traveled / self._turns_total)

    @property
    def galaxy_pos(self):
        """
        Interpolated (gx, gy) position in galaxy coordinates.
        Returns the departure→destination interpolation while traveling.
        """
        if not self.is_traveling or self._origin is None:
            return (self.location.x, self.location.y)
        t  = self.travel_fraction
        ox, oy = self._origin.x, self._origin.y
        dx, dy = self.destination.x, self.destination.y
        return (ox + t * (dx - ox), oy + t * (dy - oy))

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def set_destination(self, target):
        """
        Order this ship to travel to *target*.
        Silently ignored if the ship is already there.
        Cancels any existing travel order and restarts from current position.
        """
        if target is self.location and not self.is_traveling:
            return
        dist = math.hypot(
            target.x - self.location.x,
            target.y - self.location.y,
        )
        self._origin         = self.location
        self.destination     = target
        self._turns_total    = max(1, math.ceil(dist / self.speed))
        self._turns_traveled = 0

    def cancel_orders(self):
        """Return to orbiting the departure system."""
        self.destination     = None
        self._origin         = None
        self._turns_total    = 0
        self._turns_traveled = 0

    # ------------------------------------------------------------------
    # Turn advancement (called by TurnManager)
    # ------------------------------------------------------------------

    def advance_turn(self):
        """
        Move the ship one turn forward.
        Returns True if the ship arrived at its destination this turn.
        """
        if not self.is_traveling:
            return False

        self._turns_traveled += 1
        if self._turns_traveled >= self._turns_total:
            self.location        = self.destination
            self.destination     = None
            self._origin         = None
            self._turns_total    = 0
            self._turns_traveled = 0
            return True
        return False

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    @property
    def display_name(self):
        return f'{self.owner.race.name} {self.ship_type.replace("_", " ").title()}'

    def __repr__(self):
        state = (f'→ {self.destination.name} (ETA {self.eta})'
                 if self.is_traveling else f'@ {self.location.name}')
        return f'Ship({self.ship_type}, {self.owner.race.name}, {state})'
