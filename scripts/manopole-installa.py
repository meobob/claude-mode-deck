#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Programma le tre manopole nei tre profili, identiche su tutte le pagine.

Di suo NON scrive: stampa quello che farebbe. Per toccare i profili serve
`--scrivi`, e allora pretende OpenDeck FERMO e fa il backup prima.

    ./scripts/manopole-installa.py            # mostra e basta
    ./scripts/manopole-installa.py --scrivi   # applica

Perche' identiche sulle tre pagine: stessa ragione dei tre tasti ciechi di
navigazione. Le manopole non hanno schermo, si trovano al tatto, e cambiare
quello che fanno a seconda della pagina attiva le renderebbe inutilizzabili
senza guardare.

Cosa c'e' sotto, e da dove viene — niente qui e' dedotto:

  contesto     `Encoder.<posizione>.<stato>`, non `Keypad.<...>`. Letto il
               19/08/2026 configurando una manopola nella GUI e rileggendo il
               profilo. `sliders` e' una lista di tre, l'indice e' la
               posizione, 0 = sinistra.

  impostazioni i campi delle due azioni sono letti dai loro property
               inspector, in `plugins/com.amansprojects.starterpack.sdPlugin/
               propertyInspector/`:
                 Simulate Input -> down, up, anticlockwise, clockwise
                 Run Command    -> down, up, rotate, file, show
               Su encoder `down` e' la pressione ("Dial down" nella GUI).

  rotazione    Simulate Input ha DUE caselle, una per verso. Run Command ne ha
               UNA sola, `rotate`, dove `%d` diventa il numero di scatti:
               negativo in senso antiorario, positivo in senso orario.

  nomi tasto   `UpArrow`, `DownArrow`, `Control`, `Unicode`, `Press`,
               `Release`, `Click`: presenti nel binario del plugin.

  volume       non esiste un'azione per il volume di sistema — starterpack ne
               ha cinque e nessuna lo tocca — quindi si passa da `Run Command`
               con `pactl`. La matematica sta in `scripts/volume.sh` e non
               nella casella della GUI per due motivi: Run Command esegue il
               comando senza shell, quindi `$(( ))` non esiste; e pactl
               distingue `+5%` (relativo) da `5%` (assoluto), quindi il segno
               va costruito.

  zoom         `Ctrl` + `+` / `Ctrl` + `-` / `Ctrl+0`, letti da gsettings
               (`org.gnome.Terminal.Legacy.Keybindings`) e provati con XTEST il
               19/08/2026. NON `Ctrl+Shift++`, che LAYOUT.md dava per buono.
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
PROFILI = ("1-guida", "2-contesto", "3-regolazioni")
PLUGIN = "com.amansprojects.starterpack.sdPlugin"
VOLUME = os.path.join(REPO, "scripts", "volume.sh")


def stato(icona):
    """Lo stato di uno slot, nella forma che OpenDeck scrive di suo."""
    return {
        "alignment": "middle",
        "background_colour": "#000000",
        "colour": "#FFFFFF",
        "family": "Liberation Sans",
        "image": "plugins/%s/icons/%s.png" % (PLUGIN, icona),
        "image_scale": 100,
        "name": "",
        "show": True,
        "size": 16,
        "stroke_colour": "#000000",
        "stroke_size": 3,
        "style": "Regular",
        "text": "",
        "underline": False,
    }


def slot(posizione, nome, uuid, icona, inspector, tooltip, settings):
    s = stato(icona)
    return {
        "action": {
            "controllers": ["Keypad", "Encoder"],
            "disable_automatic_states": False,
            "encoder": None,
            "icon": "plugins/%s/icons/%s.png" % (PLUGIN, icona),
            "name": nome,
            "plugin": PLUGIN,
            "property_inspector":
                "plugins/%s/propertyInspector/%s.html" % (PLUGIN, inspector),
            "states": [dict(s)],
            "supported_in_multi_actions": True,
            "tooltip": tooltip,
            "uuid": "com.amansprojects.starterpack." + uuid,
            "visible_in_action_list": True,
        },
        "children": None,
        "context": "Encoder.%d.0" % posizione,
        "current_state": 0,
        "settings": settings,
        "states": [dict(s)],
    }


def simulate(posizione, orario, antiorario, pressione):
    return slot(
        posizione, "Simulate Input", "inputsimulation", "inputSimulation",
        "inputSimulation", "Simulate mouse or keyboard input",
        {"down": pressione, "up": "",
         "anticlockwise": antiorario, "clockwise": orario},
    )


def comando(posizione, rotazione, pressione):
    return slot(
        posizione, "Run Command", "runcommand", "runCommand",
        "runCommand", "Run a command",
        {"down": pressione, "up": "", "rotate": rotazione,
         "file": "", "show": False},
    )


def ctrl(tasto):
    return ("[Key(Control, Press), Key(Unicode('%s'), Click), "
            "Key(Control, Release)]" % tasto)


MANOPOLE = [
    # 1 — scorrimento del transcript
    simulate(0,
             orario="[Key(DownArrow, Click)]",
             antiorario="[Key(UpArrow, Click)]",
             pressione=ctrl("o")),
    # 2 — volume di sistema
    comando(1,
            rotazione="%s %%d" % VOLUME,
            pressione="%s muto" % VOLUME),
    # 3 — zoom del terminale
    simulate(2,
             orario=ctrl("+"),
             antiorario=ctrl("-"),
             pressione=ctrl("0")),
]

DESCRIZIONE = [
    ("1 sinistra", "scorri il transcript", "giu' / su", "Ctrl+O"),
    ("2 centro", "volume di sistema", "+5% / -5% per scatto", "muto"),
    ("3 destra", "zoom del terminale", "Ctrl++ / Ctrl+-", "Ctrl+0"),
]


def rileva_device():
    base = os.path.join(CONF, "profiles")
    forzato = os.environ.get("OPENDECK_DEVICE")
    if forzato:
        return forzato
    devs = sorted(d for d in os.listdir(base)
                  if os.path.isdir(os.path.join(base, d)))
    if len(devs) != 1:
        sys.exit("Trovati %d dispositivi in %s: %s\n"
                 "Scegli con  OPENDECK_DEVICE=<id> %s"
                 % (len(devs), base, devs or "nessuno", sys.argv[0]))
    return devs[0]


def main():
    scrivi = "--scrivi" in sys.argv[1:]
    device = rileva_device()
    prof = os.path.join(CONF, "profiles", device, "Claude")

    if not os.path.isfile(VOLUME) or not os.access(VOLUME, os.X_OK):
        sys.exit("manca o non e' eseguibile: %s" % VOLUME)

    print("dispositivo: %s" % device)
    print("profili:     %s" % prof)
    print()
    for (dove, cosa, rot, pres) in DESCRIZIONE:
        print("  %-10s %-22s rotazione: %-22s pressione: %s"
              % (dove, cosa, rot, pres))
    print()

    if not scrivi:
        print(json.dumps(MANOPOLE[1]["settings"], indent=2))
        print()
        print("Questa e' una prova a vuoto: non ho scritto niente.")
        print("Per applicare:  %s --scrivi   (a OpenDeck FERMO)" % sys.argv[0])
        return

    # ---------------------------------------------------------- sicurezza --
    vivo = subprocess.run(["pgrep", "-x", "opendeck"],
                          stdout=subprocess.DEVNULL).returncode == 0
    if vivo:
        sys.exit("OpenDeck e' in esecuzione: tiene i profili in memoria e li\n"
                 "riscrive, quindi quello che scrivo adesso sparisce.\n"
                 "Esci con Quit dalla tray, poi rilancia.")

    # ------------------------------------------------------------ backup --
    stampo = time.strftime("%Y-%m-%d-%H%M")
    bk = os.path.join(REPO, "backup", "%s-prima-delle-manopole" % stampo)
    os.makedirs(bk, exist_ok=True)
    for nome in PROFILI:
        shutil.copy2(os.path.join(prof, nome + ".json"), bk)
    print("backup in %s" % bk)

    # ------------------------------------------------------------ scrivi --
    for nome in PROFILI:
        percorso = os.path.join(prof, nome + ".json")
        with open(percorso, encoding="utf-8") as f:
            p = json.load(f)
        assert len(p["sliders"]) == 3, "%s: sliders non sono tre" % nome
        p["sliders"] = json.loads(json.dumps(MANOPOLE))
        with open(percorso, "w", encoding="utf-8") as f:
            json.dump(p, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("  scritto %s" % nome)

    # ----------------------------------------------------------- verifica --
    print()
    print("--- controllo, rileggendo i file ---")
    for nome in PROFILI:
        with open(os.path.join(prof, nome + ".json"), encoding="utf-8") as f:
            s = json.load(f)["sliders"]
        print("  %-14s %s" % (nome, [x["action"]["name"] for x in s]))
    print()
    print("Ora rilancia OpenDeck.")


if __name__ == "__main__":
    main()
