#!/usr/bin/env python3
"""Checks simples para frontend (templates e static).

Verifica:
- templates que não referenciam o CSS via url_for
- ausência do bloco de flash em base.html
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_base_flash():
    p = ROOT / "templates" / "base.html"
    text = p.read_text(encoding="utf-8")
    return "get_flashed_messages" in text


def find_templates_without_css():
    r = []
    for p in (ROOT / "templates").rglob("*.html"):
        text = p.read_text(encoding="utf-8")
        if "url_for('static', filename='css/" not in text:
            r.append(str(p.relative_to(ROOT)))
    return r


def main():
    print("Running frontend quick checks...")
    print("Base has flash block:", check_base_flash())
    print("\nTemplates missing explicit css include (heurística):")
    for f in find_templates_without_css():
        print(" -", f)


if __name__ == "__main__":
    main()
