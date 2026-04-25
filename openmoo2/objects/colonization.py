# vim: set ts=4 sw=4 et: coding=UTF-8

from .colony import Colony, _TERRAIN_MULT_AQUATIC, _TERRAIN_MULT_DEFAULT

# Starting population for a new colony (farmers, workers, scientists)
_START_POP = (1, 0, 1)


def colonizable_planets(system):
    """
    Return a list of planets in *system* that can accept a new colony:
    regular planet kind, not already occupied (planet.colony is None).
    """
    return [
        p for p in system.planets.values()
        if p is not None and p.kind == 'planet' and p.colony is None
    ]


def can_colonize(empire, system):
    """
    True if *empire* has a colony ship orbiting *system* AND at least one
    free planet is available there.
    """
    has_ship = any(
        s for s in empire.ships
        if s.ship_type == 'colony_ship'
        and s.is_orbiting
        and s.location is system
    )
    return has_ship and bool(colonizable_planets(system))


def best_planet(empire, system):
    """
    Return the most valuable colonizable planet for *empire*'s race,
    ranked by the terrain multiplier (higher = better environment).
    Returns None if no colonizable planet exists.
    """
    planets = colonizable_planets(system)
    if not planets:
        return None
    mults = _TERRAIN_MULT_AQUATIC if empire.race.aquatic else _TERRAIN_MULT_DEFAULT

    def score(p):
        return mults.get(p.environment, 25)

    return max(planets, key=score)


def colonize(empire, system, planet):
    """
    Establish a new colony on *planet* in *system*.

    Effects
    -------
    - Consumes one colony ship belonging to *empire* that is orbiting *system*.
    - Creates a Colony with starting population (_START_POP).
    - Sets planet.colony to the new Colony object (marks the planet occupied).
    - Appends the Colony to empire.colonies.
    - Adds the system name to empire.explored_systems.

    Returns the new Colony.

    Raises
    ------
    ValueError — if the planet is already colonized, or no colony ship is present.
    """
    if planet.colony is not None:
        raise ValueError(f'Planet already has a colony')

    ship = next(
        (s for s in empire.ships
         if s.ship_type == 'colony_ship'
         and s.is_orbiting
         and s.location is system),
        None,
    )
    if ship is None:
        raise ValueError(f'No colony ship orbiting {system.name}')

    empire.ships.remove(ship)

    colony = Colony(planet, empire.race, name=system.name)
    max_pop = colony.max_population()
    # Distribute starting colonists: farmer first, then scientist, respect max_pop
    farmers    = min(1, max_pop)
    scientists = min(1, max(0, max_pop - farmers))
    workers    = min(0, max_pop - farmers - scientists)
    colony.set_population(farmers, workers, scientists)

    planet.colony = colony
    empire.colonies.append(colony)
    empire.explored_systems.add(system.name)

    return colony
