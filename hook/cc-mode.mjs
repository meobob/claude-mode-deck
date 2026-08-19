#!/usr/bin/env node
/*
 * Copyright (C) 2026 meobob
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
/**
 * cc-mode.mjs — Claude Code hook.
 *
 * Legge il JSON che Claude Code manda su stdin, estrae `permission_mode`
 * e lo scrive in un file di stato che il plugin OpenDeck legge.
 *
 * Il campo `permission_mode` e' documentato tra i "common input fields" degli
 * hook e puo' valere: "default" (etichettato Manual nella UI), "plan",
 * "acceptEdits", "auto", "dontAsk", "bypassPermissions".
 * NON tutti gli eventi ricevono il campo: se manca, questo script non tocca
 * il file (meglio un dato vecchio che un dato sbagliato).
 *
 * Esce SEMPRE con codice 0: un hook che fallisce mostra un avviso nel
 * transcript, e un indicatore non deve mai disturbare la sessione.
 *
 * UN FILE PER SESSIONE, dal 19/08/2026. Prima ce n'era uno solo e vinceva
 * l'ultima sessione che scriveva. Sull'indicatore di attivita' quel difetto ha
 * fatto danni misurabili — la notifica di inattivita' di una sessione ha
 * spento lo stato "ti aspetta" di un'altra dopo 18 secondi, con la richiesta
 * di permesso ancora aperta a schermo — e riguardava anche questo hook. Ora
 * ogni sessione scrive il suo file, e il plugin li aggrega.
 *
 * Il nome del file e' `session_id`, che la Fase 0 del 19/08 ha stabilito
 * essere l'UNICO discriminante disponibile: nei payload non c'e' ne' un PID
 * ne' un TTY, e il `cwd` non distingue (due sessioni sullo stesso progetto lo
 * hanno uguale — e' proprio il caso che ha prodotto il difetto).
 *
 * `SessionEnd` CANCELLA il proprio file invece di scrivere "unknown": una
 * sessione chiusa non deve avere voce nell'aggregazione.
 */

import { writeFileSync, renameSync, mkdirSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";

const STATE_DIR =
  process.env.CC_MODE_STATE_DIR ||
  join(homedir(), ".claude", "cc-state", "mode");

/** Il session_id ridotto a un nome di file sicuro. */
function nomeFile(sessionId) {
  const pulito = String(sessionId || "sconosciuta").replace(/[^A-Za-z0-9._-]/g, "_");
  return join(STATE_DIR, `${pulito.slice(0, 80)}.json`);
}

const VALID_MODES = new Set([
  "default",
  "plan",
  "acceptEdits",
  "auto",
  "dontAsk",
  "bypassPermissions",
]);

function writeState(payload) {
  mkdirSync(STATE_DIR, { recursive: true });
  const file = nomeFile(payload.session_id);
  // Scrittura atomica: tmp + rename, cosi' il plugin non legge mai un file a meta'.
  const tmp = `${file}.${process.pid}.tmp`;
  writeFileSync(tmp, JSON.stringify(payload), "utf8");
  renameSync(tmp, file);
}

function removeState(sessionId) {
  try {
    rmSync(nomeFile(sessionId), { force: true });
  } catch {
    /* se non si puo' cancellare, la scadenza a tempo fa da rete */
  }
}

async function readStdin() {
  let data = "";
  for await (const chunk of process.stdin) data += chunk;
  return data;
}

try {
  const raw = await readStdin();
  const input = JSON.parse(raw);
  const event = input.hook_event_name;

  if (event === "SessionEnd") {
    // Sessione chiusa: il suo file sparisce, non resta a votare.
    removeState(input.session_id);
  } else if (VALID_MODES.has(input.permission_mode)) {
    writeState({
      mode: input.permission_mode,
      reason: event ?? "unknown_event",
      ts: Date.now(),
      session_id: input.session_id ?? null,
      cwd: input.cwd ?? null,
    });
  }
  // Se permission_mode manca: nessuna scrittura, uscita pulita.
} catch {
  // Silenzio volutamente: qualsiasi errore qui non deve mai bloccare Claude Code.
}

process.exit(0);
