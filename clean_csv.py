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
    (re.compile(r';'), ' '),
    (re.compile(r','), ' '),
    (re.compile(r' {2,}'), ' '),
]

def clean_field(value: str) -> str:
    value = value.strip()
    cleaned = []
    for ch in value:
        if ch not in CHARS_TO_REMOVE:
            cleaned.append(ch)
    value = ''.join(cleaned)
    for pattern, replacement in REGEX_CLEANUPS:
        value = pattern.sub(replacement, value)
    value = value.strip()
    return value

def rename_header_fields(row: list) -> list:
    return ['PrescriptionId' if field.strip() == 'IdPrescription' else field for field in row]

def process_csv(input_path: str, output_path: str) -> None:
    rows_ok = 0
    rows_skipped = 0
    rows_fixed = 0

    with (
        open(input_path, encoding='utf-8-sig', newline='') as fin,
        open(output_path, 'w', encoding='utf-8', newline='') as fout
    ):
        reader = csv.reader(fin, delimiter=';', quotechar='"', skipinitialspace=True)
        writer = csv.writer(fout, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_ALL, lineterminator='\n')

        for line_num, row in enumerate(reader, start=1):
            num_fields = len(row)

            if num_fields == 0:
                rows_skipped += 1
                continue

            if line_num == 1:
                row = rename_header_fields(row)

            if num_fields < 6:
                row = row + [''] * (6 - num_fields)
                rows_fixed += 1
                print(f"  [WARN] Riga {line_num}: {num_fields} campi -> integrata a 6", file=sys.stderr)
            elif num_fields > 6:
                extra = ';'.join(row[2:num_fields - 3])
                row = [row[0], row[1], extra] + row[num_fields - 3:]
                rows_fixed += 1
                print(f"  [WARN] Riga {line_num}: {num_fields} campi -> unificati in 6", file=sys.stderr)

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