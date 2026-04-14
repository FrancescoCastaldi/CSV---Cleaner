#!/usr/bin/env python3
"""
clean_csv.py
------------
Legge il file CSV in input (separatore ';', alcuni campi quotati con doppi apici),
pulisce i caratteri speciali all'interno dei campi e produce un nuovo CSV:
  - separatore: virgola ','
  - ogni campo racchiuso tra doppi apici
  - 6 campi per riga garantiti
  - caratteri speciali rimossi dal contenuto dei campi

Utilizzo:
    python3 clean_csv.py <file_input.csv> [file_output.csv]

Se il file di output non viene specificato, viene creato nella stessa cartella
dell'input con il suffisso '_cleaned.csv'.
"""

import csv
import re
import sys
import os


# ---------------------------------------------------------------------------
# Configurazione dei caratteri da pulire
# ---------------------------------------------------------------------------

# Caratteri singoli da rimuovere completamente dal testo del campo
CHARS_TO_REMOVE = set([
    '"',   # doppio apice
    "'",   # apostrofo dritto
    "\u2019",  # apostrofo curvo destro '
    "\u2018",  # apostrofo curvo sinistro '
    "\u201c",  # virgoletta aperta "
    "\u201d",  # virgoletta chiusa "
    "?",   # punto interrogativo
])

# Pattern da gestire con regex (ordine importante: prima i pattern più specifici)
REGEX_CLEANUPS = [
    # Trattino isolato a fine campo (spesso "-" finale nelle diagnosi)
    (re.compile(r'\s*-\s*$'), ''),
    # Trattino isolato a inizio campo
    (re.compile(r'^\s*-\s*'), ''),
    # Trattino isolato nel mezzo (spazio-trattino-spazio)
    (re.compile(r'\s+-\s+'), ' '),
    # Punto e virgola interno al campo → spazio
    (re.compile(r';'), ' '),
    # Virgola interna al campo → spazio
    (re.compile(r','), ' '),
    # Spazi multipli → singolo spazio
    (re.compile(r' {2,}'), ' '),
]


def clean_field(value: str) -> str:
    """Pulisce un singolo campo rimuovendo i caratteri speciali indesiderati."""
    # 1. Strip degli spazi bianchi ai bordi
    value = value.strip()

    # 2. Rimuovi caratteri singoli dalla lista CHARS_TO_REMOVE
    cleaned = []
    for ch in value:
        if ch not in CHARS_TO_REMOVE:
            cleaned.append(ch)
    value = ''.join(cleaned)

    # 3. Applica i pattern regex nell'ordine definito
    for pattern, replacement in REGEX_CLEANUPS:
        value = pattern.sub(replacement, value)

    # 4. Strip finale dopo le sostituzioni
    value = value.strip()

    return value


def process_csv(input_path: str, output_path: str) -> None:
    """
    Legge il CSV di input, pulisce i campi e scrive l'output.
    Gestisce correttamente:
      - encoding UTF-8 con BOM (utf-8-sig)
      - separatore ';'
      - campi quotati che contengono ';' interni (es. diagnosi complesse)
      - righe con a-capo incorporati dentro campi quotati
    """
    rows_ok = 0
    rows_skipped = 0
    rows_fixed = 0

    with (
        open(input_path, encoding='utf-8-sig', newline='') as fin,
        open(output_path, 'w', encoding='utf-8', newline='') as fout
    ):
        reader = csv.reader(fin, delimiter=';', quotechar='"',
                            skipinitialspace=True)
        writer = csv.writer(fout, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_ALL, lineterminator='\n')

        for line_num, row in enumerate(reader, start=1):
            # ----------------------------------------------------------------
            # Gestione righe con numero di campi diverso da 6
            # ----------------------------------------------------------------
            num_fields = len(row)

            if num_fields == 0:
                # Riga completamente vuota: salta
                rows_skipped += 1
                continue

            if num_fields < 6:
                # Troppo pochi campi: integra con stringhe vuote
                row = row + [''] * (6 - num_fields)
                rows_fixed += 1
                print(f"  [WARN] Riga {line_num}: {num_fields} campi -> integrata a 6", file=sys.stderr)

            elif num_fields > 6:
                # Troppi campi: unisci quelli in eccesso nel terzo campo (DiagnosticQuestion)
                # Strategia: i primi 2 e gli ultimi 3 campi sono stabili (ID, servizio, sesso, età, priorità)
                # tutto il resto è parte della diagnosi
                extra = ';'.join(row[2:num_fields - 3])
                row = [row[0], row[1], extra] + row[num_fields - 3:]
                rows_fixed += 1
                print(f"  [WARN] Riga {line_num}: {num_fields} campi -> unificati in 6", file=sys.stderr)

            # ----------------------------------------------------------------
            # Pulizia di ogni singolo campo
            # ----------------------------------------------------------------
            cleaned_row = [clean_field(field) for field in row[:6]]

            writer.writerow(cleaned_row)
            rows_ok += 1

    print(f"\n✓ Elaborazione completata:")
    print(f"  Righe scritte     : {rows_ok}")
    print(f"  Righe corrette    : {rows_fixed}")
    print(f"  Righe saltate     : {rows_skipped}")
    print(f"  Output            : {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 clean_csv.py <file_input.csv> [file_output.csv]")
        sys.exit(1)

    input_path = sys.argv[1]

    if not os.path.isfile(input_path):
        print(f"Errore: file non trovato -> {input_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        base, ext = os.path.splitext(input_path)
        output_path = base + '_cleaned' + ext

    print(f"Input : {input_path}")
    print(f"Output: {output_path}")
    print("Elaborazione in corso...\n")

    process_csv(input_path, output_path)


if __name__ == '__main__':
    main()
