#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Mette l'azione Activity sullo slot 2 della pagina 1.

Di suo NON scrive: stampa quello che farebbe. Per toccare il profilo serve
`--scrivi`, e allora pretende OpenDeck FERMO e fa il backup.

    ./scripts/attivita-installa.py            # mostra e basta
    ./scripts/attivita-installa.py --scrivi   # applica

Perche' lo slot 2 (indice 1) della pagina 1: e' libero dal 16/08/2026, da
quando premere l'indicatore di modalita' ha reso ridondante il tasto Modo.
Scelta del 19/08/2026, consapevole del suo limite — l'attivita' si vede solo
mentre sei sulla pagina 1.

La forma dell'oggetto e' copiata da quella che OpenDeck ha scritto per
l'indicatore di modalita' sullo slot 6, con due differenze:

  - `image` dello stato punta al PNG dentro il plugin invece che a "0.png".
    "0.png" e' l'immagine per-contesto che OpenDeck salva in
    ~/.config/opendeck/images/<deck>/<profilo>/<contesto>/, e per un tasto che
    non e' mai esistito non c'e'. Col percorso del plugin il tasto ha una
    faccia gia' al primo disegno.
  - niente `text` iniziale: il titolo lo mette il plugin.
"""
import json
import os
import shutil
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(QUI)
CONF = os.path.expanduser("~/.config/opendeck")
PROFILO = "1-guida"
SLOT = 1  # indice 0-based: il tasto 2 della pagina
PLUGIN = "io.github.meobob.ccmode.sdPlugin"
UUID = "io.github.meobob.ccmode.activity"
ICONA = "plugins/%s/states/act-idle.png" % PLUGIN


def stato():
    return {
        "alignment": "bottom",
        "background_colour": "#000000",
        "colour": "#FFFFFF",
        "family": "Liberation Sans",
        "image": ICONA,
        "image_scale": 100,
        "name": "Activity",
        "show": True,
        "size": 13,
        "stroke_colour": "#000000",
        "stroke_size": 3,
        "style": "Bold",
        "text": "",
        "underline": False,
    }


def tasto():
    return {
        "action": {
            "controllers": ["Keypad"],
            "disable_automatic_states": False,
            "encoder": None,
            "icon": ICONA,
            "name": "Activity",
            "plugin": PLUGIN,
            "property_inspector": "",
            "states": [stato()],
            "supported_in_multi_actions": False,
            "tooltip": "Mostra se Claude Code sta lavorando, ha finito o ti sta aspettando",
            "uuid": UUID,
            "visible_in_action_list": True,
        },
        "children": None,
        "context": "Keypad.%d.0" % SLOT,
        "current_state": 0,
        "settings": {},
        "states": [stato()],
    }


def rileva_device():
    forzato = os.environ.get("OPENDECK_DEVICE")
    if forzato:
        return forzato
    base = os.path.join(CONF, "profiles")
    devs = sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)))
    if len(devs) != 1:
        sys.exit("Trovati %d dispositivi: %s. Usa OPENDECK_DEVICE=<id>." % (len(devs), devs))
    return devs[0]


def main():
    scrivi = "--scrivi" in sys.argv[1:]
    device = rileva_device()
    percorso = os.path.join(CONF, "profiles", device, "Claude", PROFILO + ".json")

    with open(percorso, encoding="utf-8") as f:
        prof = json.load(f)

    attuale = prof["keys"][SLOT]
    print("dispositivo: %s" % device)
    print("profilo:     %s" % percorso)
    print("slot %d (tasto %d della pagina 1): %s"
          % (SLOT, SLOT + 1,
             "vuoto" if not attuale else attuale["action"]["name"]))
    print("ci va:       Activity (%s)" % UUID)
    print()

    if not scrivi:
        print(json.dumps(tasto()["action"], indent=2, ensure_ascii=False)[:400] + " ...")
        print()
        print("Prova a vuoto: non ho scritto niente.")
        print("Per applicare:  %s --scrivi   (a OpenDeck FERMO)" % sys.argv[0])
        return

    if attuale is not None:
        sys.exit("Lo slot %d non e' vuoto (c'e' %s). Interrotto: non sovrascrivo\n"
                 "un tasto esistente senza che sia una decisione esplicita."
                 % (SLOT, attuale["action"]["name"]))

    vivo = subprocess.run(["pgrep", "-x", "opendeck"],
                          stdout=subprocess.DEVNULL).returncode == 0
    if vivo:
        sys.exit("OpenDeck e' in esecuzione: riscriverebbe il profilo e la\n"
                 "modifica sparirebbe. Esci con Quit dalla tray, poi rilancia.")

    bk = os.path.join(REPO, "backup",
                      "%s-prima-dell-attivita" % time.strftime("%Y-%m-%d-%H%M"))
    os.makedirs(bk, exist_ok=True)
    shutil.copy2(percorso, bk)
    print("backup in %s" % bk)

    prof["keys"][SLOT] = tasto()
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(prof, f, indent=2, ensure_ascii=False)
        f.write("\n")

    with open(percorso, encoding="utf-8") as f:
        ric = json.load(f)
    print("scritto. tasti della pagina 1:")
    for i, k in enumerate(ric["keys"]):
        print("  %d  %s" % (i + 1, "vuoto" if not k else k["action"]["name"]))
    print()
    print("Ora rilancia OpenDeck e premi il tasto una volta (limite noto n. 4).")


if __name__ == "__main__":
    main()
