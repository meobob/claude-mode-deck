#!/usr/bin/env node
/*
 * Copyright (C) 2026 meobob
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
/**
 * cc-activity.mjs — hook di Claude Code per l'indicatore di ATTIVITA'.
 *
 * Distinto da cc-mode.mjs di proposito: file di stato separato
 * (~/.claude/cc-activity.json) e hook separato. Due hook che scrivono lo
 * stesso file sarebbe una corsa.
 *
 * La mappa evento -> stato qui sotto non viene dalla documentazione: viene dal
 * log raccolto il 19/08/2026 con `hook/cc-observe.mjs` su 58 eventi veri.
 * Cosa ha mostrato, e perche' la mappa e' questa:
 *
 *   lavora   UserPromptSubmit, PreToolUse, PostToolUse
 *            Sono i soli eventi che arrivano mentre il turno e' in corso.
 *
 *   aspetta  PermissionRequest
 *            Misurato: arriva 100 ms dopo il PreToolUse dello strumento da
 *            autorizzare, mentre la domanda e' a schermo. NON passa da
 *            Notification: nel log non e' mai arrivato un notification_type
 *            "permission_prompt", solo "idle_prompt".
 *            Attenzione: in modalita' `auto` non scatta mai, e nemmeno in
 *            `manual` per un comando innocuo — `date` e' passato liscio.
 *            Serve uno strumento con effetti.
 *
 *   finito   Stop
 *            Unico evento di fine turno affidabile. SubagentStop e' IGNORATO
 *            apposta: nel log arriva 2,2 s dopo Stop, ma puo' arrivare anche a
 *            meta' turno quando finisce un sottoagente e il lavoro continua.
 *
 *   inattivo SessionStart, SessionEnd, Notification(idle_prompt)
 *            `idle_prompt` e' arrivata a 57,7 s e 56,9 s dall'ultimo evento:
 *            e' Claude Code stesso a misurare l'inattivita', e per questo il
 *            verde di "finito" scade su un EVENTO invece che su un timer
 *            scelto a caso. Decisione del 19/08/2026.
 *
 * Limite noto, osservato e non risolto: se neghi un permesso con Esc, non
 * arriva ne' PostToolUse ne' Stop. Lo stato resta "aspetta" finche' non
 * succede altro. E' scomodo ma non e' falso: Claude Code sta davvero
 * aspettando te.
 *
 * Esce SEMPRE 0.
 */

import { writeFileSync, renameSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";

const STATE_FILE =
  process.env.CC_ACTIVITY_STATE_FILE ||
  join(homedir(), ".claude", "cc-activity.json");

const PER_EVENTO = {
  SessionStart: "idle",
  UserPromptSubmit: "work",
  PreToolUse: "work",
  PostToolUse: "work",
  PermissionRequest: "wait",
  Stop: "done",
  SessionEnd: "idle",
  // SubagentStop: volutamente assente. Vedi sopra.
};

function statoPer(input) {
  const evento = input.hook_event_name;
  if (evento === "Notification") {
    // Solo l'inattivita' ci interessa: gli altri tipi di notifica non
    // descrivono lo stato del turno.
    return input.notification_type === "idle_prompt" ? "idle" : null;
  }
  return PER_EVENTO[evento] ?? null;
}

function scrivi(payload) {
  mkdirSync(dirname(STATE_FILE), { recursive: true });
  // Atomica: tmp + rename, cosi' il plugin non legge mai un file a meta'.
  const tmp = `${STATE_FILE}.${process.pid}.tmp`;
  writeFileSync(tmp, JSON.stringify(payload), "utf8");
  renameSync(tmp, STATE_FILE);
}

async function leggiStdin() {
  let data = "";
  for await (const chunk of process.stdin) data += chunk;
  return data;
}

try {
  const input = JSON.parse(await leggiStdin());
  const stato = statoPer(input);
  if (stato) {
    scrivi({
      state: stato,
      reason: input.hook_event_name ?? "unknown_event",
      ts: Date.now(),
      session_id: input.session_id ?? null,
      cwd: input.cwd ?? null,
    });
  }
  // Evento non mappato: nessuna scrittura, uscita pulita.
} catch {
  // Silenzio: un indicatore non deve mai disturbare la sessione.
}

process.exit(0);
