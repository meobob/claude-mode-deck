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
 */

import { writeFileSync, renameSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";

const STATE_FILE =
  process.env.CC_MODE_STATE_FILE || join(homedir(), ".claude", "cc-mode.json");

const VALID_MODES = new Set([
  "default",
  "plan",
  "acceptEdits",
  "auto",
  "dontAsk",
  "bypassPermissions",
]);

function writeState(payload) {
  const dir = dirname(STATE_FILE);
  mkdirSync(dir, { recursive: true });
  // Scrittura atomica: tmp + rename, cosi' il plugin non legge mai un file a meta'.
  const tmp = `${STATE_FILE}.${process.pid}.tmp`;
  writeFileSync(tmp, JSON.stringify(payload), "utf8");
  renameSync(tmp, STATE_FILE);
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
    // Sessione chiusa: la modalita' non ha piu' significato -> stato ignoto.
    writeState({
      mode: "unknown",
      reason: "session_end",
      ts: Date.now(),
      session_id: input.session_id ?? null,
      cwd: input.cwd ?? null,
    });
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
