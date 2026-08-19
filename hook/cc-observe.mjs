#!/usr/bin/env node
/*
 * Copyright (C) 2026 meobob
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
/**
 * cc-observe.mjs — hook di sola osservazione.
 *
 * Non decide niente e non pilota niente: appende una riga per ogni evento a
 * cui e' registrato, per scoprire QUALI eventi arrivano davvero su questa
 * installazione, in che ordine e a che distanza. La macchina a stati
 * dell'indicatore di attivita' si progetta su questo log, non sulla
 * documentazione.
 *
 * E' temporaneo: si toglie con `scripts/install-observe.sh --rimuovi`.
 *
 * Formato, campi separati da TAB:
 *
 *   <ts ms>  <evento>  <marcatore>  <permission_mode>  <chiavi del payload>
 *
 * Cosa finisce nel log e cosa no:
 *
 *   - le CHIAVI del payload, mai i valori. Niente prompt, niente percorsi,
 *     niente messaggi di notifica.
 *   - il <marcatore>: solo campi corti e a valori chiusi, utili a distinguere
 *     un evento dall'altro (`source`, `reason`, `trigger`, `matcher`,
 *     `notification_type`, `type`, `stop_hook_active`). Non `message`.
 *   - `permission_mode` per intero, deroga decisa il 19/08/2026: e' un enum,
 *     non contenuto, sta gia' in chiaro in ~/.claude/cc-mode.json, e risponde
 *     da solo alla domanda se lavorando in `auto` una richiesta di permesso
 *     arrivi mai.
 *
 * Il timestamp e' l'istante in cui gira l'hook, non quello dell'evento: fra i
 * due c'e' l'avvio di node. Per questo l'hook e' registrato in modo SINCRONO,
 * cosi' l'ordine nel log e' l'ordine vero.
 *
 * Esce SEMPRE 0, come l'altro hook: un osservatore non deve mai disturbare la
 * sessione che osserva.
 */

import { appendFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";

const LOG_FILE =
  process.env.CC_OBSERVE_LOG || join(homedir(), ".claude", "cc-observe.log");

// Campi corti e a valori chiusi: dicono di che sotto-tipo e' l'evento senza
// portarsi dietro contenuto.
const MARCATORI = [
  "source",
  "reason",
  "trigger",
  "matcher",
  "notification_type",
  "type",
  "stop_hook_active",
];

async function readStdin() {
  let data = "";
  for await (const chunk of process.stdin) data += chunk;
  return data;
}

function marcatore(input) {
  const parti = [];
  for (const campo of MARCATORI) {
    const v = input[campo];
    if (v === undefined || v === null) continue;
    if (typeof v === "object") continue; // niente strutture: potrebbero contenere di tutto
    const s = String(v);
    if (s.length > 40) continue; // se e' lungo non e' un enum: lo lascio fuori
    parti.push(`${campo}=${s}`);
  }
  return parti.length ? parti.join(",") : "-";
}

try {
  const ts = Date.now();
  const raw = await readStdin();
  const input = JSON.parse(raw);

  const riga = [
    ts,
    input.hook_event_name ?? "?",
    marcatore(input),
    input.permission_mode ?? "-",
    Object.keys(input).sort().join(","),
  ].join("\t");

  mkdirSync(dirname(LOG_FILE), { recursive: true });
  appendFileSync(LOG_FILE, riga + "\n", "utf8");
} catch {
  // Silenzio: nessun errore di un osservatore deve fermare Claude Code.
}

process.exit(0);
