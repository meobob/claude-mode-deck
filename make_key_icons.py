#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Genera le icone dei tasti per il layout a tre pagine dell'AKP03E.

Un colore per pagina, cosi' capisci dove sei senza leggere:
  pagina 1 (guida)        verde-acqua
  pagina 2 (contesto)     viola
  pagina 3 (regolazioni)  grigio ardesia

Ogni icona ha un simbolo grande e la scorciatoia in piccolo sotto: il simbolo
si legge di colpo, la scorciatoia serve finche' non l'hai in memoria.
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZE = 144
RADIUS = 22
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WHITE = (255, 255, 255, 238)
DIM = (255, 255, 255, 165)

OUT = Path(__file__).parent / "keys"
PAGES = {
    "1-guida": (26, 106, 96, 255),
    "2-contesto": (78, 62, 148, 255),
    "3-regolazioni": (62, 66, 76, 255),
}
for name in PAGES:
    (OUT / name).mkdir(parents=True, exist_ok=True)

CY = 56  # centro verticale del simbolo


def base(color):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], RADIUS, fill=color)
    d.rounded_rectangle([3, 3, SIZE - 4, SIZE - 4], RADIUS - 3,
                        outline=(255, 255, 255, 42), width=3)
    return img, d


def caption(d, text):
    f = ImageFont.truetype(FONT, 17)
    d.text((SIZE / 2, 116), text, font=f, fill=DIM, anchor="mm")


# ------------------------------------------------------------------ glifi --

def g_mic(d):
    d.rounded_rectangle([60, CY - 32, 84, CY + 4], 12, fill=WHITE)
    d.arc([48, CY - 12, 96, CY + 24], 0, 180, fill=WHITE, width=8)
    d.line([(72, CY + 24), (72, CY + 36)], fill=WHITE, width=8)


def g_cycle(d):
    d.arc([42, CY - 30, 102, CY + 30], 40, 320, fill=WHITE, width=9)
    d.polygon([(96, CY - 30), (110, CY - 6), (82, CY - 8)], fill=WHITE)


def g_stop(d):
    d.rounded_rectangle([48, CY - 24, 96, CY + 24], 6, fill=WHITE)


def g_rewind(d):
    for x in (46, 78):
        d.polygon([(x + 28, CY - 24), (x + 28, CY + 24), (x, CY)], fill=WHITE)


def g_task(d):
    for i in range(3):
        y = CY - 24 + i * 24
        d.line([(46, y), (54, y + 8), (68, y - 8)], fill=WHITE, width=7,
               joint="curve")
        d.rounded_rectangle([80, y - 4, 106, y + 4], 4, fill=WHITE)


def g_lines(d):
    for i, w in enumerate((64, 48, 64, 36)):
        y = CY - 27 + i * 18
        d.rounded_rectangle([46, y - 4, 46 + w, y + 4], 4,
                            fill=WHITE if i % 2 == 0 else DIM)


def g_search(d):
    d.ellipse([44, CY - 32, 92, CY + 16], outline=WHITE, width=9)
    d.line([(88, CY + 12), (104, CY + 30)], fill=WHITE, width=10)


def g_pencil(d):
    d.polygon([(48, CY + 30), (54, CY + 8), (92, CY - 30), (104, CY - 18),
               (66, CY + 20)], fill=WHITE)
    d.polygon([(48, CY + 30), (54, CY + 22), (58, CY + 26)], fill=DIM)


def g_stash(d):
    d.rounded_rectangle([44, CY - 30, 100, CY - 12], 4, fill=WHITE)
    d.rounded_rectangle([50, CY - 6, 94, CY + 30], 4, outline=WHITE, width=8)


def g_play(d):
    d.polygon([(54, CY - 28), (54, CY + 28), (100, CY)], fill=WHITE)


def g_bubble(d):
    d.rounded_rectangle([40, CY - 28, 104, CY + 14], 10, fill=WHITE)
    d.polygon([(56, CY + 14), (56, CY + 32), (76, CY + 14)], fill=WHITE)


def g_layers(d):
    for i, dy in enumerate((22, 0, -22)):
        col = WHITE if i == 2 else DIM
        d.polygon([(72, CY + dy - 16), (108, CY + dy), (72, CY + dy + 16),
                   (36, CY + dy)], fill=col)


def g_think(d):
    d.ellipse([42, CY - 30, 102, CY + 18], outline=WHITE, width=8)
    for i, x in enumerate((58, 72, 86)):
        d.ellipse([x - 5, CY - 11, x + 5, CY - 1], fill=WHITE)
    d.rounded_rectangle([62, CY + 18, 82, CY + 26], 4, fill=WHITE)


def g_bolt(d):
    d.polygon([(84, CY - 32), (52, CY + 4), (70, CY + 4), (60, CY + 32),
               (94, CY - 6), (74, CY - 6)], fill=WHITE)


def g_background(d):
    d.rounded_rectangle([40, CY - 4, 104, CY + 30], 6, outline=WHITE, width=7)
    d.line([(72, CY - 32), (72, CY + 6)], fill=WHITE, width=8)
    d.polygon([(60, CY - 4), (84, CY - 4), (72, CY + 14)], fill=WHITE)


def g_stopall(d):
    d.rounded_rectangle([44, CY - 28, 100, CY + 28], 8, outline=WHITE, width=8)
    d.line([(60, CY - 12), (84, CY + 12)], fill=WHITE, width=8)
    d.line([(84, CY - 12), (60, CY + 12)], fill=WHITE, width=8)


def g_sliders(d):
    for i, kx in enumerate((88, 56, 78)):
        y = CY - 24 + i * 24
        d.rounded_rectangle([40, y - 3, 104, y + 3], 3, fill=DIM)
        d.ellipse([kx - 9, y - 9, kx + 9, y + 9], fill=WHITE)


# ------------------------------------------------------------------ tasti --

KEYS = [
    ("1-guida", "1-voce", g_mic, "Space"),
    # 2-modo non e' piu' assegnata a nessun tasto: dal 15/08/2026 le modalita'
    # si ciclano premendo l'indicatore, e il tasto 2 e' stato liberato.
    # L'icona resta generata, cosi' se un giorno il tasto torna e' gia' pronta.
    ("1-guida", "2-modo", g_cycle, "Shift+Tab"),
    ("1-guida", "3-stop", g_stop, "Esc"),
    ("1-guida", "4-rewind", g_rewind, "Esc Esc"),
    ("1-guida", "5-task", g_task, "Ctrl+T"),
    ("2-contesto", "1-storico", g_lines, "Ctrl+O"),
    ("2-contesto", "2-cerca", g_search, "Ctrl+R"),
    ("2-contesto", "3-editor", g_pencil, "Ctrl+G"),
    ("2-contesto", "4-stash", g_stash, "Ctrl+S"),
    ("2-contesto", "5-riprendi", g_play, "/resume"),
    ("2-contesto", "6-a-parte", g_bubble, "/btw"),
    ("3-regolazioni", "1-modello", g_layers, "Alt+P"),
    ("3-regolazioni", "2-thinking", g_think, "Alt+T"),
    # La didascalia diceva "Alt+O", ma il tasto manda "/fast" + Invio: l'icona
    # avrebbe insegnato una scorciatoia che non esiste. Corretto il 16/08/2026.
    ("3-regolazioni", "3-fast", g_bolt, "/fast"),
    ("3-regolazioni", "4-sfondo", g_background, "Ctrl+B"),
    ("3-regolazioni", "5-ferma", g_stopall, "CtrlX K"),
    ("3-regolazioni", "6-config", g_sliders, "/config"),
]

for page, name, glyph, cap in KEYS:
    img, d = base(PAGES[page])
    glyph(d)
    caption(d, cap)
    img.save(OUT / page / f"{name}.png")

print(f"scritte {len(KEYS)} icone in {OUT}")
