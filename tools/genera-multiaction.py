#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Genera il profilo usa-e-getta Claude/9-prova per l'esperimento multi-action.

Tutti i blocchi sono copiati dai profili reali, non scritti a mano: l'unica
cosa dedotta e' la numerazione del campo `context` per i figli.

Quattro tasti, tre varianti piu' un controllo:
  1  Multi Action [Simulate Input Shift+Tab, Permission mode]
  2  Multi Action [Permission mode, Simulate Input Shift+Tab]   (ordine invertito)
  3  Permission mode da solo                                    (controllo)
  4  Multi Action [Permission mode]                             (solo indicatore)
  7-8-9  Switch Profile verso le tre pagine vere, per uscire
"""
import copy
import json
import os
import sys

CONF = os.path.expanduser("~/.config/opendeck")


def rileva_device():
    """L'ID del deck e' il nome della cartella dentro profiles/."""
    if os.environ.get("OPENDECK_DEVICE"):
        return os.environ["OPENDECK_DEVICE"]
    base = os.path.join(CONF, "profiles")
    try:
        trovati = sorted(d for d in os.listdir(base)
                         if os.path.isdir(os.path.join(base, d)))
    except FileNotFoundError:
        raise SystemExit("Non esiste %s: OpenDeck non e' mai partito?" % base)
    if len(trovati) == 1:
        return trovati[0]
    raise SystemExit("Trovati %d dispositivi in %s: %s\n"
                     "Scegli con  OPENDECK_DEVICE=<id> %s"
                     % (len(trovati), base, ", ".join(trovati) or "nessuno",
                        sys.argv[0]))


PROF = os.path.join(CONF, "profiles", rileva_device())
GUIDA = os.path.join(PROF, "Claude", "1-guida.json")
OUT = os.path.join(PROF, "Claude", "9-prova.json")

# Il contenitore `opendeck.multiaction` non viene scritto a mano: si copia da
# un profilo che ne contiene gia' uno, configurato da OpenDeck. Quando questo
# script e' stato usato la fonte era il `Default.json` del deck, che qui non
# esiste piu' — passane uno sulla riga di comando.
DEFAULT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROF, "Default.json")

guida = json.load(open(GUIDA))
if not os.path.exists(DEFAULT):
    raise SystemExit(
        "Manca il profilo da cui copiare il contenitore multi-action:\n"
        "  %s\n"
        "Serve un profilo con almeno un'azione `opendeck.multiaction` gia'\n"
        "creata da OpenDeck. Uso:  %s <profilo.json>"
        % (DEFAULT, sys.argv[0]))
default = json.load(open(DEFAULT))

# --- blocchi presi dai file reali -----------------------------------------
MULTIACTION = default["keys"][6]        # contenitore opendeck.multiaction
SIMINPUT = guida["keys"][1]             # gia' configurato con Shift+Tab
INDICATOR = guida["keys"][5]            # la nostra azione
SWITCH = guida["keys"][6]               # Switch Profile

assert MULTIACTION["action"]["uuid"] == "opendeck.multiaction"
assert SIMINPUT["settings"]["down"] == \
    "[Key(Shift, Press), Key(Tab, Click), Key(Shift, Release)]"
assert INDICATOR["action"]["uuid"] == "io.github.meobob.ccmode.indicator"
assert SWITCH["action"]["uuid"] == "com.amansprojects.starterpack.switchprofile"


def ctx(instance, pos, index):
    """Il campo context e' controller.posizione.indice.

    Dedotto: tutti gli slot radice dei profili veri finiscono in `.0`, quindi
    l'indice e' la posizione nella pila del multi-action. I figli prendono
    1, 2, ... Se la deduzione e' sbagliata, si vede da come OpenDeck riscrive
    il file al primo salvataggio: e' proprio quello che vogliamo misurare.
    """
    instance["context"] = "Keypad.%d.%d" % (pos, index)
    return instance


def indicator(pos, index):
    """Indicatore riportato allo stato iniziale del manifest.

    Nel profilo vivo l'immagine e' "0.png" con testo "AUTO": e' quello che il
    plugin ci ha dipinto sopra a runtime e che OpenDeck ha salvato. Qui
    rimettiamo il default del manifest, cosi' se sul tasto compare la
    modalita' significa che l'ha dipinta il plugin adesso, non che era gia'
    scritta nel file.
    """
    k = copy.deepcopy(INDICATOR)
    k["states"] = copy.deepcopy(k["action"]["states"])
    # il manifest ora dichiara true: allineiamo la copia dentro il profilo
    k["action"]["supported_in_multi_actions"] = True
    return ctx(k, pos, index)


def siminput(pos, index):
    return ctx(copy.deepcopy(SIMINPUT), pos, index)


def multi(pos, children):
    k = copy.deepcopy(MULTIACTION)
    k["children"] = [f(pos, i + 1) for i, f in enumerate(children)]
    return ctx(k, pos, 0)


def switch(pos, profile):
    k = copy.deepcopy(SWITCH)
    k["settings"] = dict(k["settings"], profile=profile)
    return ctx(k, pos, 0)


keys = [
    multi(0, [siminput, indicator]),   # tasto 1
    multi(1, [indicator, siminput]),   # tasto 2
    indicator(2, 0),                   # tasto 3, controllo
    multi(3, [indicator]),             # tasto 4
    None,                              # tasto 5
    None,                              # tasto 6
    switch(6, "Claude/1-guida"),
    switch(7, "Claude/2-contesto"),
    switch(8, "Claude/3-regolazioni"),
]

profile = {"infobars": [], "keys": keys, "sliders": [None, None, None]}

if os.path.exists(OUT):
    raise SystemExit("ESISTE GIA': %s — non lo sovrascrivo" % OUT)

with open(OUT, "w") as f:
    json.dump(profile, f, indent="\t")

print("scritto:", OUT)
print("byte:", os.path.getsize(OUT))
for i, k in enumerate(keys):
    if k is None:
        print("  tasto %d: vuoto" % (i + 1))
    else:
        figli = k.get("children")
        desc = k["action"]["name"]
        if figli:
            desc += " [" + ", ".join(c["action"]["name"] for c in figli) + "]"
            desc += "  ctx figli: " + ", ".join(c["context"] for c in figli)
        elif k["action"]["uuid"].startswith("com.amansprojects"):
            desc += " -> " + k["settings"]["profile"]
        print("  tasto %d: %s  (ctx %s)" % (i + 1, desc, k["context"]))
