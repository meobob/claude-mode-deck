#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Genera i tre profili DA ZERO, per un deck qualsiasi della famiglia N3.

Diverso da `profili-genera.py`, che trasforma i profili esistenti ed e' uno
strumento a colpo singolo, gia' applicato: quello e' il documento di come sono
nati i profili in uso, questo e' lo strumento per chi parte da zero.

Scrive in `nuovi-profili/` e `nuove-immagini/` qui accanto. L'installazione e'
un passo separato — `profili-installa.sh` — che fa il backup e pretende
OpenDeck fermo.

    ./scripts/profili-da-zero.py           genera
    ./scripts/profili-da-zero.py --dry     dice cosa farebbe e si ferma

QUESTO E' IL LIVELLO 2 del progetto, e a differenza degli indicatori NON e'
portabile senza condizioni. Le sue assunzioni sono elencate qui e verificate
all'avvio; quelle che cadono non fanno fallire tutto, ma **svuotano lo slot che
ne dipende** e lo dicono. Uno slot vuoto e' onesto; un tasto che manda una
combinazione che il tuo sistema non conosce sembra rotto senza spiegare perche'.

  1. FORMA DEL DECK: 9 tasti (3x3) e 3 manopole. Vale per tutti e tredici i
     modelli gestiti dal plugin AKP03 — ROW_COUNT, COL_COUNT ed ENCODER_COUNT
     in `src/mappings.rs` sono costanti di modulo, non parametri per
     dispositivo. Verificata rileggendo un profilo che OpenDeck ha gia' creato.
     Se non ce n'e' nessuno, ci si ferma: vuol dire che OpenDeck non ha mai
     visto questo deck.

     Le icone si installano su TUTTI E NOVE i tasti. Il plugin manda immagini a
     tutti, e su questo deck tre semplicemente non le mostrano: rilevare quali
     abbiano uno schermo non serve e non si puo'.

  2. VOLUME: serve `pactl`. Senza, la manopola centrale resta vuota.

  3. ZOOM DEL TERMINALE: le scorciatoie sono lette da `gsettings`, chiave
     `org.gnome.Terminal.Legacy.Keybindings`. Su un altro emulatore la
     manopola destra resta vuota, perche' mandare `Ctrl` + `+` a un terminale
     che usa altro non produrrebbe niente di visibile.

  4. TASTIERA: `Key(Unicode('+'))` presume che il `+` sia raggiungibile senza
     maiuscolo, come sulla tastiera italiana. E' implicito nel punto 3: se le
     scorciatoie di zoom non si verificano, la manopola non viene cablata.
"""
import json
import os
import shutil
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(QUI)
CONF = os.path.expanduser(os.environ.get("OPENDECK_CONFIG", "~/.config/opendeck"))
OUT_P = os.path.join(QUI, "nuovi-profili")
OUT_I = os.path.join(QUI, "nuove-immagini")

STARTER = "com.amansprojects.starterpack.sdPlugin"
NOSTRO = "io.github.meobob.ccmode.sdPlugin"
PROFILI = ("1-guida", "2-contesto", "3-regolazioni")

ESC = "[Key(Escape, Click)]"
CTRL = "[Key(Control, Press), Key(Unicode('%s'), Click), Key(Control, Release)]"
ALT = "[Key(Alt, Press), Key(Unicode('%s'), Click), Key(Alt, Release)]"
FERMA = CTRL % "x" + " + " + CTRL % "k"
FERMA = ("[Key(Control, Press), Key(Unicode('x'), Click), Key(Control, Release), "
         "Key(Control, Press), Key(Unicode('k'), Click), Key(Control, Release)]")

rosso = "\033[31m"; giallo = "\033[33m"; verde = "\033[32m"; fine = "\033[0m"


def ok(t): print("  %s[OK]%s   %s" % (verde, fine, t))
def avviso(t): print("  %s[!]%s    %s" % (giallo, fine, t))
def muori(t): sys.exit("%sERRORE:%s %s" % (rosso, fine, t))


# ---------------------------------------------------------------- layout ---
# (nome, down, up, icona). icona None = la disegna il plugin.
TASTI = {
    "1-guida": [
        ("Voce",     "[Key(Space, Click)]", "", "1-guida/1-voce.png"),
        ("Attivita", None, None, None),          # azione Activity
        ("Stop",     ESC, "", "1-guida/3-stop.png"),
        ("Rewind",   ESC, ESC, "1-guida/4-rewind.png"),
        ("Task",     CTRL % "t", "", "1-guida/5-task.png"),
        ("Stato",    None, None, None),          # azione Permission mode
    ],
    "2-contesto": [
        ("Storico",  CTRL % "o", "", "2-contesto/1-storico.png"),
        ("Cerca",    CTRL % "r", "", "2-contesto/2-cerca.png"),
        ("Editor",   CTRL % "g", "", "2-contesto/3-editor.png"),
        ("Stash",    CTRL % "s", "", "2-contesto/4-stash.png"),
        ("Riprendi", '[Text("/resume"), Key(Return, Click)]', "", "2-contesto/5-riprendi.png"),
        ("A parte",  '[Text("/btw ")]', "", "2-contesto/6-a-parte.png"),
    ],
    "3-regolazioni": [
        ("Modello",  ALT % "p", "", "3-regolazioni/1-modello.png"),
        ("Thinking", ALT % "t", "", "3-regolazioni/2-thinking.png"),
        ("Fast",     '[Text("/fast"), Key(Return, Click)]', "", "3-regolazioni/3-fast.png"),
        ("Sfondo",   CTRL % "b", "", "3-regolazioni/4-sfondo.png"),
        ("Ferma",    FERMA, FERMA, "3-regolazioni/5-ferma.png"),
        ("Config",   '[Text("/config"), Key(Return, Click)]', "", "3-regolazioni/6-config.png"),
    ],
}
# I due slot che ospitano le azioni del nostro plugin, per pagina e posizione.
NOSTRE_AZIONI = {("1-guida", 1): ("activity", "Activity", "act-idle"),
                 ("1-guida", 5): ("indicator", "Permission mode", "unknown")}


def stato(image, testo="", allineamento="middle", corpo=16, stile="Regular"):
    return {
        "alignment": allineamento, "background_colour": "#000000",
        "colour": "#FFFFFF", "family": "Liberation Sans", "image": image,
        "image_scale": 100, "name": "", "show": True, "size": corpo,
        "stroke_colour": "#000000", "stroke_size": 3, "style": stile,
        "text": testo, "underline": False,
    }


def azione(nome, uuid, icona, inspector, tooltip, stati, plugin=STARTER,
           controllers=("Keypad", "Encoder"), multi=True):
    return {
        "controllers": list(controllers), "disable_automatic_states": False,
        "encoder": None, "icon": icona, "name": nome, "plugin": plugin,
        "property_inspector": inspector, "states": stati,
        "supported_in_multi_actions": multi, "tooltip": tooltip,
        "uuid": uuid, "visible_in_action_list": True,
    }


def simula(pos, down, up, image, tipo="Keypad"):
    ic = "plugins/%s/icons/inputSimulation.png" % STARTER
    st = [stato(ic)]
    return {
        "action": azione("Simulate Input",
                         "com.amansprojects.starterpack.inputsimulation", ic,
                         "plugins/%s/propertyInspector/inputSimulation.html" % STARTER,
                         "Simulate mouse or keyboard input", st),
        "children": None, "context": "%s.%d.0" % (tipo, pos), "current_state": 0,
        "settings": {"down": down, "up": up, "anticlockwise": "", "clockwise": ""},
        "states": [stato(image)],
    }


def comando(pos, rotate, down):
    ic = "plugins/%s/icons/runCommand.png" % STARTER
    st = [stato(ic)]
    return {
        "action": azione("Run Command",
                         "com.amansprojects.starterpack.runcommand", ic,
                         "plugins/%s/propertyInspector/runCommand.html" % STARTER,
                         "Run a command", st),
        "children": None, "context": "Encoder.%d.0" % pos, "current_state": 0,
        "settings": {"down": down, "up": "", "rotate": rotate,
                     "file": "", "show": False},
        "states": [stato(ic)],
    }


def cambia_profilo(pos, device, profilo):
    ic = "plugins/%s/icons/switchProfile.png" % STARTER
    st = [stato(ic)]
    return {
        "action": azione("Switch Profile",
                         "com.amansprojects.starterpack.switchprofile", ic,
                         "plugins/%s/propertyInspector/switchProfile.html" % STARTER,
                         "Switch the selected profile", st),
        "children": None, "context": "Keypad.%d.0" % pos, "current_state": 0,
        "settings": {"anticlockwise": "Default", "clockwise": "Default",
                     "device": device, "profile": profilo},
        "states": [stato(ic)],
    }


def nostra(pos, quale, nome, icona):
    ic = "plugins/%s/states/%s.png" % (NOSTRO, icona)
    testo = "?" if quale == "indicator" else ""
    st = [stato(ic, testo, "bottom", 13, "Bold")]
    st[0]["name"] = "Indicator" if quale == "indicator" else "Activity"
    return {
        "action": azione(nome, "io.github.meobob.ccmode." + quale, ic, "",
                         "Indicatore di Claude Code", st, plugin=NOSTRO,
                         controllers=("Keypad",), multi=False),
        "children": None, "context": "Keypad.%d.0" % pos, "current_state": 0,
        "settings": {}, "states": [dict(st[0])],
    }


# ------------------------------------------------------------ verifiche ---
def trova_device():
    forzato = os.environ.get("OPENDECK_DEVICE")
    base = os.path.join(CONF, "profiles")
    if forzato:
        return forzato
    if not os.path.isdir(base):
        muori("non trovo %s.\n"
              "  Avvia OpenDeck almeno una volta, oppure indica la sua config con\n"
              "  OPENDECK_CONFIG=/percorso %s" % (base, sys.argv[0]))
    devs = sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)))
    if not devs:
        muori("nessun dispositivo in %s.\n"
              "  Collega il deck e avvia OpenDeck: il profilo lo crea lui." % base)
    if len(devs) > 1:
        muori("trovati %d dispositivi: %s\n"
              "  Scegli con  OPENDECK_DEVICE=<id> %s" % (len(devs), devs, sys.argv[0]))
    return devs[0]


def verifica_forma(device):
    """Legge un profilo gia' creato da OpenDeck e controlla 9 tasti + 3 manopole."""
    base = os.path.join(CONF, "profiles", device)
    campioni = []
    for radice, _, file in os.walk(base):
        campioni += [os.path.join(radice, f) for f in file if f.endswith(".json")]
    if not campioni:
        muori("nessun profilo esistente per %s in %s.\n"
              "  Serve per sapere quanti tasti e manopole ha il tuo deck, e non\n"
              "  voglio dedurlo. Avvia OpenDeck col deck collegato: ne crea uno."
              % (device, base))
    try:
        with open(campioni[0]) as f:
            p = json.load(f)
    except Exception as e:
        muori("non riesco a leggere %s: %s" % (campioni[0], e))
    nk, ns = len(p.get("keys") or []), len(p.get("sliders") or [])
    if (nk, ns) != (9, 3):
        muori("il tuo deck ha %d tasti e %d manopole, questo layout ne vuole 9 e 3.\n"
              "  Letto da %s. Il layout andrebbe ripensato, non adattato a forza."
              % (nk, ns, campioni[0]))
    ok("Forma del deck: 9 tasti e 3 manopole (da %s)" % os.path.basename(campioni[0]))


def verifica_volume():
    if shutil.which("pactl") is None:
        avviso("`pactl` non c'e': la manopola centrale (volume) resta VUOTA.")
        avviso("  Su Debian/Ubuntu:  sudo apt install pulseaudio-utils")
        return False
    vol = os.path.join(REPO, "scripts", "volume.sh")
    if not os.access(vol, os.X_OK):
        avviso("%s non e' eseguibile: manopola centrale VUOTA." % vol)
        return False
    ok("Volume: pactl presente, uso scripts/volume.sh")
    return True


ZOOM_ATTESO = {"zoom-in": "'<Control>plus'", "zoom-out": "'<Control>minus'",
               "zoom-normal": "'<Control>0'"}


def verifica_zoom():
    if shutil.which("gsettings") is None:
        avviso("`gsettings` non c'e': la manopola destra (zoom) resta VUOTA.")
        return False
    schema = ("org.gnome.Terminal.Legacy.Keybindings:"
              "/org/gnome/terminal/legacy/keybindings/")
    letti = {}
    for chiave in ZOOM_ATTESO:
        try:
            letti[chiave] = subprocess.run(
                ["gsettings", "get", schema, chiave],
                capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception:
            letti[chiave] = ""
    diverse = {k: v for k, v in letti.items() if v != ZOOM_ATTESO[k]}
    if not letti.get("zoom-in"):
        avviso("gnome-terminal non risponde a gsettings: manopola destra VUOTA.")
        avviso("  Su un altro emulatore le scorciatoie di zoom sono altre, e")
        avviso("  cablare le nostre darebbe un tasto che non fa niente.")
        return False
    if diverse:
        avviso("le scorciatoie di zoom non sono quelle attese: manopola destra VUOTA.")
        for k, v in diverse.items():
            avviso("    %-12s atteso %s, trovato %s" % (k, ZOOM_ATTESO[k], v or "(niente)"))
        return False
    ok("Zoom: <Control>plus / minus / 0, come atteso")
    return True


# ---------------------------------------------------------------- main ----
def main():
    dry = "--dry" in sys.argv[1:]
    print("\n== Verifiche ==")
    device = trova_device()
    ok("Dispositivo: %s" % device)
    verifica_forma(device)
    con_volume = verifica_volume()
    con_zoom = verifica_zoom()

    if not os.path.isdir(os.path.join(CONF, "plugins", NOSTRO)):
        avviso("il plugin degli indicatori non risulta installato in %s/plugins."
               % CONF)
        avviso("  I due tasti indicatori resteranno grigi. Lancia prima:  ./scripts/installa.sh")

    mancanti = [i for pagina in TASTI.values() for (_, _, _, i) in pagina
                if i and not os.path.isfile(os.path.join(REPO, "keys", i))]
    if mancanti:
        muori("mancano %d icone in keys/: %s" % (len(mancanti), mancanti[:3]))
    ok("Icone: tutte presenti in keys/")

    # --- costruzione ------------------------------------------------------
    volume_sh = os.path.join(REPO, "scripts", "volume.sh")
    manopole = [
        simula(0, CTRL % "o", "", "plugins/%s/icons/inputSimulation.png" % STARTER,
               tipo="Encoder"),
        comando(1, "%s %%d" % volume_sh, "%s muto" % volume_sh) if con_volume else None,
        simula(2, CTRL % "0", "", "plugins/%s/icons/inputSimulation.png" % STARTER,
               tipo="Encoder") if con_zoom else None,
    ]
    manopole[0]["settings"]["clockwise"] = "[Key(DownArrow, Click)]"
    manopole[0]["settings"]["anticlockwise"] = "[Key(UpArrow, Click)]"
    if con_zoom:
        manopole[2]["settings"]["clockwise"] = CTRL % "+"
        manopole[2]["settings"]["anticlockwise"] = CTRL % "-"

    profili, immagini = {}, []
    for nome in PROFILI:
        keys = []
        for pos, (etichetta, down, up, icona) in enumerate(TASTI[nome]):
            if (nome, pos) in NOSTRE_AZIONI:
                keys.append(nostra(pos, *NOSTRE_AZIONI[(nome, pos)]))
                continue
            k = simula(pos, down, up, "0.png")
            keys.append(k)
            immagini.append((nome, k["context"], icona))
        for pos, dest in enumerate(PROFILI, start=6):
            keys.append(cambia_profilo(pos, device, "Claude/" + dest))
        profili[nome] = {"infobars": [], "keys": keys, "sliders": manopole}

    print("\n== Cosa verrebbe scritto ==")
    print("  profili:   %s" % OUT_P)
    print("  immagini:  %s/%s/Claude/<profilo>/<contesto>/0.png" % (OUT_I, device))
    print("  tasti:     %d (6 con icona + 3 di navigazione, per 3 pagine)" % (9 * 3))
    print("  manopole:  %s" % ", ".join(
        "vuota" if m is None else m["action"]["name"] for m in manopole))

    if dry:
        print("\nProva a vuoto: non ho scritto niente.")
        return

    for d in (OUT_P, OUT_I):
        if os.path.isdir(d):
            shutil.rmtree(d)
    os.makedirs(OUT_P)
    for nome, ctx, icona in immagini:
        dest = os.path.join(OUT_I, device, "Claude", nome, ctx)
        os.makedirs(dest, exist_ok=True)
        shutil.copyfile(os.path.join(REPO, "keys", icona),
                        os.path.join(dest, "0.png"))
    for nome, prof in profili.items():
        with open(os.path.join(OUT_P, nome + ".json"), "w") as f:
            json.dump(prof, f, indent="\t")
            f.write("\n")

    print("\n%sGenerati.%s Ora, a OpenDeck FERMO:\n\n    ./scripts/profili-installa.sh\n"
          % (verde, fine))


if __name__ == "__main__":
    main()
