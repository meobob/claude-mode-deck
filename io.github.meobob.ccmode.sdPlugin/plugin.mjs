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
const ACTIVITY_UUID = "io.github.meobob.ccmode.activity";

const STATE_FILE =
  process.env.CC_MODE_STATE_FILE || join(homedir(), ".claude", "cc-mode.json");

// Ogni quanto rileggere il file di stato (ms).
const POLL_MS = Number(process.env.CC_MODE_POLL_MS || 500);

// Dopo quanti ms senza aggiornamenti considerare il dato scaduto e mostrare
// "unknown". 0 = mai. Nota: "vecchio" non vuol dire "sbagliato" — se non usi
// Claude Code da un'ora la modalita' e' comunque ancora quella.
const STALE_AFTER_MS = Number(process.env.CC_MODE_STALE_MS || 0);

const LOG_FILE = join(HERE, "plugin.log");

// --- indicatore di attivita' -----------------------------------------------
//
// Seconda azione, file di stato SEPARATO e hook separato: due hook che
// scrivono lo stesso file sarebbe una corsa. La mappa evento -> stato sta in
// hook/cc-activity.mjs ed e' costruita sul log di eventi veri raccolto il
// 19/08/2026, non sulla documentazione.
const ACTIVITY_STATE_FILE =
  process.env.CC_ACTIVITY_STATE_FILE ||
  join(homedir(), ".claude", "cc-activity.json");

// Ogni quanto alternare i due fotogrammi di "aspetta" (ms).
const BLINK_MS = Number(process.env.CC_ACTIVITY_BLINK_MS || 600);

// Dopo quanti ms senza aggiornamenti tornare a "inattivo". 0 = mai, ed e' il
// default: una singola chiamata a uno strumento puo' durare minuti senza
// produrre eventi, e far scadere "lavora" mentre lavora sarebbe peggio del
// male che cura. Resta a disposizione per chi lascia sessioni uccise a meta'.
const ACTIVITY_STALE_MS = Number(process.env.CC_ACTIVITY_STALE_MS || 0);

/**
 * Mappa stato -> aspetto del tasto.
 *
 *  - blu     = sta lavorando
 *  - rosso   = ti aspetta, ed e' l'unico che LAMPEGGIA: e' il solo stato che
 *              chiede un'azione a te, e deve staccarsi dagli altri anche con
 *              la coda dell'occhio
 *  - verde   = ha finito. Scade su un EVENTO e non su un timer: torna grigio
 *              quando arriva la notifica di inattivita' di Claude Code,
 *              misurata a ~57 s dall'ultimo movimento
 *  - grigio  = nessuna sessione, o sessione ferma da un po'
 */
const ACTIVITY = {
  idle: { file: "act-idle.png", title: "" },
  work: { file: "act-work.png", title: "LAVORA" },
  wait: { file: "act-wait.png", title: "ASPETTA" },
  done: { file: "act-done.png", title: "FINITO" },
};

// Fotogramma spento del lampeggio. Non e' uno stato: non compare in ACTIVITY.
const ACTIVITY_OFF = { file: "act-wait-off.png", title: "ASPETTA" };

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

/** Carica una volta sola le PNG di una mappa stato -> file, come data URL. */
function loadImagesFrom(spec) {
  const out = {};
  for (const [mode, cfg] of Object.entries(spec)) {
    const path = join(HERE, "states", cfg.file);
    try {
      out[mode] = `data:image/png;base64,${readFileSync(path).toString("base64")}`;
    } catch (err) {
      log("ERRORE lettura immagine", path, String(err));
    }
  }
  return out;
}

/** Le immagini dell'indicatore di modalita'. */
function loadImages() {
  return loadImagesFrom(MODES);
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

/** Legge il file di stato dell'attivita'. Ritorna sempre uno stato valido. */
function readActivity() {
  if (!existsSync(ACTIVITY_STATE_FILE)) return "idle";
  try {
    const data = JSON.parse(readFileSync(ACTIVITY_STATE_FILE, "utf8"));
    if (!Object.prototype.hasOwnProperty.call(ACTIVITY, data.state)) return "idle";
    if (ACTIVITY_STALE_MS > 0 && typeof data.ts === "number") {
      if (Date.now() - data.ts > ACTIVITY_STALE_MS) return "idle";
    }
    return data.state;
  } catch {
    return "idle";
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
const ACTIVITY_IMAGES = loadImagesFrom({ ...ACTIVITY, waitOff: ACTIVITY_OFF });

/** context -> ultima modalita' inviata (per non spammare il socket). */
const contexts = new Map();

/** context -> ultimo stato di attivita' inviato. */
const activityContexts = new Map();

/** Fotogramma corrente del lampeggio di "aspetta". */
let blinkOn = true;

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
 * Disegna il tasto dell'attivita'.
 *
 * Differenza dall'altro `paint`: "aspetta" va ridisegnato anche quando lo
 * stato NON cambia, perche' e' il lampeggio a cambiare fotogramma. Per questo
 * chi lampeggia passa `force`.
 */
function paintActivity(context, state, { force = false } = {}) {
  if (!force && activityContexts.get(context) === state) return;
  activityContexts.set(context, state);

  const cfg = ACTIVITY[state] ?? ACTIVITY.idle;
  const chiave = state === "wait" && !blinkOn ? "waitOff" : state;
  const image = ACTIVITY_IMAGES[chiave] ?? ACTIVITY_IMAGES.idle;
  if (image) {
    send({ event: "setImage", context, payload: { image, target: 0 } });
  }
  send({ event: "setTitle", context, payload: { title: cfg.title, target: 0 } });
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
      if (msg.action === ACTIVITY_UUID) {
        activityContexts.set(msg.context, null); // null = mai dipinto
        paintActivity(msg.context, readActivity(), { force: true });
        return;
      }
      if (msg.action !== ACTION_UUID) return;
      contexts.set(msg.context, null); // null = mai dipinto -> forza il primo paint
      paint(msg.context, readMode(), { force: true });
      break;

    case "willDisappear":
      if (msg.action === ACTIVITY_UUID) {
        activityContexts.delete(msg.context);
        return;
      }
      if (msg.action !== ACTION_UUID) return;
      contexts.delete(msg.context);
      clearPending(msg.context);
      break;

    case "keyDown":
      // L'attivita' e' di sola lettura: premerla ridisegna e basta. Serve
      // soprattutto al limite noto n. 4 — un tasto nato mentre il plugin gira
      // non riceve `willAppear` e resta "?" finche' non lo premi una volta.
      if (msg.action === ACTIVITY_UUID) {
        paintActivity(msg.context, readActivity(), { force: true });
        return;
      }
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

let lastActivity = null;
setInterval(() => {
  const state = readActivity();
  if (state === lastActivity) return;
  lastActivity = state;
  // Uscendo dall'attesa il lampeggio riparte acceso, cosi' la prossima volta
  // non comincia dal fotogramma spento.
  if (state !== "wait") blinkOn = true;
  log("Attivita' ->", state);
  for (const context of activityContexts.keys()) {
    paintActivity(context, state, { force: true });
  }
}, POLL_MS);

// Lampeggio di "aspetta". Gira a vuoto se nessun tasto e' in attesa: nessun
// messaggio sul socket, nessun consumo.
setInterval(() => {
  let inAttesa = false;
  for (const state of activityContexts.values()) {
    if (state === "wait") inAttesa = true;
  }
  if (!inAttesa) return;
  blinkOn = !blinkOn;
  for (const [context, state] of activityContexts) {
    if (state === "wait") paintActivity(context, state, { force: true });
  }
}, BLINK_MS);
