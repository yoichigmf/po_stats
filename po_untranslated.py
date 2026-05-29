#!/usr/bin/env python3
"""List untranslated entries in a PO file with line numbers and msgid."""

import sys
from pathlib import Path


def parse_entries(lines: list[str]) -> list[dict]:
    """Parse PO file lines into entry dicts with line numbers."""
    entries = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # Skip comment lines that are not flags, looking for start of an entry
        if not (
            line.startswith("msgid ")
            or line.startswith("#,")
            or line.startswith("#:")
            or line.startswith("#.")
            or line.startswith("# ")
            or line == "#"
        ):
            i += 1
            continue

        # Collect the block for this entry
        entry_start = i
        is_fuzzy = False
        refs = []  # RST file references from #: lines
        msgid_line = None
        msgstr_line = None
        msgid_parts = []
        msgstr_parts = []
        in_msgid = False
        in_msgstr = False

        while i < n:
            line = lines[i]

            # Blank line ends the entry
            if line.strip() == "":
                break

            # Obsolete entries — skip entire block
            if line.startswith("#~"):
                while i < n and lines[i].strip() != "":
                    i += 1
                break

            # Flag line
            if line.startswith("#,") and "fuzzy" in line:
                is_fuzzy = True
                in_msgid = in_msgstr = False

            # Reference line: collect all #: refs (e.g. "../../docs/foo.rst:42")
            elif line.startswith("#:"):
                for token in line[2:].split():
                    # Normalize path: strip leading ../../
                    ref = token.lstrip("./").lstrip("/")
                    refs.append(ref)
                in_msgid = in_msgstr = False

            # msgid start
            elif line.startswith("msgid "):
                msgid_line = i + 1  # 1-indexed
                in_msgid = True
                in_msgstr = False
                val = _extract_str(line[len("msgid "):])
                msgid_parts = [val]

            # msgstr start
            elif line.startswith("msgstr "):
                msgstr_line = i + 1
                in_msgid = False
                in_msgstr = True
                val = _extract_str(line[len("msgstr "):])
                msgstr_parts = [val]

            # Continuation string
            elif line.startswith('"') and line.endswith('"'):
                val = line[1:-1]
                if in_msgid:
                    msgid_parts.append(val)
                elif in_msgstr:
                    msgstr_parts.append(val)

            # msgctxt or plural forms reset state
            elif line.startswith("msgctxt") or line.startswith("msgstr["):
                in_msgid = in_msgstr = False

            i += 1

        if msgid_line is not None:
            entries.append(
                {
                    "msgid_line": msgid_line,
                    "refs": refs,
                    "msgid": "".join(msgid_parts),
                    "msgstr": "".join(msgstr_parts),
                    "is_fuzzy": is_fuzzy,
                }
            )

        i += 1  # move past blank line

    return entries


def _extract_str(s: str) -> str:
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: python po_untranslated.py <file.po> [--fuzzy]")
        print("  --fuzzy  also show fuzzy (needs review) entries")
        sys.exit(0 if args else 1)

    show_fuzzy = "--fuzzy" in args
    po_path = Path(next(a for a in args if not a.startswith("--")))

    if not po_path.exists():
        print(f"Error: file not found: {po_path}")
        sys.exit(1)

    lines = po_path.read_text(encoding="utf-8", errors="replace").splitlines()
    entries = parse_entries(lines)

    untranslated = []
    fuzzy_entries = []

    for e in entries:
        if e["msgid"] == "":
            continue  # skip file header
        if e["is_fuzzy"]:
            fuzzy_entries.append(e)
        elif not e["msgstr"].strip():
            untranslated.append(e)

    print(f"File: {po_path}")
    print(f"Untranslated: {len(untranslated)}  Fuzzy: {len(fuzzy_entries)}")

    def print_entries(label: str, elist: list[dict]) -> None:
        if not elist:
            print(f"\n--- {label}: none ---")
            return
        print(f"\n--- {label} ({len(elist)}) ---")
        for e in elist:
            msgid_display = e["msgid"].replace("\\n", " ").strip()
            if len(msgid_display) > 100:
                msgid_display = msgid_display[:97] + "..."
            if e["refs"]:
                # Extract only line numbers from "path/file.rst:42"
                nums = ", ".join(r.rsplit(":", 1)[-1] for r in e["refs"])
            else:
                nums = str(e["msgid_line"])
            print(f"  {nums}, {msgid_display}")

    print_entries("Untranslated", untranslated)
    if show_fuzzy:
        print_entries("Fuzzy (needs review)", fuzzy_entries)


if __name__ == "__main__":
    main()
