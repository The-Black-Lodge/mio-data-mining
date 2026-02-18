#!/usr/bin/env python3
"""
Extract localization strings by category from relevant_strings.txt.
Outputs to extracted_strings/ with truncated lines removed.
Also generates extracted_strings/localization.json from the txt files.
"""
import csv
import io
import json
from pathlib import Path

CATEGORIES = [
    "ITEM_NAME_ITEM",
    "ITEM_NAME_KEY",
    "ITEM_NAME_RESOURCE",
    "ITEM_NAME_SHOP_UPGRADE",
    "ITEM_NAME_TRINKET",
    "ITEM_NAME_TRINKET_SLOT_UPGRADE",
    "ITEM_NAME_UNLOCK",
    "ITEM_NAME_VOICE",
    "ITEM_DESCRIPTION_ITEM",
    "ITEM_DESCRIPTION_KEY",
    "ITEM_DESCRIPTION_RESOURCE",
    "ITEM_DESCRIPTION_SHOP_UPGRADE",
    "ITEM_DESCRIPTION_TRINKET",
    "ITEM_DESCRIPTION_UNLOCK",
    "ITEM_DESCRIPTION_VOICE",
    "ITEM_FLAVOUR_ITEM",
    "ITEM_FLAVOUR_KEY",
    "ITEM_FLAVOUR_RESOURCE",
    "ITEM_FLAVOUR_TRINKET",
    "ITEM_FLAVOUR_UNLOCK",
    "ITEM_FLAVOUR_VOICE",
    "HOVERTEXT",
]

# Language order in the CSV (matches game's translation columns)
LANG_CODES = [
    "en",      # English
    "fr",      # French
    "de",      # German
    "it",      # Italian
    "es",      # Spanish
    "es-LA",   # Spanish (LATAM)
    "pt",      # Portuguese
    "pl",      # Polish
    "ru",      # Russian
    "zh-TW",   # Chinese Traditional
    "zh-CN",   # Chinese Simplified
    "ko",      # Korean
    "ja",      # Japanese
    "uk",      # Ukrainian
    "tr",      # Turkish
]

MIN_FIELDS = 14  # Complete lines have ~16 languages; truncated have fewer


def is_complete_line(line: str) -> bool:
    """Keep only lines with enough comma-separated fields (not truncated)."""
    fields = line.split(",")
    return len(fields) >= MIN_FIELDS


def filename_for_category(cat: str) -> str:
    """Convert ITEM_NAME_TRINKET -> item_name_trinket.txt"""
    return cat.lower() + ".txt"


def parse_line_to_entry(line: str) -> tuple[str, str, dict[str, str]] | None:
    """
    Parse a CSV line into (category, item_key, {lang: value}).
    Returns None if line cannot be parsed.
    Uses csv reader to handle quoted values with commas.
    """
    reader = csv.reader(io.StringIO(line))
    try:
        parts = next(reader)
    except StopIteration:
        return None
    if len(parts) < 2:
        return None

    key_part = parts[0]
    value_parts = parts[1:]

    if ":" in key_part:
        category, item_key = key_part.split(":", 1)
    else:
        category = key_part
        item_key = "default"

    # Build lang dict - only include languages we have values for
    lang_dict = {}
    for i, code in enumerate(LANG_CODES):
        if i < len(value_parts) and value_parts[i].strip():
            lang_dict[code] = value_parts[i].strip()

    return (category, item_key, lang_dict)


def build_json_from_txt_files(out_dir: Path) -> dict:
    """Read all txt files in extracted_strings and build the JSON structure."""
    result: dict[str, dict[str, dict[str, str]]] = {}

    for txt_file in sorted(out_dir.glob("*.txt")):
        if txt_file.name == "trinket_names.txt":
            continue  # Skip alias, we get trinkets from item_name_trinket.txt

        for line in txt_file.read_text(encoding="utf-8").strip().splitlines():
            if not line.strip():
                continue
            entry = parse_line_to_entry(line)
            if not entry:
                continue

            category, item_key, lang_dict = entry
            if category not in result:
                result[category] = {}
            result[category][item_key] = lang_dict

    return result


def main():
    src = Path(r"d:\mio\relevant_strings.txt")
    out_dir = Path(r"d:\mio\extracted_strings")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect lines per category
    buckets: dict[str, set[str]] = {cat: set() for cat in CATEGORIES}

    print(f"Reading {src}...")
    with src.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            for cat in CATEGORIES:
                if line.startswith(cat + ":") or line.startswith(cat + ","):
                    if is_complete_line(line):
                        buckets[cat].add(line)
                    break

    for cat in CATEGORIES:
        lines = sorted(buckets[cat])
        if not lines:
            continue
        out_file = out_dir / filename_for_category(cat)
        out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  {filename_for_category(cat)}: {len(lines)} entries")

    # Also write trinket_names.txt as alias for item_name_trinket
    if buckets.get("ITEM_NAME_TRINKET"):
        trinket_lines = sorted(buckets["ITEM_NAME_TRINKET"])
        (out_dir / "trinket_names.txt").write_text("\n".join(trinket_lines) + "\n", encoding="utf-8")
        print(f"  trinket_names.txt: {len(trinket_lines)} entries")

    # Generate JSON from txt files
    json_data = build_json_from_txt_files(out_dir)
    json_path = out_dir / "localization.json"
    json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  localization.json: {sum(len(v) for v in json_data.values())} entries across {len(json_data)} categories")

    # Simplified English-only JSON: CATEGORY -> { ITEM_KEY -> "en string" }
    en_data = {
        cat: {item_key: lang_dict.get("en", "") for item_key, lang_dict in items.items()}
        for cat, items in json_data.items()
    }
    en_path = out_dir / "localization.en.json"
    en_path.write_text(json.dumps(en_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  localization.en.json: {sum(len(v) for v in en_data.values())} entries across {len(en_data)} categories")


if __name__ == "__main__":
    main()
