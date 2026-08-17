# Prompt di apertura per Claude Code

Clona il repo, entra nella cartella, avvia `claude` e incolla questo:

---

```
Devo installare un indicatore hardware per Claude Code su uno stream deck
Ajazz AKP03E. Sono su Linux Mint, sessione X11.

Nel repo trovi tre documenti. Leggili in quest'ordine PRIMA di toccare
qualsiasi cosa:

1. docs/CONTEXT.md — perché questo progetto esiste, cosa è già stato deciso e
                     perché, i limiti noti. Non rimetterli in discussione
                     senza un motivo nuovo.
2. INSTALL.md      — la procedura da eseguire. Contiene regole operative
                     all'inizio: seguile.
3. README.md       — come funziona il codice, e la distinzione esplicita fra
                     ciò che è stato verificato e ciò che non lo è.

Poi lancia ./scripts/check.sh e dimmi da dove partiamo.

Vincoli per questa sessione:
- Un passo alla volta. Ferma dopo ogni fase e fammi vedere l'esito di
  check.sh prima di proseguire.
- Mostrami ogni comando con sudo prima di eseguirlo.
- I passi marcati [UTENTE] li faccio io: chiedi e aspetta.
- Non inventare percorsi, comandi o URL. Se una cosa non è nei documenti e
  non la sai, dimmelo invece di provare a indovinare.
- Se una fase fallisce, fermati e riportami l'errore esatto. Non cercare
  strade alternative di tua iniziativa.

Alla fine della sessione aggiorna docs/CONTEXT.md con quello che è successo
davvero: cosa ha funzionato, cosa no, e i comandi che sono serviti e che nei
documenti non c'erano.
```

---

## Perché è formulato così

- **I documenti prima dei comandi.** `docs/CONTEXT.md` contiene decisioni già prese
  con le loro motivazioni. Senza, un agente rischia di rifare da capo il
  ragionamento e arrivare altrove.
- **Fermate esplicite.** Le fasi 0–3 dipendono da hardware e GUI. Un agente che
  tira dritto arriva alla fine con tre cose rotte insieme invece di una.
- **Niente `--dangerously-skip-permissions`.** Si tocca `apt`,
  `/etc/apt/sources.list.d/` e `/etc/udev/rules.d/`. Vale la pena vedere ogni
  comando prima che parta.
- **L'aggiornamento finale di docs/CONTEXT.md** è il modo per non ripartire da zero
  la prossima volta. Io non ho memoria fra le conversazioni; quel file è il
  sostituto.
