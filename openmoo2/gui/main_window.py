# vim: set ts=4 sw=4 et: coding=UTF-8

import math
import pygame

from .colors import (
    C_BG, C_PANEL, C_PANEL_BORDER, C_DIVIDER, C_BTN, C_BTN_HOVER,
    C_HEADER, C_TEXT, C_SUBTEXT, C_LABEL, C_WHITE,
    C_SELECTED, C_HOVER, C_ORION,
    STAR_COLOR, STAR_HIGHLIGHT, STAR_RADIUS, EMPIRE_COLOR,
)
from openmoo2.objects.colonization import can_colonize, best_planet, colonize

# ── Layout ────────────────────────────────────────────────────────────────
_W, _H        = 1100, 720
_MAP_W        = 800
_PANEL_X      = _MAP_W
_PANEL_W      = _W - _MAP_W
_MAP_PAD      = 28
_FPS          = 30
_STAR_HIT     = 14      # px radius for star click detection
_SHIP_HIT     = 10      # px radius for ship click detection

# Ship icon colours
_C_SHIP_SELECT = (255, 255,  80)   # yellow ring on selected ship
_C_FLIGHT_LINE = ( 60,  90, 150)   # colour of in-transit flight path line
_C_ETA_TEXT    = (160, 210, 160)   # ETA label colour

# Ship shape sizes (half-width of the icon)
_SHIP_ICON_R = {'scout': 5, 'colony_ship': 6}

# Orbit offset slots so multiple ships at the same star don't overlap
_ORBIT_OFFSETS = [(14, -10), (14, 2), (14, 14), (-14, -10), (-14, 2), (-14, 14)]


def _draw_triangle(surf, color, cx, cy, r, outline=False):
    """Draw an upward-pointing triangle centred at (cx, cy)."""
    pts = [(cx, cy - r), (cx - r, cy + r), (cx + r, cy + r)]
    if outline:
        pygame.draw.polygon(surf, color, pts, 1)
    else:
        pygame.draw.polygon(surf, color, pts)


def _draw_diamond(surf, color, cx, cy, r, outline=False):
    """Draw a diamond centred at (cx, cy)."""
    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    if outline:
        pygame.draw.polygon(surf, color, pts, 1)
    else:
        pygame.draw.polygon(surf, color, pts)


class MainWindow:
    """
    Pygame galaxy map view.

    Controls
    --------
    Left-click star       : select system (or issue move order if a ship is selected)
    Left-click ship icon  : select ship (enters move-order mode)
    Click ship name (panel): select ship
    Right-click / Escape  : cancel ship selection
    N / Return / Space    : end turn
    Escape (no ship sel.) : quit
    """

    def __init__(self, galaxy, empires, player_empire, turn_manager):
        pygame.init()
        pygame.display.set_caption('OpenMOO2 – Galaxy Map')
        self._surf  = pygame.display.set_mode((_W, _H))
        self._clock = pygame.time.Clock()

        self.galaxy  = galaxy
        self.empires = empires
        self.player  = player_empire
        self.turns   = turn_manager

        self.selected        = None    # selected StarSystem
        self.hovered         = None    # hovered StarSystem
        self.selected_ship   = None    # Ship awaiting move order
        self._last_arrivals  = []      # ships that arrived last turn (for brief highlight)
        self._colonize_btn   = None    # Rect of Colonize button (set each draw)

        self._map_rect = pygame.Rect(
            _MAP_PAD, _MAP_PAD,
            _MAP_W - 2 * _MAP_PAD,
            _H - 2 * _MAP_PAD,
        )
        self._sx = self._map_rect.w / galaxy.width
        self._sy = self._map_rect.h / galaxy.height

        self._fonts      = self._init_fonts()
        self._star_pos   = {s: self._to_screen(s.x, s.y) for s in galaxy.systems}
        self._empire_col = {e: EMPIRE_COLOR[e.color] for e in empires}

        # "End Turn" button — updated on every draw
        self._btn = pygame.Rect(_PANEL_X + 10, _H - 55, _PANEL_W - 20, 40)

    # ── Main loop ──────────────────────────────────────────────────────────

    def run(self):
        running = True
        while running:
            for ev in pygame.event.get():
                running = self._handle(ev, running)
            self._draw()
            pygame.display.flip()
            self._clock.tick(_FPS)
        pygame.quit()

    def _handle(self, ev, running):
        if ev.type == pygame.QUIT:
            return False

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                if self.selected_ship:
                    self.selected_ship = None   # cancel order mode
                else:
                    return False
            elif ev.key in (pygame.K_n, pygame.K_RETURN, pygame.K_SPACE):
                self._end_turn()

        elif ev.type == pygame.MOUSEMOTION:
            mx, my = ev.pos
            self.hovered = self._nearest_star(mx, my) if mx < _MAP_W else None

        elif ev.type == pygame.MOUSEBUTTONDOWN:
            mx, my = ev.pos
            if ev.button == 3:                          # right-click cancels
                self.selected_ship = None
            elif ev.button == 1:
                if mx >= _MAP_W:                        # panel click
                    if self._btn.collidepoint(ev.pos):
                        self._end_turn()
                    elif self._colonize_btn and self._colonize_btn.collidepoint(ev.pos):
                        self._do_colonize()
                else:                                   # map click
                    self._handle_map_click(mx, my)

        return running

    def _handle_map_click(self, mx, my):
        # Check ships first (higher priority than stars)
        ship = self._nearest_ship(mx, my)
        if ship and ship.owner is self.player:
            self.selected_ship = ship
            return

        star = self._nearest_star(mx, my)
        if self.selected_ship:
            # Issue move order if clicking a different system
            if star and star is not self.selected_ship.location:
                self.selected_ship.set_destination(star)
            self.selected_ship = None
        else:
            self.selected = star

    def _end_turn(self):
        result = self.turns.process_turn()
        self._last_arrivals = result.arrivals.get(self.player, [])

    def _do_colonize(self):
        """Colonize the best available planet in the selected system."""
        system = self.selected
        if system is None or not can_colonize(self.player, system):
            return
        planet = best_planet(self.player, system)
        if planet:
            colonize(self.player, system, planet)

    # ── Coordinate helpers ─────────────────────────────────────────────────

    def _to_screen(self, gx, gy):
        return (
            int(self._map_rect.left + gx * self._sx),
            int(self._map_rect.top  + gy * self._sy),
        )

    def _nearest_star(self, sx, sy, threshold=_STAR_HIT):
        best, best_d = None, threshold
        for system, (px, py) in self._star_pos.items():
            d = math.hypot(sx - px, sy - py)
            if d < best_d:
                best_d, best = d, system
        return best

    def _nearest_ship(self, sx, sy, threshold=_SHIP_HIT):
        """Return the nearest ship icon on the map within threshold px."""
        best, best_d = None, threshold
        for emp in self.empires:
            for ship in emp.ships:
                gx, gy = ship.galaxy_pos
                px, py = self._to_screen(gx, gy)
                # Apply orbit slot offset for orbiting ships
                if ship.is_orbiting:
                    idx = emp.ships.index(ship) % len(_ORBIT_OFFSETS)
                    ox, oy = _ORBIT_OFFSETS[idx]
                    px, py = px + ox, py + oy
                d = math.hypot(sx - px, sy - py)
                if d < best_d:
                    best_d, best = d, ship
        return best

    # ── Drawing ────────────────────────────────────────────────────────────

    def _draw(self):
        self._surf.fill(C_BG)
        self._draw_flight_lines()
        self._draw_stars()
        self._draw_ships()
        self._draw_map_border()
        self._draw_legend()
        self._draw_panel()

    def _draw_map_border(self):
        pygame.draw.rect(self._surf, C_PANEL_BORDER, (0, 0, _MAP_W, _H), 1)

    def _draw_flight_lines(self):
        """Draw dashed lines from ship origin to destination for traveling ships."""
        for emp in self.empires:
            for ship in emp.ships:
                if not ship.is_traveling or ship._origin is None:
                    continue
                p1 = self._to_screen(ship._origin.x,      ship._origin.y)
                p2 = self._to_screen(ship.destination.x,  ship.destination.y)
                # Dashed line
                self._draw_dashed_line(p1, p2, _C_FLIGHT_LINE)

    def _draw_dashed_line(self, p1, p2, color, dash=8, gap=5):
        dx, dy  = p2[0] - p1[0], p2[1] - p1[1]
        length  = math.hypot(dx, dy)
        if length == 0:
            return
        ux, uy  = dx / length, dy / length
        pos     = 0.0
        drawing = True
        while pos < length:
            seg_end = min(pos + (dash if drawing else gap), length)
            if drawing:
                x1 = int(p1[0] + ux * pos)
                y1 = int(p1[1] + uy * pos)
                x2 = int(p1[0] + ux * seg_end)
                y2 = int(p1[1] + uy * seg_end)
                pygame.draw.line(self._surf, color, (x1, y1), (x2, y2), 1)
            pos    += dash if drawing else gap
            drawing = not drawing

    def _draw_stars(self):
        surf = self._surf
        font = self._fonts['sm']

        for system in self.galaxy.systems:
            pos = self._star_pos[system]
            col = STAR_COLOR[system.color]
            hi  = STAR_HIGHLIGHT[system.color]
            r   = STAR_RADIUS[system.color]

            # Orion aura
            if system.special == 'orion':
                pygame.draw.circle(surf, C_ORION, pos, r + 10, 1)
                pygame.draw.circle(surf, C_ORION, pos, r +  7, 1)

            # Homeworld ring
            for emp in self.empires:
                if emp.homeworld is system:
                    pygame.draw.circle(surf, self._empire_col[emp], pos, r + 7, 2)

            # Destination highlight (when a ship is selected)
            if self.selected_ship and system is not self.selected_ship.location:
                pygame.draw.circle(surf, (50, 80, 140), pos, r + 5, 1)

            # Selection / hover ring
            if system is self.selected:
                pygame.draw.circle(surf, C_SELECTED, pos, r + 4, 2)
            elif system is self.hovered:
                pygame.draw.circle(surf, C_HOVER, pos, r + 3, 1)

            # Star body + core highlight
            pygame.draw.circle(surf, col, pos, r)
            if system.color != 'black':
                pygame.draw.circle(surf, hi, pos, max(1, r - 2))
            else:
                pygame.draw.circle(surf, (120, 40, 40), pos, r + 2, 1)

            # Name label
            lbl = font.render(system.name, True, C_LABEL)
            surf.blit(lbl, (pos[0] - lbl.get_width() // 2, pos[1] + r + 4))

    def _draw_ships(self):
        surf = self._surf

        for emp in self.empires:
            ec  = self._empire_col[emp]
            for idx, ship in enumerate(emp.ships):
                gx, gy = ship.galaxy_pos
                px, py = self._to_screen(gx, gy)

                if ship.is_orbiting:
                    ox, oy = _ORBIT_OFFSETS[idx % len(_ORBIT_OFFSETS)]
                    px, py = px + ox, py + oy

                r = _SHIP_ICON_R[ship.ship_type]

                # Selected ship highlight
                if ship is self.selected_ship:
                    _draw_diamond(surf, _C_SHIP_SELECT, px, py, r + 4, outline=True)
                # Recently arrived highlight
                elif ship in self._last_arrivals:
                    _draw_diamond(surf, (200, 255, 200), px, py, r + 3, outline=True)

                # Ship icon: triangle = scout, diamond = colony ship
                if ship.ship_type == 'scout':
                    _draw_triangle(surf, ec, px, py, r)
                else:
                    _draw_diamond(surf, ec, px, py, r)

                # ETA label for traveling ships
                if ship.is_traveling:
                    eta_lbl = self._fonts['sm'].render(str(ship.eta), True, _C_ETA_TEXT)
                    surf.blit(eta_lbl, (px + r + 2, py - eta_lbl.get_height() // 2))

    def _draw_legend(self):
        font = self._fonts['sm']
        classes = [
            ('blue', 'Blue'), ('white', 'White'), ('yellow', 'Yellow'),
            ('orange', 'Orange'), ('red', 'Red'), ('gray', 'Gray'),
            ('black', 'Black Hole'),
        ]
        x0, y0 = _MAP_PAD + 4, _H - _MAP_PAD - len(classes) * 16 - 4
        for cls, label in classes:
            pygame.draw.circle(self._surf, STAR_COLOR[cls], (x0 + 5, y0 + 6), 4)
            self._surf.blit(font.render(label, True, C_SUBTEXT), (x0 + 14, y0))
            y0 += 16

    # ── Panel ──────────────────────────────────────────────────────────────

    def _draw_panel(self):
        surf = self._surf
        fnt  = self._fonts

        pygame.draw.rect(surf, C_PANEL,        (_PANEL_X, 0, _PANEL_W, _H))
        pygame.draw.rect(surf, C_PANEL_BORDER, (_PANEL_X, 0, _PANEL_W, _H), 1)

        x, y = _PANEL_X + 12, 12

        y = self._txt(x, y, 'OPEN MOO2',          fnt['lg'], C_HEADER)
        y += 4
        y = self._txt(x, y, f'Turn  {self.turns.turn}', fnt['md'], C_TEXT)
        y += 8

        # Empire
        y = self._txt(x, y, self.player.race.name.upper(), fnt['lg'], C_HEADER)
        y = self._txt(x, y, f'Treasury   {self.player.treasury} BC',      fnt['sm'], C_TEXT)
        y = self._txt(x, y, f'Research   {self.player.research_accumulated} RP', fnt['sm'], C_TEXT)
        y += 4
        pygame.draw.line(surf, C_DIVIDER, (x, y), (x + _PANEL_W - 24, y))
        y += 8

        # Ships summary (if a ship is selected, show move-order prompt)
        if self.selected_ship:
            y = self._txt(x, y, 'SELECT DESTINATION', fnt['md'], _C_SHIP_SELECT)
            y = self._txt(x, y, self.selected_ship.display_name, fnt['sm'], C_TEXT)
            y = self._txt(x, y, 'Click a star to issue order', fnt['sm'], C_SUBTEXT)
            y = self._txt(x, y, 'Right-click / Esc to cancel', fnt['sm'], C_SUBTEXT)
        else:
            y = self._ship_list(x, y, fnt)

        pygame.draw.line(surf, C_DIVIDER, (x, y), (x + _PANEL_W - 24, y))
        y += 8

        # System detail
        system = self.selected or self.hovered
        if system:
            y = self._system_info(x, y, system, fnt)
        else:
            y = self._txt(x, y, 'Click a star to inspect', fnt['sm'], C_SUBTEXT)

        # ── Colonize button (shown when opportunity exists) ──────────────
        mx, my = pygame.mouse.get_pos()
        system = self.selected or self.hovered
        if system and can_colonize(self.player, system):
            planet = best_planet(self.player, system)
            env    = planet.environment.title() if planet else '?'
            self._colonize_btn = pygame.Rect(_PANEL_X + 10, _H - 105, _PANEL_W - 20, 40)
            c_bc = C_BTN_HOVER if self._colonize_btn.collidepoint(mx, my) else (20, 55, 30)
            pygame.draw.rect(surf, c_bc, self._colonize_btn, border_radius=5)
            pygame.draw.rect(surf, (50, 160, 70), self._colonize_btn, 1, border_radius=5)
            c_lbl = fnt['lg'].render(f'Colonize  [{env}]', True, (120, 240, 130))
            surf.blit(c_lbl, (
                self._colonize_btn.centerx - c_lbl.get_width() // 2,
                self._colonize_btn.centery - c_lbl.get_height() // 2,
            ))
        else:
            self._colonize_btn = None

        # ── End Turn button ──────────────────────────────────────────
        self._btn = pygame.Rect(_PANEL_X + 10, _H - 55, _PANEL_W - 20, 40)
        bc      = C_BTN_HOVER if self._btn.collidepoint(mx, my) else C_BTN
        pygame.draw.rect(surf, bc, self._btn, border_radius=5)
        pygame.draw.rect(surf, C_PANEL_BORDER, self._btn, 1, border_radius=5)
        lbl = fnt['lg'].render('End Turn  [N]', True, C_HEADER)
        surf.blit(lbl, (
            self._btn.centerx - lbl.get_width() // 2,
            self._btn.centery - lbl.get_height() // 2,
        ))

    def _ship_list(self, x, y, fnt):
        """List player ships with status; clicking a name selects the ship."""
        y = self._txt(x, y, 'YOUR SHIPS', fnt['md'], C_HEADER)
        if not self.player.ships:
            return self._txt(x, y, '  (none)', fnt['sm'], C_SUBTEXT)

        for ship in self.player.ships:
            if ship.is_traveling:
                status = f'  ETA {ship.eta}t -> {ship.destination.name}'
                col = _C_ETA_TEXT
            else:
                status = f'  @ {ship.location.name}'
                col = C_SUBTEXT

            # Clickable ship name
            name_lbl = fnt['sm'].render(ship.display_name, True, C_TEXT)
            stat_lbl = fnt['sm'].render(status, True, col)
            self._surf.blit(name_lbl, (x + 4, y))
            y += name_lbl.get_height() + 1
            self._surf.blit(stat_lbl, (x + 4, y))
            y += stat_lbl.get_height() + 4

            # Store a rect for click detection (used in panel-click handler)
            if not hasattr(self, '_ship_btn_rects'):
                self._ship_btn_rects = {}
            self._ship_btn_rects[ship] = pygame.Rect(
                x, y - name_lbl.get_height() * 2 - 5,
                _PANEL_W - 24, name_lbl.get_height() * 2 + 4
            )

        return y

    def _system_info(self, x, y, system, fnt):
        special = f'  [{system.special}]' if system.special else ''
        y = self._txt(x, y, system.name + special, fnt['lg'], C_HEADER)
        y = self._txt(x, y, f'{system.color.title()} Star', fnt['md'], C_TEXT)
        y += 4

        planets = [p for p in system.planets.values() if p is not None]
        if planets:
            y = self._txt(x, y, f'Planets ({len(planets)})', fnt['md'], C_TEXT)
            for p in planets:
                if p.kind == 'planet':
                    line = (f'{p.environment.title()} / {p.size.title()} /'
                            f' {p.mineral.title()}')
                    tag = ' [HW]' if p.homeworld else ''
                    y = self._txt(x + 8, y, '• ' + line + tag, fnt['sm'], C_SUBTEXT)
                elif p.kind == 'giant':
                    y = self._txt(x + 8, y, '• Gas Giant', fnt['sm'], C_SUBTEXT)
                else:
                    y = self._txt(x + 8, y, '• Asteroids', fnt['sm'], C_SUBTEXT)
        else:
            y = self._txt(x, y, 'No planets', fnt['sm'], C_SUBTEXT)
        y += 4

        # Colony info
        for emp in self.empires:
            if emp.homeworld is system and emp.colonies:
                col = emp.colonies[0]
                ec  = EMPIRE_COLOR[emp.color]
                pygame.draw.line(self._surf, C_DIVIDER,
                                 (x, y), (x + _PANEL_W - 24, y))
                y += 4
                y = self._txt(x, y, f'{emp.race.name} Colony', fnt['md'], ec)
                y = self._txt(x, y, f'Pop  {col.population}/{col.max_population()}', fnt['sm'], C_TEXT)
                y = self._txt(x, y,
                              f'  {col.farmers}f {col.workers}w {col.scientists}s',
                              fnt['sm'], C_SUBTEXT)
                fb    = col.calculate_food_balance()
                fb_c  = (100, 220, 100) if fb >= 0 else (220, 80, 80)
                y = self._txt(x, y, f'Food {col.calculate_food()} ({fb:+d})', fnt['sm'], fb_c)
                y = self._txt(x, y, f'Prod {col.calculate_industry()}',        fnt['sm'], C_TEXT)
                y = self._txt(x, y, f'Research {col.calculate_research()} RP', fnt['sm'], C_TEXT)
                y = self._txt(x, y, f'BC   {col.calculate_bc()}',              fnt['sm'], C_TEXT)

        # Ships currently at this system
        ships_here = [
            s for emp in self.empires for s in emp.ships
            if s.is_orbiting and s.location is system
        ]
        if ships_here:
            y += 4
            pygame.draw.line(self._surf, C_DIVIDER, (x, y), (x + _PANEL_W - 24, y))
            y += 4
            y = self._txt(x, y, 'Ships in orbit', fnt['md'], C_TEXT)
            for s in ships_here:
                ec = EMPIRE_COLOR[s.owner.color]
                y = self._txt(x + 8, y, f'• {s.display_name}', fnt['sm'], ec)

        return y

    # ── Helpers ────────────────────────────────────────────────────────────

    def _txt(self, x, y, text, font, color):
        s = font.render(text, True, color)
        self._surf.blit(s, (x, y))
        return y + s.get_height() + 2

    @staticmethod
    def _init_fonts():
        for name in ('segoeui', 'calibri', 'arial', 'helvetica', 'freesans'):
            try:
                return {
                    'lg': pygame.font.SysFont(name, 16, bold=True),
                    'md': pygame.font.SysFont(name, 13),
                    'sm': pygame.font.SysFont(name, 11),
                }
            except Exception:
                pass
        return {
            'lg': pygame.font.Font(None, 22),
            'md': pygame.font.Font(None, 18),
            'sm': pygame.font.Font(None, 15),
        }
