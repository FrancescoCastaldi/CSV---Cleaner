# CSV CLEANER

Utility Python per pulire e normalizzare file CSV con separatore `;`.

## Funzionalità

- Legge CSV con separatore `;` e campi eventualmente quotati.
- Converte l'output in CSV con separatore `,` e tutti i campi tra doppi apici.
- Garantisce 6 campi per riga (completa o unisce campi in eccesso).
- Rimuove caratteri speciali e normalizza gli spazi.

## Utilizzo

```bash
python3 clean_csv.py <file_input.csv> [file_output.csv]
