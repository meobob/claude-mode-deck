#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Applica ai tre profili le correzioni decise, senza toccare gli originali.

Legge i profili vivi, scrive i nuovi in `nuovi-profili/` e le immagini in
`nuove-immagini/`, accanto a se stesso. L'installazione e' un passo separato:
`profili-installa.sh`, che cerca quelle due cartelle qui di fianco e pretende
OpenDeck FERMO.

ATTENZIONE: e' uno strumento a colpo singolo, gia' applicato il 16/08/2026.
Rilanciarlo cosi' com'e' fallisce di proposito — gli `assert` controllano di
trovare i profili nello stato PRIMA delle correzioni, e adesso non lo sono
piu'. E' voluto: meglio un errore che applicare due volte le stesse modifiche.

Resta qui perche' e' il documento di come i profili in uso sono stati
prodotti — in particolare la tabella che lega ogni icona alla FUNZIONE del
tasto — e perche' e' il modello da copiare per la prossima modifica.

Cosa cambia, e perche':

  1-guida  tasto 2 (slot 1)  -> vuoto
      Da quando premere l'indicatore cicla le modalita', questo tasto faceva
      esattamente la stessa cosa senza dire dove sei.

  1-guida  tasto 4 (slot 3)  -> Rewind: un Esc alla pressione, uno al rilascio
      Prima erano due Esc nella stessa stringa `down`, e la cattura li ha
      misurati a 0,0 ms di distanza: buone probabilita' di essere letti come
      uno solo. La sintassi RON non ha una pausa (verificato sulla property
      inspector di starterpack: Text, MoveMouse, Scroll, Button, Key e basta),
      ma ogni azione ha due campi, `down` e `up`. Spezzandoli, la pausa
      diventa il tempo in cui tieni premuto il tasto.

  3-regolazioni  tasto 5 (slot 4) -> Ferma: accordo alla pressione e al rilascio
      Stesso trucco. `Ctrl+X Ctrl+K` va ripetuto entro 3 secondi per
      confermare, e prima c'era una volta sola.

  tutte le pagine -> le icone di keys/ al posto di quelle generiche

Sulle icone, due scelte:

  - **Si assegnano per funzione, non per posizione.** La tabella qui sotto e'
    indicizzata sulla coppia (down, up), cioe' su cosa il tasto *fa*. Se un
    giorno i tasti vengono spostati, le icone li seguono; e se uno slot facesse
    qualcosa che non e' in tabella, lo script si ferma invece di mettergli
    addosso l'icona sbagliata. Serve davvero: dopo la correzione del Rewind,
    Stop e Rewind hanno lo stesso `down` e si distinguono solo per l'`up`.

  - **Solo i tasti 1-6.** I tre in basso non hanno schermo (LAYOUT.md), quindi
    la loro icona non la vede nessuno. Il tasto 6 della pagina guida e'
    l'indicatore e se la disegna da solo: non si tocca.

Percorso delle immagini, ricavato da come OpenDeck salva quelle dell'indicatore:

    images/<device>/<profilo>/<context>/0.png     e nel profilo  "image": "0.png"
"""
import copy
import json
import os
import shutil
import sys

CONF = os.path.expanduser("~/.config/opendeck")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def rileva_device():
    """L'ID del deck e' il nome della cartella dentro profiles/.

    Su questa macchina e' n3-4250D2784745: il prefisso n3 viene dal
    DeviceNamespace di OpenDeck, il resto identifica il pezzo di hardware.
    Cambia da deck a deck, quindi si legge invece di scriverlo.
    """
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
    raise SystemExit(
        "Trovati %d dispositivi in %s: %s\n"
        "Scegli con  OPENDECK_DEVICE=<id> %s"
        % (len(trovati), base, ", ".join(trovati) or "nessuno", sys.argv[0]))


DEVICE = rileva_device()
PROF = os.path.join(CONF, "profiles", DEVICE, "Claude")
OUT_P = os.path.join(HERE, "nuovi-profili")
OUT_I = os.path.join(HERE, "nuove-immagini")

ESC = "[Key(Escape, Click)]"
CTRL = "[Key(Control, Press), Key(Unicode('%s'), Click), Key(Control, Release)]"
FERMA = ("[Key(Control, Press), Key(Unicode('x'), Click), Key(Control, Release), "
         "Key(Control, Press), Key(Unicode('k'), Click), Key(Control, Release)]")

# (down, up) -> icona. Le chiavi sono lo stato DOPO le correzioni.
ICONE = {
    ("[Key(Space, Click)]", ""): "1-guida/1-voce.png",
    (ESC, ""): "1-guida/3-stop.png",
    (ESC, ESC): "1-guida/4-rewind.png",
    (CTRL % "t", ""): "1-guida/5-task.png",

    (CTRL % "o", ""): "2-contesto/1-storico.png",
    (CTRL % "r", ""): "2-contesto/2-cerca.png",
    (CTRL % "g", ""): "2-contesto/3-editor.png",
    (CTRL % "s", ""): "2-contesto/4-stash.png",
    ('[Text("/resume"), Key(Return, Click)]', ""): "2-contesto/5-riprendi.png",
    ('[Text("/btw ")]', ""): "2-contesto/6-a-parte.png",

    ("[Key(Alt, Press), Key(Unicode('p'), Click), Key(Alt, Release)]", ""):
        "3-regolazioni/1-modello.png",
    ("[Key(Alt, Press), Key(Unicode('t'), Click), Key(Alt, Release)]", ""):
        "3-regolazioni/2-thinking.png",
    ('[Text("/fast"), Key(Return, Click)]', ""): "3-regolazioni/3-fast.png",
    (CTRL % "b", ""): "3-regolazioni/4-sfondo.png",
    (FERMA, FERMA): "3-regolazioni/5-ferma.png",
    ('[Text("/config"), Key(Return, Click)]', ""): "3-regolazioni/6-config.png",
}

INDICATORE = "io.github.meobob.ccmode.indicator"


def carica(nome):
    with open(os.path.join(PROF, nome + ".json")) as f:
        return json.load(f)


def descrivi(slot):
    if slot is None:
        return "vuoto"
    out = slot["action"]["name"]
    for campo in ("down", "up"):
        v = slot["settings"].get(campo, "")
        if v:
            out += "\n      %-5s %s" % (campo + ":", v)
    return out


def main():
    for d in (OUT_P, OUT_I):
        if os.path.isdir(d):
            shutil.rmtree(d)
    os.makedirs(OUT_P)

    profili = {n: carica(n) for n in ("1-guida", "2-contesto", "3-regolazioni")}
    prima = {n: copy.deepcopy(p) for n, p in profili.items()}

    # --- 1. tasto 2 della pagina guida: via -----------------------------------
    profili["1-guida"]["keys"][1] = None

    # --- 2. Rewind: un Esc alla pressione, uno al rilascio ---------------------
    rewind = profili["1-guida"]["keys"][3]
    assert rewind["settings"]["down"] == "[Key(Escape, Click), Key(Escape, Click)]", \
        "il tasto Rewind non e' come me lo aspettavo: " + rewind["settings"]["down"]
    rewind["settings"]["down"] = ESC
    rewind["settings"]["up"] = ESC

    # --- 3. Ferma: accordo alla pressione e al rilascio ------------------------
    ferma = profili["3-regolazioni"]["keys"][4]
    assert ferma["settings"]["down"] == FERMA, \
        "il tasto Ferma non e' come me lo aspettavo: " + ferma["settings"]["down"]
    ferma["settings"]["up"] = FERMA

    # --- 4. icone, cercate per funzione ---------------------------------------
    assegnate = []
    for nome, prof in profili.items():
        for pos in range(6):  # solo i tasti con schermo
            slot = prof["keys"][pos]
            if slot is None:
                continue
            if slot["action"]["uuid"] == INDICATORE:
                continue  # se la disegna il plugin
            chiave = (slot["settings"].get("down", ""),
                      slot["settings"].get("up", ""))
            if chiave not in ICONE:
                raise SystemExit(
                    "nessuna icona per %s tasto %d: %r\n"
                    "Meglio fermarsi che mettergli addosso quella sbagliata."
                    % (nome, pos + 1, chiave))
            icona = ICONE[chiave]
            ctx = slot["context"]
            dest = os.path.join(OUT_I, DEVICE, "Claude", nome, ctx)
            os.makedirs(dest, exist_ok=True)
            shutil.copyfile(os.path.join(REPO, "keys", icona),
                            os.path.join(dest, "0.png"))
            slot["states"][0]["image"] = "0.png"
            assegnate.append((nome, pos + 1, icona, ctx))

    for nome, prof in profili.items():
        with open(os.path.join(OUT_P, nome + ".json"), "w") as f:
            json.dump(prof, f, indent="\t")

    # --- riepilogo -----------------------------------------------------------
    print("profili in", OUT_P)
    print("immagini in", OUT_I)
    print("\n--- slot modificati ---")
    for nome in profili:
        for i, (a, b) in enumerate(zip(prima[nome]["keys"], profili[nome]["keys"])):
            if a == b:
                continue
            cambi = []
            if a is None or b is None:
                cambi.append("presenza")
            else:
                if a["settings"] != b["settings"]:
                    cambi.append("comportamento")
                if a["states"][0]["image"] != b["states"][0]["image"]:
                    cambi.append("icona")
            print("\n%s, tasto %d  [%s]" % (nome, i + 1, ", ".join(cambi)))
            print("  PRIMA: %s" % descrivi(a))
            print("  DOPO:  %s" % descrivi(b))

    print("\n--- icone assegnate (%d) ---" % len(assegnate))
    for nome, pos, icona, ctx in assegnate:
        print("  %-16s tasto %d  <-  %-28s %s" % (nome, pos, icona, ctx))

    non_usate = set(ICONE.values())
    for _, _, icona, _ in assegnate:
        non_usate.discard(icona)
    print("\nicone in tabella non assegnate:", non_usate or "nessuna")


if __name__ == "__main__":
    main()
