#!/usr/bin/env node
/*
 * Copyright (C) 2026 meobob
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
/**
 * Claude Code Mode — plugin OpenAction/OpenDeck.
 *
 * Legge il file di stato scritto dall'hook di Claude Code e aggiorna
 * immagine e titolo di ogni istanza dell'azione sul deck.
 *
 * Premere il tasto cicla la permission mode: il plugin manda Shift+Tab alla
 * finestra attiva tramite `sendkeys.py`. Non si puo' fare impilando due azioni
 * sullo stesso tasto — misurato il 15 agosto 2026: dentro un `Multi Action` il
 * contenitore si tiene la faccia del tasto e l'indicatore non disegna piu'.
 * Restando una sola azione, `setImage` continua a comandare.
 *
 * Usa solo due eventi serverbound, entrambi specificati in modo univoco
 * nella documentazione OpenAction: `setImage` e `setTitle`.
 * (`setState` esiste ma nella doc ha un esempio evidentemente sbagliato:
 * riporta event "logMessage" e non ha il campo `context`. Non lo usiamo.)
 *
 * Richiede Node.js 22+ per la classe WebSocket globale.
 */

import { readFileSync, existsSync, appendFileSync } from "node:fs";
import { spawn } from "node:child_process";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------- config ---

const ACTION_UUID = "io.github.meobob.ccmode.indicator";

const STATE_FILE =
  process.env.CC_MODE_STATE_FILE || join(homedir(), ".claude", "cc-mode.json");

// Ogni quanto rileggere il file di stato (ms).
const POLL_MS = Number(process.env.CC_MODE_POLL_MS || 500);

// Dopo quanti ms senza aggiornamenti considerare il dato scaduto e mostrare
// "unknown". 0 = mai. Nota: "vecchio" non vuol dire "sbagliato" — se non usi
// Claude Code da un'ora la modalita' e' comunque ancora quella.
const STALE_AFTER_MS = Number(process.env.CC_MODE_STALE_MS || 0);

const LOG_FILE = join(HERE, "plugin.log");

// Premere l'indicatore cicla la modalita'. CC_MODE_CYCLE=0 lo riporta in sola
// lettura, senza toccare il codice.
const CYCLE_ON_PRESS = process.env.CC_MODE_CYCLE !== "0";
const CYCLE_KEYS = process.env.CC_MODE_CYCLE_KEYS || "shift+Tab";
const PYTHON = process.env.CC_MODE_PYTHON || "/usr/bin/python3";
const SENDKEYS = join(HERE, "sendkeys.py");

// Per quanto tempo il tasto mostra il segno di "richiesta partita".
//
// Serve perche' fra la pressione e l'icona nuova passa un tempo che non
// dipende da noi: l'hook scrive solo al prossimo evento (prompt o tool call),
// non quando premi. Senza un segno il tasto sembrerebbe non aver fatto niente,
// e la tentazione sarebbe premere una seconda volta ciclando due modalita'.
// Non mostriamo invece la modalita' successiva "prevista": l'ordine del ciclo
// dipende dalla configurazione, e indovinare vorrebbe dire scrivere sul tasto
// una cosa falsa.
const PENDING_MS = Number(process.env.CC_MODE_PENDING_MS || 6000);
const PENDING_MARK = process.env.CC_MODE_PENDING_MARK || "·";

/**
 * Mappa modalita' -> aspetto del tasto.
 *
 * Scelta dei colori, deliberata:
 *  - rosso   = ogni azione viene chiesta a te (modalita' Manual/default)
 *  - verde   = le modifiche ai file passano da sole (acceptEdits)
 *  - ambra   = approvazione automatica piu' ampia (auto / dontAsk)
 *  - magenta = bypassPermissions, cioe' niente freni. NON e' verde apposta:
 *              lo stato piu' pericoloso non deve avere il colore che il
 *              cervello legge come "tutto ok".
 *  - grigio  = stato ignoto. Fail-safe: se non sappiamo, non diciamo verde.
 */
const MODES = {
  unknown: { file: "unknown.png", title: "?" },
  default: { file: "manual.png", title: "MANUAL" },
  plan: { file: "plan.png", title: "PLAN" },
  acceptEdits: { file: "acceptedits.png", title: "EDITS" },
  auto: { file: "auto.png", title: "AUTO" },
  dontAsk: { file: "dontask.png", title: "NO ASK" },
  bypassPermissions: { file: "bypass.png", title: "BYPASS" },
};

// ------------------------------------------------------------- utilities ---

function log(...parts) {
  const line = `[${new Date().toISOString()}] ${parts.join(" ")}\n`;
  try {
    appendFileSync(LOG_FILE, line);
  } catch {
    /* il logging non deve mai far cadere il plugin */
  }
}

/** Carica una volta sola le PNG degli stati come data URL base64. */
function loadImages() {
  const out = {};
  for (const [mode, cfg] of Object.entries(MODES)) {
    const path = join(HERE, "states", cfg.file);
    try {
      out[mode] = `data:image/png;base64,${readFileSync(path).toString("base64")}`;
    } catch (err) {
      log("ERRORE lettura immagine", path, String(err));
    }
  }
  return out;
}

/** Legge il file di stato. Ritorna sempre una modalita' valida. */
function readMode() {
  if (!existsSync(STATE_FILE)) return "unknown";
  try {
    const data = JSON.parse(readFileSync(STATE_FILE, "utf8"));
    if (!Object.prototype.hasOwnProperty.call(MODES, data.mode)) return "unknown";
    if (STALE_AFTER_MS > 0 && typeof data.ts === "number") {
      if (Date.now() - data.ts > STALE_AFTER_MS) return "unknown";
    }
    return data.mode;
  } catch {
    return "unknown";
  }
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith("-")) {
      out[argv[i].slice(1)] = argv[i + 1];
      i++;
    }
  }
  return out;
}

// ------------------------------------------------------------------ main ---

const args = parseArgs(process.argv.slice(2));
const port = args.port;
const pluginUUID = args.pluginUUID;
const registerEvent = args.registerEvent;

if (!port || !pluginUUID || !registerEvent) {
  log("Argomenti di registrazione mancanti. Ricevuto:", JSON.stringify(args));
  process.exit(1);
}

if (typeof WebSocket === "undefined") {
  log("Questo Node non espone la classe WebSocket globale. Serve Node 22+.");
  process.exit(1);
}

const IMAGES = loadImages();

/** context -> ultima modalita' inviata (per non spammare il socket). */
const contexts = new Map();

const ws = new WebSocket(`ws://localhost:${port}`);

function send(obj) {
  try {
    ws.send(JSON.stringify(obj));
  } catch (err) {
    log("Invio fallito:", String(err));
  }
}

/** context -> timer che toglie il segno di attesa. */
const pendingTimers = new Map();

function clearPending(context) {
  const timer = pendingTimers.get(context);
  if (timer) {
    clearTimeout(timer);
    pendingTimers.delete(context);
  }
}

function paint(context, mode, { force = false, pending = false } = {}) {
  if (!force && contexts.get(context) === mode) return;
  contexts.set(context, mode);

  // Un disegno normale e' la risposta arrivata: il segno di attesa se ne va.
  if (!pending) clearPending(context);

  const image = IMAGES[mode] ?? IMAGES.unknown;
  if (image) {
    send({ event: "setImage", context, payload: { image, target: 0 } });
  }
  const title = pending
    ? `${MODES[mode].title} ${PENDING_MARK}`
    : MODES[mode].title;
  send({ event: "setTitle", context, payload: { title, target: 0 } });
}

/**
 * Segna l'attesa e mette una scadenza.
 *
 * La scadenza non e' un dettaglio: se cicli e torni sulla modalita' di
 * partenza, il file di stato non cambia mai valore e il poll non ridisegna
 * niente. Senza timer il puntino resterebbe li' per sempre.
 */
function markPending(context) {
  paint(context, readMode(), { force: true, pending: true });
  clearPending(context);
  pendingTimers.set(
    context,
    setTimeout(() => {
      pendingTimers.delete(context);
      paint(context, readMode(), { force: true });
    }, PENDING_MS),
  );
}

/**
 * Manda la combinazione che cicla la modalita'.
 *
 * Non aspettiamo l'esito: che abbia funzionato lo dice il file di stato al
 * prossimo evento, non il codice di uscita di questo processo.
 */
function cycleMode() {
  const child = spawn(PYTHON, [SENDKEYS, CYCLE_KEYS], {
    stdio: ["ignore", "ignore", "pipe"],
  });
  let stderr = "";
  child.stderr.on("data", (chunk) => {
    stderr += chunk;
  });
  child.on("error", (err) => {
    log("sendkeys non eseguibile:", String(err?.message ?? err));
  });
  child.on("close", (code) => {
    if (code !== 0) log("sendkeys uscito con", code, stderr.trim());
  });
}

function paintAll(mode, opts) {
  for (const context of contexts.keys()) paint(context, mode, opts);
}

ws.addEventListener("open", () => {
  send({ event: registerEvent, uuid: pluginUUID });
  log("Registrato sulla porta", port);
});

ws.addEventListener("message", (event) => {
  let msg;
  try {
    msg = JSON.parse(event.data);
  } catch {
    return;
  }

  switch (msg.event) {
    case "willAppear":
      if (msg.action !== ACTION_UUID) return;
      contexts.set(msg.context, null); // null = mai dipinto -> forza il primo paint
      paint(msg.context, readMode(), { force: true });
      break;

    case "willDisappear":
      if (msg.action !== ACTION_UUID) return;
      contexts.delete(msg.context);
      clearPending(msg.context);
      break;

    case "keyDown":
      if (msg.action !== ACTION_UUID) return;
      if (CYCLE_ON_PRESS) {
        cycleMode();
        markPending(msg.context);
      } else {
        // Indicatore in sola lettura: la pressione forza solo un refresh.
        paint(msg.context, readMode(), { force: true });
      }
      break;

    default:
      break;
  }
});

ws.addEventListener("close", () => {
  log("WebSocket chiuso, esco.");
  process.exit(0);
});

ws.addEventListener("error", (err) => {
  log("Errore WebSocket:", String(err?.message ?? err));
});

let lastMode = null;
setInterval(() => {
  const mode = readMode();
  if (mode === lastMode) return;
  lastMode = mode;
  log("Modalita' ->", mode);
  paintAll(mode);
}, POLL_MS);
