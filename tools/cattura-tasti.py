#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Cattura i byte che arrivano dal deck e li registra con l'orario.

Sola lettura: non tocca niente, non scrive fuori dal proprio log.
Uscita: Ctrl+C.

DUE COSE DA SAPERE PRIMA DI LEGGERE UNA CATTURA, tutte e due imparate
sbagliando il 18/08/2026:

1. **La riga di pausa NON separa le pressioni.** Segnala solo che fra due byte
   e' passato piu' di mezzo secondo. Un tasto configurato con `down` e `up` —
   il trucco che questo progetto usa per dare una pausa a `Esc Esc` — manda un
   byte alla pressione e uno al rilascio, e se lo tieni premuto a lungo la
   pausa cade IN MEZZO a una pressione sola. Il 18/08 questo ha prodotto una
   diagnosi sbagliata: si erano lette raffiche di tre colpi dove c'erano due
   pressioni normali.

   Il criterio giusto e' **contare i byte**: un tasto `down`/`up` ne produce
   sempre un numero PARI. Da qui la riga di pausa dice quanto e' durata, e in
   fondo si trova il totale.

2. **Il log si accumula.** Fino al 19/08/2026 si apriva in modalita' `w` e ogni
   avvio cancellava la cattura precedente: si perdeva la misura di prima
   proprio quando serviva confrontarla con quella nuova.
"""
import os
import sys
import termios
import time

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keytest.log")


def caret(b):
    """Notazione ^X, come 'cat -v'."""
    if b == 0x7F:
        return "^?"
    if b < 0x20:
        return "^" + chr(b + 0x40)
    if b < 0x7F:
        return chr(b)
    return "\\x%02x" % b


def main():
    fd = sys.stdin.fileno()
    if not os.isatty(fd):
        sys.exit("Errore: va lanciato in un terminale vero, non in una pipe.")

    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    # iflag: niente XON/XOFF (altrimenti Ctrl+S congela) e niente CR->NL
    new[0] &= ~(termios.IXON | termios.ICRNL)
    # lflag: niente riga bufferizzata, niente eco, niente IEXTEN
    # (IEXTEN si mangerebbe Ctrl+O). ISIG resta acceso: Ctrl+C esce.
    new[3] &= ~(termios.ICANON | termios.ECHO | termios.IEXTEN)
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, new)

    # In coda, non in sovrascrittura: una cattura non deve cancellare quella
    # con cui la vuoi confrontare.
    nuovo = not os.path.exists(LOG)
    log = open(LOG, "a", buffering=1)
    log.write("\n# ===== cattura avviata %s =====\n"
              % time.strftime("%Y-%m-%d %H:%M:%S"))

    print("\r\n  Cattura attiva. Questa finestra deve avere il FOCUS.")
    print("  Premi i tasti del deck. Ctrl+C per finire.\r")
    print("  Le righe di pausa dicono quanto silenzio c'e' stato, NON dove\r")
    print("  finisce una pressione: un tasto down/up manda un byte alla\r")
    print("  pressione e uno al rilascio. Conta i byte, sono sempre pari.\r")
    if not nuovo:
        print("  Il log si accumula: le catture precedenti restano.\r")
    print("  " + "-" * 56 + "\r\n")

    last = None
    byte_totali = [0]
    try:
        while True:
            data = os.read(fd, 64)
            if not data:
                break
            now = time.time()
            # Piu' di mezzo secondo di silenzio. NON vuol dire "pressione
            # nuova": con un tasto down/up la pausa cade dentro la pressione.
            if last is not None and now - last > 0.5:
                pausa = now - last
                sys.stdout.write("\r\n  [pausa %.2f s]\r\n" % pausa)
                log.write("--- pausa %.2f s ---\n" % pausa)
            last = now
            stamp = time.strftime("%H:%M:%S", time.localtime(now))
            stamp += ".%03d" % int((now % 1) * 1000)
            for b in data:
                byte_totali[0] += 1
                r = caret(b)
                sys.stdout.write(r)
                log.write("%s  0x%02x  %s\n" % (stamp, b, r))
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old)
        n = byte_totali[0]
        parita = "pari" if n % 2 == 0 else "DISPARI"
        log.write("# fine %s — %d byte (%s)\n"
                  % (time.strftime("%Y-%m-%d %H:%M:%S"), n, parita))
        log.close()
        print("\r\n\r\n  Fine. %d byte catturati (%s).\r" % (n, parita))
        if n % 2:
            print("  Numero dispari: se stavi provando solo tasti down/up,\r")
            print("  una pressione e' andata persa o ne hai premuto un altro.\r")
        print("  Log (in coda al precedente):\r\n  %s\r" % LOG)


if __name__ == "__main__":
    main()
