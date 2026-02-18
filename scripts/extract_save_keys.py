#!/usr/bin/env python3
"""
Extract CATEGORY:ITEM format keys from save files (e.g. slot_0.save).
Outputs to extracted_strings/save_keys.json and save_keys.txt.
"""
import json
import re
from pathlib import Path

PATTERN = re.compile(r'String\("([A-Z_]+):([A-Z_0-9]+)"\)')


def extract_keys(save_path: Path) -> dict[str, list[str]]:
    """Extract CATEGORY:ITEM keys from save file, grouped by category."""
    content = save_path.read_text(encoding="utf-8", errors="ignore")
    matches = PATTERN.findall(content)

    result: dict[str, set[str]] = {}
    for category, item in matches:
        if category not in result:
            result[category] = set()
        result[category].add(item)

    # Convert sets to sorted lists for deterministic output
    return {cat: sorted(items) for cat, items in sorted(result.items())}


def main():
    save_path = Path(r"d:\mio\slot_0.save")
    out_dir = Path(r"d:\mio\extracted_strings")
    out_dir.mkdir(parents=True, exist_ok=True)

    if not save_path.exists():
        print(f"Save file not found: {save_path}")
        return

    keys = extract_keys(save_path)

    # JSON: { CATEGORY: [ITEM1, ITEM2, ...] }
    json_path = out_dir / "save_keys.json"
    json_path.write_text(json.dumps(keys, indent=2, ensure_ascii=False), encoding="utf-8")

    # TXT: flat CATEGORY:ITEM list (one per line)
    flat = []
    for cat in sorted(keys):
        for item in keys[cat]:
            flat.append(f"{cat}:{item}")
    txt_path = out_dir / "save_keys.txt"
    txt_path.write_text("\n".join(flat) + "\n", encoding="utf-8")

    total = sum(len(v) for v in keys.values())
    print(f"  save_keys.json: {total} keys across {len(keys)} categories")
    print(f"  save_keys.txt: {total} keys (flat list)")


if __name__ == "__main__":
    main()
