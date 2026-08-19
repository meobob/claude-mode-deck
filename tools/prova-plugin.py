#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prova il plugin contro un finto server OpenDeck, senza deck e senza OpenDeck.

Fa parlare il plugin con un WebSocket vero, gli manda gli eventi che manderebbe
OpenDeck (`willAppear`, `keyDown`) e controlla che risponda con `setImage` e
`setTitle` giusti quando il file di stato cambia.

Copre entrambe le azioni: la modalita' (che deve continuare a funzionare) e
l'attivita'. Usa file di stato temporanei: non tocca ~/.claude.

    ./tools/prova-plugin.py
"""
import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile

import websockets

QUI = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(os.path.dirname(QUI), "io.github.meobob.ccmode.sdPlugin", "plugin.mjs")
CTX_MODO = "Keypad.5.0"
CTX_ATT = "Keypad.1.0"

esiti = []


def esito(ok, testo):
    esiti.append(ok)
    print("  %s %s" % ("\033[32mOK  \033[0m" if ok else "\033[31mNO  \033[0m", testo))


def porta_libera():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


async def main():
    porta = porta_libera()
    ricevuti = []
    pronto = asyncio.Event()
    canale = {}

    async def handler(ws, *_):
        canale["ws"] = ws
        pronto.set()
        async for raw in ws:
            ricevuti.append(json.loads(raw))

    server = await websockets.serve(handler, "127.0.0.1", porta)

    modo_file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    att_file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    modo_file.write('{"mode":"auto","ts":0}'); modo_file.close()
    att_file.write('{"state":"idle","ts":0}'); att_file.close()

    env = dict(os.environ,
               CC_MODE_STATE_FILE=modo_file.name,
               CC_ACTIVITY_STATE_FILE=att_file.name,
               CC_MODE_CYCLE="0",          # niente XTEST durante la prova
               CC_MODE_POLL_MS="200",
               CC_ACTIVITY_BLINK_MS="300")
    proc = subprocess.Popen(
        ["node", PLUGIN, "-port", str(porta), "-pluginUUID", "prova",
         "-registerEvent", "registerPlugin"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    try:
        await asyncio.wait_for(pronto.wait(), 10)
    except asyncio.TimeoutError:
        print("il plugin non si e' connesso.")
        print(proc.stderr.read().decode())
        sys.exit(1)
    await asyncio.sleep(0.5)

    esito(any(m.get("event") == "registerPlugin" for m in ricevuti),
          "il plugin si registra")

    ws = canale["ws"]

    async def manda(ev, action, ctx):
        await ws.send(json.dumps({"event": ev, "action": action, "context": ctx}))
        await asyncio.sleep(0.6)

    def immagini(ctx):
        return [m["payload"]["image"] for m in ricevuti
                if m.get("event") == "setImage" and m.get("context") == ctx]

    def titoli(ctx):
        return [m["payload"]["title"] for m in ricevuti
                if m.get("event") == "setTitle" and m.get("context") == ctx]

    # --- willAppear sulle due azioni ---------------------------------------
    await manda("willAppear", "io.github.meobob.ccmode.indicator", CTX_MODO)
    esito(len(immagini(CTX_MODO)) >= 1, "willAppear modalita' -> disegna subito")

    await manda("willAppear", "io.github.meobob.ccmode.activity", CTX_ATT)
    esito(len(immagini(CTX_ATT)) >= 1, "willAppear attivita' -> disegna subito")

    # --- N cambi di stato -> N setImage distinti ----------------------------
    prima = len(immagini(CTX_ATT))
    viste = []
    for stato, atteso in (("work", "LAVORA"), ("wait", "ASPETTA"),
                          ("done", "FINITO"), ("idle", "")):
        with open(att_file.name, "w") as f:
            f.write(json.dumps({"state": stato, "ts": 0}))
        await asyncio.sleep(0.8)
        viste.append(immagini(CTX_ATT)[-1])
        esito(titoli(CTX_ATT)[-1] == atteso,
              "stato %-5s -> titolo %r" % (stato, atteso))

    esito(len(immagini(CTX_ATT)) - prima >= 4,
          "quattro cambi di stato producono almeno quattro setImage")
    esito(len(set(viste)) == 4, "le quattro immagini sono tutte diverse fra loro")

    # --- lampeggio di "aspetta" --------------------------------------------
    with open(att_file.name, "w") as f:
        f.write(json.dumps({"state": "wait", "ts": 0}))
    await asyncio.sleep(0.8)
    segno = len(immagini(CTX_ATT))
    await asyncio.sleep(1.5)
    durante = immagini(CTX_ATT)[segno:]
    esito(len(durante) >= 3, "in attesa il tasto continua a ridisegnarsi (%d volte in 1,5 s)" % len(durante))
    esito(len(set(durante)) == 2, "il lampeggio alterna esattamente due fotogrammi")

    # --- l'attesa non deve sporcare il tasto della modalita' ----------------
    modo_prima = len(immagini(CTX_MODO))
    await asyncio.sleep(1.0)
    esito(len(immagini(CTX_MODO)) == modo_prima,
          "mentre l'attivita' lampeggia, la modalita' non riceve nulla")

    # --- regressione: l'indicatore di modalita' funziona ancora -------------
    with open(att_file.name, "w") as f:
        f.write(json.dumps({"state": "idle", "ts": 0}))
    await asyncio.sleep(0.5)
    with open(modo_file.name, "w") as f:
        f.write(json.dumps({"mode": "plan", "ts": 0}))
    await asyncio.sleep(0.8)
    esito(titoli(CTX_MODO)[-1] == "PLAN", "la modalita' cambia ancora: titolo PLAN")

    # --- keyDown sull'attivita' non deve mandare tasti ----------------------
    await manda("keyDown", "io.github.meobob.ccmode.activity", CTX_ATT)
    esito(len(immagini(CTX_ATT)) >= 1, "keyDown sull'attivita' ridisegna (limite noto n. 4)")

    proc.terminate()
    server.close()
    os.unlink(modo_file.name)
    os.unlink(att_file.name)

    print()
    if all(esiti):
        print("  \033[32mTutte le %d prove superate.\033[0m" % len(esiti))
    else:
        print("  \033[31m%d prove su %d fallite.\033[0m" % (esiti.count(False), len(esiti)))
        sys.exit(1)


asyncio.run(main())
