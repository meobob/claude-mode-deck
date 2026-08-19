#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Genera le icone dell'indicatore di attivita'.

Stesso stampo di make_icons.py: fondo arrotondato, bordo interno chiaro, e per
ogni stato un colore E una forma diversa — il colore da solo non basta.

Le forme sono scelte per non somigliare a quelle dell'indicatore di modalita',
che sta sullo stesso deck: niente ottagono, niente chevron, e la spunta di
"finito" e' dentro un cerchio per distinguerla da quella di acceptEdits, che e'
verde pure lei.

Lo stato "aspetta" ha due fotogrammi, acceso e spento: e' l'unico che chiede
un'azione, e il plugin li alterna per farlo lampeggiare.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZE = 144
RADIUS = 22
OUT = Path(__file__).parent / "io.github.meobob.ccmode.sdPlugin" / "states"
OUT.mkdir(parents=True, exist_ok=True)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WHITE = (255, 255, 255, 235)


def base(color):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], RADIUS, fill=color)
    d.rounded_rectangle(
        [3, 3, SIZE - 4, SIZE - 4], RADIUS - 3, outline=(255, 255, 255, 45), width=3
    )
    return img, d


def glyph_anello(d, cy=58):
    """inattivo: un anello vuoto. Niente dentro, niente in corso."""
    d.ellipse([SIZE / 2 - 32, cy - 32, SIZE / 2 + 32, cy + 32], outline=WHITE, width=9)


def glyph_puntini(d, cy=58):
    """lavora: tre puntini, come un discorso in corso."""
    for i in (-1, 0, 1):
        x = SIZE / 2 + i * 34
        d.ellipse([x - 11, cy - 11, x + 11, cy + 11], fill=WHITE)


def glyph_esclamativo(d, cy=58):
    """aspetta: un punto esclamativo. Chiede qualcosa."""
    d.rounded_rectangle([SIZE / 2 - 8, cy - 34, SIZE / 2 + 8, cy + 8], 8, fill=WHITE)
    d.ellipse([SIZE / 2 - 9, cy + 18, SIZE / 2 + 9, cy + 36], fill=WHITE)


def glyph_spunta_cerchiata(d, cy=58):
    """finito: spunta dentro un cerchio, per non confonderla con acceptEdits."""
    d.ellipse([SIZE / 2 - 38, cy - 38, SIZE / 2 + 38, cy + 38], outline=WHITE, width=7)
    d.line([(SIZE / 2 - 19, cy + 1), (SIZE / 2 - 5, cy + 16), (SIZE / 2 + 21, cy - 17)],
           fill=WHITE, width=11, joint="curve")


SPECS = {
    "act-idle": ((58, 58, 64, 255),   glyph_anello),
    "act-work": ((26, 88, 168, 255),  glyph_puntini),
    "act-wait": ((176, 34, 27, 255),  glyph_esclamativo),
    "act-done": ((32, 116, 56, 255),  glyph_spunta_cerchiata),
    # fotogramma spento del lampeggio: stessa forma, fondo smorzato
    "act-wait-off": ((74, 22, 19, 255), glyph_esclamativo),
}

for name, (color, glyph) in SPECS.items():
    img, d = base(color)
    glyph(d)
    img.save(OUT / f"{name}.png")
    print("scritto", OUT / f"{name}.png")
