# vim: set ts=4 sw=4 et: coding=UTF-8

import math
import pygame

from .colors import (
    C_BG, C_PANEL, C_PANEL_BORDER, C_DIVIDER, C_BTN, C_BTN_HOVER,
    C_HEADER, C_TEXT, C_SUBTEXT, C_LABEL, C_WHITE,
    C_SELECTED, C_HOVER, C_ORION,
    STAR_COLOR, STAR_HIGHLIGHT, STAR_RADIUS, EMPIRE_COLOR,
)

# Layout constants
_W, _H       = 1100, 720
_MAP_W       = 800        # pixel width reserved for the galaxy map
_PANEL_X     = _MAP_W
_PANEL_W     = _W - _MAP_W
_MAP_PAD     = 28         # margin inside the map area
_FPS         = 30
_CLICK_RADIUS = 14        # max px from star centre to count as a click


class MainWindow:
    """
    Pygame galaxy map view.

    Controls
    --------
    Left-click star : select it (shows detail in panel)
    N / Return / Space : end turn
    Escape : quit
    """

    def __init__(self, galaxy, empires, player_empire, turn_manager):
        pygame.init()
        pygame.display.set_caption('OpenMOO2 – Galaxy Map')
        self._surf = pygame.display.set_mode((_W, _H))
        self._clock = pygame.time.Clock()

        self.galaxy = galaxy
        self.empires = empires
        self.player = player_empire
        self.turns = turn_manager

        self.selected = None
        self.hovered = None

        # Map area rect (within which stars are drawn)
        self._map_rect = pygame.Rect(
            _MAP_PAD, _MAP_PAD,
            _MAP_W - 2 * _MAP_PAD,
            _H - 2 * _MAP_PAD,
        )
        self._scale_x = self._map_rect.w / galaxy.width
        self._scale_y = self._map_rect.h / galaxy.height

        self._fonts = self._init_fonts()
        self._star_pos = {s: self._to_screen(s.x, s.y) for s in galaxy.systems}

        # "End Turn" button — set properly on first draw
        self._btn = pygame.Rect(_PANEL_X + 10, _H - 55, _PANEL_W - 20, 40)

        # Build empire-colour lookup for fast homeworld ring drawing
        self._empire_color = {e: EMPIRE_COLOR[e.color] for e in empires}

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        running = True
        while running:
            for ev in pygame.event.get():
                running = self._handle_event(ev, running)

            self._draw()
            pygame.display.flip()
            self._clock.tick(_FPS)

        pygame.quit()

    def _handle_event(self, ev, running):
        if ev.type == pygame.QUIT:
            return False
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                return False
            if ev.key in (pygame.K_n, pygame.K_RETURN, pygame.K_SPACE):
                self._end_turn()
        elif ev.type == pygame.MOUSEMOTION:
            mx, my = ev.pos
            self.hovered = self._nearest(mx, my) if mx < _MAP_W else None
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            mx, my = ev.pos
            if mx < _MAP_W:
                self.selected = self._nearest(mx, my)
            elif self._btn.collidepoint(ev.pos):
                self._end_turn()
        return running

    def _end_turn(self):
        self.turns.process_turn()

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def _to_screen(self, gx, gy):
        return (
            int(self._map_rect.left + gx * self._scale_x),
            int(self._map_rect.top  + gy * self._scale_y),
        )

    def _nearest(self, sx, sy, threshold=_CLICK_RADIUS):
        best, best_d = None, threshold
        for system, (px, py) in self._star_pos.items():
            d = math.hypot(sx - px, sy - py)
            if d < best_d:
                best_d, best = d, system
        return best

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self):
        self._surf.fill(C_BG)
        self._draw_stars()
        self._draw_map_border()
        self._draw_legend()
        self._draw_panel()

    def _draw_map_border(self):
        pygame.draw.rect(self._surf, C_PANEL_BORDER, (0, 0, _MAP_W, _H), 1)

    def _draw_stars(self):
        surf = self._surf
        font = self._fonts['sm']

        for system in self.galaxy.systems:
            pos  = self._star_pos[system]
            col  = STAR_COLOR[system.color]
            hi   = STAR_HIGHLIGHT[system.color]
            r    = STAR_RADIUS[system.color]

            # ── Orion aura ──────────────────────────────────────────
            if system.special == 'orion':
                pygame.draw.circle(surf, C_ORION, pos, r + 10, 1)
                pygame.draw.circle(surf, (*C_ORION[:3],), pos, r + 7, 1)

            # ── Homeworld ring (empire colour) ───────────────────────
            for emp in self.empires:
                if emp.homeworld is system:
                    ec = self._empire_color[emp]
                    pygame.draw.circle(surf, ec, pos, r + 7, 2)

            # ── Selection / hover ring ───────────────────────────────
            if system is self.selected:
                pygame.draw.circle(surf, C_SELECTED, pos, r + 4, 2)
            elif system is self.hovered:
                pygame.draw.circle(surf, C_HOVER, pos, r + 3, 1)

            # ── Star body ────────────────────────────────────────────
            pygame.draw.circle(surf, col, pos, r)
            if system.color != 'black':
                # bright inner core
                core_r = max(1, r - 2)
                pygame.draw.circle(surf, hi, pos, core_r)

            # Black-hole event-horizon ring
            if system.color == 'black':
                pygame.draw.circle(surf, (120, 40, 40), pos, r + 2, 1)

            # ── Star name label ──────────────────────────────────────
            # Always show for homeworlds / selected / hovered; others on map too
            lbl = font.render(system.name, True, C_LABEL)
            surf.blit(lbl, (pos[0] - lbl.get_width() // 2, pos[1] + r + 4))

    def _draw_legend(self):
        """Small star-class colour key in the bottom-left corner of the map."""
        font = self._fonts['sm']
        classes = [
            ('blue', 'Blue'), ('white', 'White'), ('yellow', 'Yellow'),
            ('orange', 'Orange'), ('red', 'Red'), ('gray', 'Gray'), ('black', 'Black Hole'),
        ]
        x0, y0 = _MAP_PAD + 4, _H - _MAP_PAD - len(classes) * 16 - 4
        for cls, label in classes:
            pygame.draw.circle(self._surf, STAR_COLOR[cls], (x0 + 5, y0 + 6), 4)
            txt = font.render(label, True, C_SUBTEXT)
            self._surf.blit(txt, (x0 + 14, y0))
            y0 += 16

    # ------------------------------------------------------------------
    # Right panel
    # ------------------------------------------------------------------

    def _draw_panel(self):
        surf = self._surf
        fnt  = self._fonts

        # Background
        pygame.draw.rect(surf, C_PANEL, (_PANEL_X, 0, _PANEL_W, _H))
        pygame.draw.rect(surf, C_PANEL_BORDER, (_PANEL_X, 0, _PANEL_W, _H), 1)

        x, y = _PANEL_X + 12, 12

        y = self._txt(x, y, 'OPEN MOO2', fnt['lg'], C_HEADER)
        y += 4
        y = self._txt(x, y, f'Turn  {self.turns.turn}', fnt['md'], C_TEXT)
        y += 8

        # ── Player empire ────────────────────────────────────────────
        y = self._txt(x, y, self.player.race.name.upper(), fnt['lg'], C_HEADER)
        y = self._txt(x, y, f'Government:  {self.player.race.government.title()}', fnt['sm'], C_TEXT)
        y = self._txt(x, y, f'Treasury:    {self.player.treasury} BC', fnt['sm'], C_TEXT)
        y = self._txt(x, y, f'Research:    {self.player.research_accumulated} RP', fnt['sm'], C_TEXT)
        y += 4
        pygame.draw.line(surf, C_DIVIDER, (x, y), (x + _PANEL_W - 24, y))
        y += 8

        # ── Selected / hovered system ────────────────────────────────
        system = self.selected or self.hovered
        if system:
            y = self._system_info(x, y, system, fnt)
        else:
            y = self._txt(x, y, 'Click a star to inspect', fnt['sm'], C_SUBTEXT)

        # ── End Turn button ──────────────────────────────────────────
        self._btn = pygame.Rect(_PANEL_X + 10, _H - 55, _PANEL_W - 20, 40)
        mx, my = pygame.mouse.get_pos()
        btn_col = C_BTN_HOVER if self._btn.collidepoint(mx, my) else C_BTN
        pygame.draw.rect(surf, btn_col, self._btn, border_radius=5)
        pygame.draw.rect(surf, C_PANEL_BORDER, self._btn, 1, border_radius=5)
        lbl = fnt['lg'].render('End Turn  [N / Enter]', True, C_HEADER)
        surf.blit(lbl, (
            self._btn.centerx - lbl.get_width() // 2,
            self._btn.centery - lbl.get_height() // 2,
        ))

    def _system_info(self, x, y, system, fnt):
        special_tag = f'  [{system.special}]' if system.special else ''
        y = self._txt(x, y, system.name + special_tag, fnt['lg'], C_HEADER)
        y = self._txt(x, y, f'{system.color.title()} Star', fnt['md'], C_TEXT)
        y += 6

        # Planets
        planets = [p for p in system.planets.values() if p is not None]
        if planets:
            y = self._txt(x, y, f'Planets ({len(planets)})', fnt['md'], C_TEXT)
            for p in planets:
                if p.kind == 'planet':
                    line = (f'{p.environment.title()} / {p.size.title()} / '
                            f'{p.mineral.title()}')
                    tag = ' [HW]' if p.homeworld else ''
                    y = self._txt(x + 8, y, '• ' + line + tag, fnt['sm'], C_SUBTEXT)
                elif p.kind == 'giant':
                    y = self._txt(x + 8, y, '• Gas Giant', fnt['sm'], C_SUBTEXT)
                else:
                    y = self._txt(x + 8, y, '• Asteroids', fnt['sm'], C_SUBTEXT)
        else:
            y = self._txt(x, y, 'No planets', fnt['sm'], C_SUBTEXT)
        y += 6

        # Colony info (if any empire has its homeworld here)
        for emp in self.empires:
            if emp.homeworld is system and emp.colonies:
                col = emp.colonies[0]
                ec  = EMPIRE_COLOR[emp.color]
                pygame.draw.line(self._surf, C_DIVIDER,
                                 (x, y), (x + _PANEL_W - 24, y))
                y += 6
                y = self._txt(x, y,
                              f'{emp.race.name} Colony', fnt['md'], ec)
                y = self._txt(x, y,
                              f'Pop  {col.population} / {col.max_population()}',
                              fnt['sm'], C_TEXT)
                y = self._txt(x, y,
                              f'  {col.farmers}f  {col.workers}w  {col.scientists}s',
                              fnt['sm'], C_SUBTEXT)
                fb = col.calculate_food_balance()
                fb_col = (100, 220, 100) if fb >= 0 else (220, 80, 80)
                y = self._txt(x, y,
                              f'Food   {col.calculate_food()}  ({fb:+d})',
                              fnt['sm'], fb_col)
                y = self._txt(x, y,
                              f'Prod   {col.calculate_industry()}',
                              fnt['sm'], C_TEXT)
                y = self._txt(x, y,
                              f'Research {col.calculate_research()} RP',
                              fnt['sm'], C_TEXT)
                y = self._txt(x, y,
                              f'BC     {col.calculate_bc()}',
                              fnt['sm'], C_TEXT)
        return y

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _txt(self, x, y, text, font, color):
        """Blit text and return next y position."""
        s = font.render(text, True, color)
        self._surf.blit(s, (x, y))
        return y + s.get_height() + 2

    @staticmethod
    def _init_fonts():
        candidates = ('segoeui', 'calibri', 'arial', 'helvetica', 'freesans')
        for name in candidates:
            try:
                return {
                    'lg': pygame.font.SysFont(name, 16, bold=True),
                    'md': pygame.font.SysFont(name, 13),
                    'sm': pygame.font.SysFont(name, 11),
                }
            except Exception:
                pass
        # Fallback to pygame built-in
        return {
            'lg': pygame.font.Font(None, 22),
            'md': pygame.font.Font(None, 18),
            'sm': pygame.font.Font(None, 15),
        }
