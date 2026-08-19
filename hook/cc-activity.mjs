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
 * UN FILE PER SESSIONE, dal 19/08/2026. Prima ce n'era uno solo, e il difetto
 * si e' visto proprio qui: alle 09:33:09 il tasto e' andato in "aspetta" con un
 * permesso aperto a schermo, e alle 09:33:27 la notifica di inattivita' di
 * UN'ALTRA sessione lo ha riportato a "inattivo". Diciotto secondi, e lo stato
 * che l'indicatore esiste per mostrare era sparito.
 *
 * Il nome del file e' `session_id`: la Fase 0 ha stabilito che e' l'unico
 * discriminante nei payload — niente PID, niente TTY, e il `cwd` e' uguale per
 * due sessioni sullo stesso progetto.
 *
 * `SessionEnd` CANCELLA il file invece di scrivere "idle": una sessione chiusa
 * non deve avere voce nell'aggregazione. Restava un caso scoperto, il
 * terminale che muore senza `SessionEnd`, e lo copre la scadenza a tempo nel
 * plugin — diversa per stato, perche' una scadenza cieca ricreerebbe lo stesso
 * difetto in versione lenta: un permesso aperto mentre sei a pranzo non e' una
 * sessione morta.
 *
 * Esce SEMPRE 0.
 */

import { writeFileSync, renameSync, mkdirSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";

const STATE_DIR =
  process.env.CC_ACTIVITY_STATE_DIR ||
  join(homedir(), ".claude", "cc-state", "activity");

/** Il session_id ridotto a un nome di file sicuro. */
function nomeFile(sessionId) {
  const pulito = String(sessionId || "sconosciuta").replace(/[^A-Za-z0-9._-]/g, "_");
  return join(STATE_DIR, `${pulito.slice(0, 80)}.json`);
}

const PER_EVENTO = {
  SessionStart: "idle",
  UserPromptSubmit: "work",
  PreToolUse: "work",
  PostToolUse: "work",
  PermissionRequest: "wait",
  Stop: "done",
  // SessionEnd non c'e': non scrive uno stato, cancella il file.
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
  mkdirSync(STATE_DIR, { recursive: true });
  const file = nomeFile(payload.session_id);
  // Atomica: tmp + rename, cosi' il plugin non legge mai un file a meta'.
  const tmp = `${file}.${process.pid}.tmp`;
  writeFileSync(tmp, JSON.stringify(payload), "utf8");
  renameSync(tmp, file);
}

function cancella(sessionId) {
  try {
    rmSync(nomeFile(sessionId), { force: true });
  } catch {
    /* se non si puo' cancellare, la scadenza nel plugin fa da rete */
  }
}

async function leggiStdin() {
  let data = "";
  for await (const chunk of process.stdin) data += chunk;
  return data;
}

try {
  const input = JSON.parse(await leggiStdin());

  if (input.hook_event_name === "SessionEnd") {
    cancella(input.session_id);
    process.exit(0);
  }

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
