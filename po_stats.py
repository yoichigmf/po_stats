#!/usr/bin/env python3
"""Show translation completion stats for PO files of a given language."""

import sys
import re
from pathlib import Path


def count_entries(po_path: Path) -> int:
    """Return total number of translatable entries in a PO file (header excluded)."""
    text = po_path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\n\n+", text.strip())
    count = 0
    for block in blocks:
        lines = block.strip().splitlines()
        msgid_val = []
        in_msgid = False
        for line in lines:
            if line.startswith("msgid "):
                in_msgid = True
                val = re.match(r'^msgid\s+"(.*)"$', line)
                msgid_val = [val.group(1)] if val else []
            elif line.startswith('"') and line.endswith('"') and in_msgid:
                msgid_val.append(line[1:-1])
            elif line.startswith("msgstr") or line.startswith("msgctxt"):
                in_msgid = False
            elif line.startswith("#~"):
                in_msgid = False
        full_msgid = "".join(msgid_val)
        if full_msgid != "":
            count += 1
    return count


def parse_po_stats(po_path: Path) -> tuple[int, int, int]:
    """Return (translated, fuzzy, total) for a PO file."""
    text = po_path.read_text(encoding="utf-8", errors="replace")

    translated = 0
    fuzzy = 0
    total = 0

    # Split into blocks by blank lines, filter out the header block (msgid "")
    blocks = re.split(r"\n\n+", text.strip())

    for block in blocks:
        lines = block.strip().splitlines()
        # Collect all msgid and msgstr lines (handle multi-line values)
        msgid_val = []
        msgstr_val = []
        is_fuzzy = False
        in_msgid = False
        in_msgstr = False

        for line in lines:
            if line.startswith("#, ") and "fuzzy" in line:
                is_fuzzy = True
            elif line.startswith("msgid "):
                in_msgid = True
                in_msgstr = False
                val = re.match(r'^msgid\s+"(.*)"$', line)
                msgid_val = [val.group(1)] if val else []
            elif line.startswith("msgstr "):
                in_msgid = False
                in_msgstr = True
                val = re.match(r'^msgstr\s+"(.*)"$', line)
                msgstr_val = [val.group(1)] if val else []
            elif line.startswith('"') and line.endswith('"'):
                content = line[1:-1]
                if in_msgid:
                    msgid_val.append(content)
                elif in_msgstr:
                    msgstr_val.append(content)
            elif line.startswith("msgstr[") or line.startswith("msgctxt"):
                in_msgid = False
                in_msgstr = False
            # Obsolete entries (#~) are skipped
            elif line.startswith("#~"):
                in_msgid = False
                in_msgstr = False

        full_msgid = "".join(msgid_val)
        full_msgstr = "".join(msgstr_val)

        # Skip the PO file header (msgid is empty string)
        if full_msgid == "":
            continue

        total += 1
        if is_fuzzy:
            fuzzy += 1
        elif full_msgstr.strip():
            translated += 1

    return translated, fuzzy, total


def main():
    if len(sys.argv) < 2:
        print("Usage: python po_stats.py <lang_code> [--sort] [--min-pct N] [--bar]")
        print("  --sort       sort by completion rate (ascending)")
        print("  --min-pct N  only show files below N% completion")
        print("  --bar        show progress bar")
        sys.exit(1)

    lang = sys.argv[1]
    do_sort = "--sort" in sys.argv
    show_bar = "--bar" in sys.argv
    min_pct = None
    if "--min-pct" in sys.argv:
        idx = sys.argv.index("--min-pct")
        try:
            min_pct = float(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Error: --min-pct requires a numeric argument")
            sys.exit(1)

    locale_dir = Path(__file__).parent / "locale" / lang / "LC_MESSAGES"
    en_dir = Path(__file__).parent / "locale" / "en" / "LC_MESSAGES"

    print(f"Scanning PO files in: {locale_dir}")

    if not locale_dir.exists():
        print(f"Error: directory not found: {locale_dir}")
        print("Available languages:")
        for d in sorted((Path(__file__).parent / "locale").iterdir()):
            if d.is_dir():
                print(f"  {d.name}")
        sys.exit(1)

    # Build the full source file list from English (all translatable strings)
    use_en_total = en_dir.exists()
    if use_en_total:
        en_files = {p.relative_to(en_dir): p for p in en_dir.rglob("*.po")}
    else:
        en_files = {}

    po_files = sorted(locale_dir.rglob("*.po"))
    if not po_files:
        print(f"No PO files found under {locale_dir}")
        sys.exit(1)

    # Also include English files that have no ja counterpart (0% translated)
    all_rel_paths = set(p.relative_to(locale_dir) for p in po_files)
    if use_en_total:
        missing_in_lang = set(en_files.keys()) - all_rel_paths
    else:
        missing_in_lang = set()

    rows = []
    grand_translated = grand_fuzzy = grand_total = 0

    for po_path in po_files:
        translated, fuzzy, total_in_file = parse_po_stats(po_path)
        rel = po_path.relative_to(locale_dir)

        # Use English source count as the true total if available
        if use_en_total and rel in en_files:
            en_total = count_entries(en_files[rel])
            # Untranslated = entries present in en but absent from ja file
            missing = max(0, en_total - total_in_file)
            total = total_in_file + missing
        else:
            total = total_in_file

        pct = (translated / total * 100) if total > 0 else 0.0
        rows.append((pct, translated, fuzzy, total, str(rel)))
        grand_translated += translated
        grand_fuzzy += fuzzy
        grand_total += total

    # Files that exist in English but have no ja PO file at all
    for rel in sorted(missing_in_lang):
        en_total = count_entries(en_files[rel])
        rows.append((0.0, 0, 0, en_total, str(rel)))
        grand_total += en_total

    if do_sort:
        rows.sort(key=lambda r: r[0])

    if min_pct is not None:
        rows = [r for r in rows if r[0] < min_pct]

    label_width = max(len(r[4]) for r in rows) if rows else 10
    header = f"{'File':<{label_width}}  {'Translated':>10}  {'Fuzzy':>5}  {'Total':>5}  {'Rate':>6}"
    print(f"\nLanguage: {lang}")
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    for pct, translated, fuzzy, total, rel in rows:
        line = f"{rel:<{label_width}}  {translated:>10}  {fuzzy:>5}  {total:>5}  {pct:>5.1f}%"
        if show_bar:
            bar_filled = int(pct / 5)  # 20-char bar
            bar = "#" * bar_filled + "." * (20 - bar_filled)
            line += f"  [{bar}]"
        print(line)

    print("-" * len(header))
    grand_pct = (grand_translated / grand_total * 100) if grand_total > 0 else 0.0
    print(
        f"{'TOTAL':<{label_width}}  {grand_translated:>10}  {grand_fuzzy:>5}  {grand_total:>5}  {grand_pct:>5.1f}%"
    )


if __name__ == "__main__":
    main()
