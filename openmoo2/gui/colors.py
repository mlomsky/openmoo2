# vim: set ts=4 sw=4 et: coding=UTF-8

# ── Background & UI chrome ────────────────────────────────────────────────
C_BG           = (  5,   5,  18)   # deep space
C_PANEL        = ( 12,  14,  30)   # right panel
C_PANEL_BORDER = ( 40,  55,  90)
C_DIVIDER      = ( 30,  40,  70)
C_BTN          = ( 22,  35,  65)
C_BTN_HOVER    = ( 35,  52,  95)

# ── Text ──────────────────────────────────────────────────────────────────
C_HEADER  = (160, 195, 255)
C_TEXT    = (190, 190, 210)
C_SUBTEXT = (120, 120, 150)
C_LABEL   = (130, 140, 170)   # star name labels on map
C_WHITE   = (255, 255, 255)

# ── Selection / hover ────────────────────────────────────────────────────
C_SELECTED = (255, 255, 255)
C_HOVER    = (160, 170, 230)
C_ORION    = (205, 170,  40)   # gold aura around Orion

# ── Star body colours ─────────────────────────────────────────────────────
STAR_COLOR = {
    'blue':   (110, 155, 255),
    'white':  (225, 232, 255),
    'yellow': (255, 220,  75),
    'orange': (255, 138,  55),
    'red':    (255,  65,  65),
    'gray':   (155, 158, 175),
    'black':  ( 45,  12,  12),
}

# Bright inner highlight (added on top of the star circle)
STAR_HIGHLIGHT = {
    'blue':   (180, 210, 255),
    'white':  (255, 255, 255),
    'yellow': (255, 245, 180),
    'orange': (255, 200, 130),
    'red':    (255, 150, 120),
    'gray':   (210, 212, 225),
    'black':  ( 80,  20,  20),
}

# Pixel radius of each star class
STAR_RADIUS = {
    'blue':   7,
    'white':  6,
    'yellow': 5,
    'orange': 5,
    'red':    4,
    'gray':   3,
    'black':  7,
}

# ── Empire colours (for homeworld rings) ─────────────────────────────────
EMPIRE_COLOR = {
    'red':    (230,  55,  55),
    'yellow': (215, 200,  50),
    'green':  ( 50, 205,  80),
    'white':  (210, 215, 230),
    'blue':   ( 60, 115, 235),
    'brown':  (140,  85,  40),
    'purple': (165,  55, 215),
    'orange': (230, 120,  35),
}
