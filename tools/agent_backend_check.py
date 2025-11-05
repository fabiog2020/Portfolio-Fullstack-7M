#!/usr/bin/env python3
"""Checks simples para o backend do projeto.

Exemplos de checagens:
- Detecta files que definem `db = SQLAlchemy(app)` (padrão inline) — sinaliza para unificar.
- Verifica strings de tipo 'entrada'/'saida' no código.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def find_inline_db():
    matches = []
    for p in ROOT.rglob('*.py'):
        text = p.read_text(encoding='utf-8')
        if 'SQLAlchemy(app)' in text:
            matches.append(str(p.relative_to(ROOT)))
    return matches

def find_tipo_strings():
    files = []
    pattern = re.compile(r"\b'tipo'\b|\b\"tipo\"\b")
    for p in ROOT.rglob('*.py'):
        text = p.read_text(encoding='utf-8')
        if pattern.search(text) and ("entrada" in text or "saida" in text):
            files.append(str(p.relative_to(ROOT)))
    return files

def main():
    print('Running backend quick checks...')
    inline = find_inline_db()
    if inline:
        print('\nFound inline db usage (consider unifying to database.py):')
        for f in inline:
            print(' -', f)
    else:
        print('\nNo inline db usage found.')

    tipo_files = find_tipo_strings()
    print('\nFiles referencing tipo with entrada/saida:')
    for f in tipo_files:
        print(' -', f)

if __name__ == '__main__':
    main()
