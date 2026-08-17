#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Genera le icone PNG degli stati del plugin Claude Code Mode.

Ogni stato ha un colore E una forma diversa: il colore da solo non basta
(daltonismo, schermi piccoli, luce forte sulla scrivania).
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
    # bordo interno chiaro, aiuta a staccare il tasto dallo sfondo nero
    d.rounded_rectangle(
        [3, 3, SIZE - 4, SIZE - 4], RADIUS - 3, outline=(255, 255, 255, 45), width=3
    )
    return img, d


def glyph_text(d, text, size=64, cy=58):
    font = ImageFont.truetype(FONT_PATH, size)
    d.text((SIZE / 2, cy), text, font=font, fill=WHITE, anchor="mm")


def glyph_check(d, cy=58):
    d.line([(44, cy + 2), (64, cy + 22), (102, cy - 22)], fill=WHITE, width=13,
           joint="curve")


def glyph_octagon(d, cy=58, r=34):
    import math
    pts = []
    for i in range(8):
        a = math.radians(22.5 + i * 45)
        pts.append((SIZE / 2 + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, outline=WHITE, width=10)


def glyph_lines(d, cy=58):
    for i, w in enumerate((66, 52, 38)):
        y = cy - 22 + i * 22
        x0 = SIZE / 2 - w / 2
        d.rounded_rectangle([x0, y - 5, x0 + w, y + 5], 5, fill=WHITE)


def glyph_chevrons(d, n, cy=58):
    total_w = 26 * n
    x = SIZE / 2 - total_w / 2 + 4
    for _ in range(n):
        d.line([(x, cy - 22), (x + 18, cy), (x, cy + 22)], fill=WHITE, width=11,
               joint="curve")
        x += 26


def glyph_warning(d, cy=58):
    d.polygon([(SIZE / 2, cy - 32), (SIZE / 2 + 38, cy + 28), (SIZE / 2 - 38, cy + 28)],
              outline=WHITE, width=9)
    d.rounded_rectangle([SIZE / 2 - 5, cy - 8, SIZE / 2 + 5, cy + 12], 5, fill=WHITE)
    d.ellipse([SIZE / 2 - 6, cy + 17, SIZE / 2 + 6, cy + 29], fill=WHITE)


SPECS = {
    "unknown":     ((58, 58, 64, 255),   lambda d: glyph_text(d, "?", 76)),
    "manual":      ((176, 34, 27, 255),  glyph_octagon),
    "plan":        ((26, 88, 168, 255),  glyph_lines),
    "acceptedits": ((32, 116, 56, 255),  glyph_check),
    "auto":        ((186, 112, 0, 255),  lambda d: glyph_chevrons(d, 2)),
    "dontask":     ((150, 88, 0, 255),   lambda d: glyph_chevrons(d, 3)),
    "bypass":      ((136, 32, 160, 255), glyph_warning),
}

for name, (color, draw_glyph) in SPECS.items():
    img, d = base(color)
    draw_glyph(d)
    img.save(OUT / f"{name}.png")
    print("scritto", OUT / f"{name}.png")

# icona del plugin / della categoria
img, d = base((40, 40, 46, 255))
glyph_text(d, "CC", 56, cy=SIZE / 2)
img.save(OUT.parent / "icon.png")
print("scritto", OUT.parent / "icon.png")
