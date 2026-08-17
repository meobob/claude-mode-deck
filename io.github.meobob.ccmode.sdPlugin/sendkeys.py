#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Manda una combinazione di tasti alla finestra attiva, via XTEST.

Serve al tasto indicatore: premerlo cicla la permission mode di Claude Code,
e per farlo bisogna simulare Shift+Tab come se l'avessi premuto tu.

Perche' XTEST e non xdotool: `python3-xlib` e' gia' installato su questa
macchina, xdotool no. Una dipendenza in meno e nessun sudo.

Perche' si tiene premuto Shift e si batte il *keycode* di Tab, invece di
mandare direttamente il keysym ISO_Left_Tab: e' quello che fa una tastiera
vera. Il server X calcola da se' ISO_Left_Tab dallo stato dello Shift, e il
terminale riceve la stessa sequenza `^[[Z` che abbiamo misurato dal deck.

Uso:
    sendkeys.py                  # shift+Tab, il default
    sendkeys.py ctrl+o
    sendkeys.py --dry-run alt+p  # risolve i keycode e non manda niente

Vincolo che vale per tutti: i tasti vanno alla finestra che ha il focus, non
a Claude Code in quanto tale. Lo stesso vincolo dei tasti del deck.
"""
import os
import sys
import time

from Xlib import XK, X, display
from Xlib.ext import xtest

# Alias comodi -> nome X11 vero.
MODIFIERS = {
    "shift": "Shift_L",
    "ctrl": "Control_L",
    "control": "Control_L",
    "alt": "Alt_L",
    "meta": "Alt_L",
    "super": "Super_L",
    "win": "Super_L",
}

# Nomi di tasto che non coincidono con il proprio carattere.
ALIASES = {
    "esc": "Escape",
    "enter": "Return",
    "invio": "Return",
    "tab": "Tab",
    "space": "space",
    "spazio": "space",
    "backspace": "BackSpace",
}


def keycode(d, name):
    ks = XK.string_to_keysym(name)
    if ks == 0:
        raise SystemExit("keysym sconosciuto: %s" % name)
    kc = d.keysym_to_keycode(ks)
    if kc == 0:
        raise SystemExit("nessun keycode per %s su questa tastiera" % name)
    return kc


def parse(spec):
    """'shift+Tab' -> (['Shift_L'], 'Tab'). L'ultimo pezzo e' il tasto."""
    parts = [p for p in spec.split("+") if p]
    if not parts:
        raise SystemExit("combinazione vuota")
    key = parts[-1]
    key = ALIASES.get(key.lower(), key)
    mods = []
    for m in parts[:-1]:
        if m.lower() not in MODIFIERS:
            raise SystemExit("modificatore sconosciuto: %s" % m)
        mods.append(MODIFIERS[m.lower()])
    return mods, key


def main():
    argv = sys.argv[1:]
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    spec = argv[0] if argv else "shift+Tab"

    mods, key = parse(spec)
    d = display.Display(os.environ.get("DISPLAY") or ":0")

    mod_codes = [keycode(d, m) for m in mods]
    key_code = keycode(d, key)

    if dry:
        print("%s -> modificatori %s, tasto %s (%d)"
              % (spec, list(zip(mods, mod_codes)), key, key_code))
        return

    for kc in mod_codes:
        xtest.fake_input(d, X.KeyPress, kc)
    time.sleep(0.01)
    xtest.fake_input(d, X.KeyPress, key_code)
    time.sleep(0.01)
    xtest.fake_input(d, X.KeyRelease, key_code)
    time.sleep(0.01)
    for kc in reversed(mod_codes):
        xtest.fake_input(d, X.KeyRelease, kc)
    d.sync()


if __name__ == "__main__":
    main()
