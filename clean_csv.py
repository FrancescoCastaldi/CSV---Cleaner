#!/usr/bin/env python3
import csv
import re
import sys
import os

CHARS_TO_REMOVE = set([
    '"',
    "'",
    "\u2019",
    "\u2018",
    "\u201c",
    "\u201d",
    "?",
])

REGEX_CLEANUPS = [
    (re.compile(r'\s*-\s*$'), ''),
    (re.compile(r'^\s*-\s*'), ''),
    (re.compile(r'\s+-\s+'), ' '),
    (re.compile(r' {2,}'), ' '),
]

SEPARATOR_LABELS = {
    ';': 'punto e virgola (;)',
    ',': 'virgola (,)',
    '\t': 'tab (\\t)',
    '|': 'pipe (|)',
}

QUOTE_LABELS = {
    '"': 'doppio apice (")',
    "'": "apice singolo (')",
    '': 'nessuno',
}

def ask_separator(prompt: str, default: str) -> str:
    print(prompt)
    for i, (k, v) in enumerate(SEPARATOR_LABELS.items(), 1):
        marker = ' [default]' if k == default else ''
        print(f"  {i}. {v}{marker}")
    print("  5. Altro (inserisci manualmente)")
    choice = input("Scelta [invio = default]: ").strip()
    if not choice:
        return default
    if choice == '1': return ';'
    if choice == '2': return ','
    if choice == '3': return '\t'
    if choice == '4': return '|'
    if choice == '5':
        return input("Inserisci il separatore: ").strip() or default
    return default

def ask_quotechar() -> str:
    print("\nCarattere di quoting dell'output:")
    for i, (k, v) in enumerate(QUOTE_LABELS.items(), 1):
        print(f"  {i}. {v}")
    choice = input("Scelta [invio = doppio apice]: ").strip()
    if choice == '2': return "'"
    if choice == '3': return ''
    return '"'

def detect_separator(input_path: str) -> str:
    with open(input_path, encoding='utf-8-sig', newline='') as f:
        sample = f.read(4096)
    counts = {sep: sample.count(sep) for sep in SEPARATOR_LABELS}
    detected = max(counts, key=counts.get)
    return detected

def detect_num_fields(input_path: str, delimiter: str) -> int:
    with open(input_path, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f, delimiter=delimiter, quotechar='"', skipinitialspace=True)
        for row in reader:
            if row:
                return len(row)
    return 0

def clean_field(value: str, extra_chars: set) -> str:
    value = value.strip()
    all_remove = CHARS_TO_REMOVE | extra_chars
    value = ''.join(ch for ch in value if ch not in all_remove)
    for pattern, replacement in REGEX_CLEANUPS:
        value = pattern.sub(replacement, value)
    value = value.strip()
    return value

def rename_header_fields(row: list) -> list:
    return ['PrescriptionId' if field.strip() == 'IdPrescription' else field for field in row]

def process_csv(input_path: str, output_path: str, config: dict) -> None:
    in_sep      = config['in_sep']
    out_sep     = config['out_sep']
    out_quote   = config['out_quote']
    num_fields  = config['num_fields']
    extra_chars = config['extra_chars']

    quoting = csv.QUOTE_ALL if out_quote else csv.QUOTE_MINIMAL
    quotechar = out_quote if out_quote else '"'

    rows_ok = 0
    rows_skipped = 0
    rows_fixed = 0

    with (
        open(input_path, encoding='utf-8-sig', newline='') as fin,
        open(output_path, 'w', encoding='utf-8', newline='') as fout
    ):
        reader = csv.reader(fin, delimiter=in_sep, quotechar='"', skipinitialspace=True)
        writer = csv.writer(fout, delimiter=out_sep, quotechar=quotechar,
                            quoting=quoting, lineterminator='\n')

        for line_num, row in enumerate(reader, start=1):
            n = len(row)

            if n == 0:
                rows_skipped += 1
                continue

            if line_num == 1:
                row = rename_header_fields(row)

            # Rimuovi il separatore di output dai campi per evitare collisioni
            out_sep_pattern = re.compile(re.escape(out_sep))
            row = [out_sep_pattern.sub(' ', field) for field in row]

            if n < num_fields:
                row = row + [''] * (num_fields - n)
                rows_fixed += 1
                print(f"  [WARN] Riga {line_num}: {n} campi -> integrata a {num_fields}", file=sys.stderr)
            elif n > num_fields:
                extra = in_sep.join(row[2:n - (num_fields - 3)])
                row = [row[0], row[1], extra] + row[n - (num_fields - 3):]
                rows_fixed += 1
                print(f"  [WARN] Riga {line_num}: {n} campi -> unificati in {num_fields}", file=sys.stderr)

            cleaned_row = [clean_field(field, extra_chars) for field in row[:num_fields]]
            writer.writerow(cleaned_row)
            rows_ok += 1

    print(f"\n✓ Elaborazione completata:")
    print(f"  Righe scritte     : {rows_ok}")
    print(f"  Righe corrette    : {rows_fixed}")
    print(f"  Righe saltate     : {rows_skipped}")
    print(f"  Output            : {output_path}")

def interactive_config(input_path: str) -> dict:
    print("\n" + "="*50)
    print("  CONFIGURAZIONE ELABORAZIONE CSV")
    print("="*50)

    detected_sep = detect_separator(input_path)
    print(f"\n[Auto-detect] Separatore rilevato: {SEPARATOR_LABELS.get(detected_sep, repr(detected_sep))}")
    in_sep = ask_separator("\nConferma o scegli il separatore di INPUT:", detected_sep)

    detected_fields = detect_num_fields(input_path, in_sep)
    print(f"\n[Auto-detect] Campi per riga rilevati: {detected_fields}")
    custom = input(f"Numero di campi da usare [{detected_fields}] (invio = usa rilevato): ").strip()
    num_fields = int(custom) if custom.isdigit() else detected_fields

    out_sep = ask_separator("\nScegli il separatore di OUTPUT:", ',')

    out_quote = ask_quotechar()

    print("\nCaratteri aggiuntivi da rimuovere dai campi (es: @#%) [invio = nessuno]:")
    extra_input = input("> ").strip()
    extra_chars = set(extra_input) if extra_input else set()

    print("\n" + "="*50)
    print(f"  Separatore input : {repr(in_sep)}")
    print(f"  Separatore output: {repr(out_sep)}")
    print(f"  Quoting output   : {repr(out_quote) if out_quote else 'nessuno'}")
    print(f"  Campi per riga   : {num_fields}")
    print(f"  Char extra rimossi: {extra_chars or 'nessuno'}")
    print("="*50 + "\n")

    confirm = input("Confermi? [S/n]: ").strip().lower()
    if confirm == 'n':
        print("Configurazione annullata.")
        sys.exit(0)

    return {
        'in_sep': in_sep,
        'out_sep': out_sep,
        'out_quote': out_quote,
        'num_fields': num_fields,
        'extra_chars': extra_chars,
    }

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

    config = interactive_config(input_path)

    print("Elaborazione in corso...\n")
    process_csv(input_path, output_path, config)

if __name__ == '__main__':
    main()