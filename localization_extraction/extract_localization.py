"""
extract_localization.py

Extracts all localization strings from the MIO: Memories in Orbit decompiled files
and writes them to extracted_strings/ as per-category .txt files, a full
localization.json (all languages), and a localization.en.json (English only).

Source files (produced by mio-decomp from misc_files.gin):
  decomp/misc_files/decompiled/misc_files/assetslocalockit_other.csv
  decomp/misc_files/decompiled/misc_files/assetslocalockit_non_spoken.csv
  decomp/misc_files/decompiled/misc_files/assetslocalockit_spoken.csv

CSV format:
  KEY-ID,EN - SOURCE,FR,GER,IT,SP,SP LATAM,PT,PL,RU,ZH T,ZH S,KO,JA,UA,TR
  ITEM_NAME_TRINKET:BERSERKER,"The Hand's Greed",...
  HOVERTEXT:BELL_PASS_REQUIRED,"<large>Bell Tower...</large>",...

The KEY-ID column encodes both the category and item key as CATEGORY:ITEM_KEY.
Lines without a colon (bare key IDs) are skipped — they are unrelated metadata.
"""
import csv
import json
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
# Root of your mio-decomp output folder
DECOMP_DIR  = Path(r"../decomp")
# Where to write the extracted files
OUTPUT_DIR  = Path(r"extracted_strings")
# ──────────────────────────────────────────────────────────────────────────────

CSV_FILES = [
    "assetslocalockit_other.csv",
    "assetslocalockit_non_spoken.csv",
    "assetslocalockit_spoken.csv",
]

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

# Language codes matching the CSV column order (after KEY-ID and EN - SOURCE)
LANG_CODES = ["en", "fr", "de", "it", "es", "es-LA", "pt", "pl", "ru",
              "zh-TW", "zh-CN", "ko", "ja", "uk", "tr"]


def find_csv_dir(decomp_dir: Path) -> Path:
    """Locate the decompiled misc_files folder regardless of exact depth."""
    for candidate in [
        decomp_dir / "misc_files" / "decompiled" / "misc_files",
        decomp_dir / "decompiled" / "misc_files",
        decomp_dir,
    ]:
        if (candidate / "assetslocalockit_other.csv").exists():
            return candidate
    raise FileNotFoundError(
        f"Could not find assetslocalockit_other.csv under {decomp_dir}. "
        "Make sure DECOMP_DIR points at the root folder produced by mio-decomp."
    )


def read_csv_rows(csv_path: Path) -> list[dict]:
    """
    Read a localization CSV and return rows as dicts with keys:
      'raw_key', 'category', 'item_key', 'langs' (dict of lang_code -> value)
    Only rows whose KEY-ID contains a colon (i.e. CATEGORY:ITEM_KEY) are returned.
    """
    rows = []
    with csv_path.open(encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return rows

        for parts in reader:
            if not parts:
                continue
            raw_key = parts[0].strip()
            if ":" not in raw_key:
                continue
            category, item_key = raw_key.split(":", 1)
            if category not in CATEGORIES:
                continue

            # Values start at index 1 (EN - SOURCE), then FR, GER, ...
            # Map them to our LANG_CODES list
            values = parts[1:]
            lang_dict = {}
            for i, code in enumerate(LANG_CODES):
                if i < len(values) and values[i].strip():
                    lang_dict[code] = values[i].strip()

            rows.append({
                "raw_key":  raw_key,
                "category": category,
                "item_key": item_key,
                "langs":    lang_dict,
            })
    return rows


def main():
    csv_dir = find_csv_dir(DECOMP_DIR)
    print(f"Reading CSVs from: {csv_dir}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect deduplicated rows per category (use raw_key as dedup key)
    buckets: dict[str, dict[str, dict]] = {cat: {} for cat in CATEGORIES}

    for fname in CSV_FILES:
        csv_path = csv_dir / fname
        if not csv_path.exists():
            print(f"  [skip] {fname} not found")
            continue
        rows = read_csv_rows(csv_path)
        print(f"  {fname}: {len(rows)} matching rows")
        for row in rows:
            buckets[row["category"]][row["item_key"]] = row

    print()

    # Write per-category .txt files (CSV lines, sorted)
    for cat in CATEGORIES:
        items = buckets[cat]
        if not items:
            continue
        out_file = OUTPUT_DIR / (cat.lower() + ".txt")
        lines = []
        for item_key, row in sorted(items.items()):
            lang_values = [row["langs"].get(code, "") for code in LANG_CODES]
            lines.append(f'{row["raw_key"]},' + ",".join(lang_values))
        out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  {out_file.name}: {len(lines)} entries")

    # trinket_names.txt alias
    trinkets = buckets.get("ITEM_NAME_TRINKET", {})
    if trinkets:
        alias = OUTPUT_DIR / "trinket_names.txt"
        lines = []
        for item_key, row in sorted(trinkets.items()):
            lang_values = [row["langs"].get(code, "") for code in LANG_CODES]
            lines.append(f'{row["raw_key"]},' + ",".join(lang_values))
        alias.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  trinket_names.txt: {len(lines)} entries (alias for item_name_trinket)")

    print()

    # Build full localization.json: CATEGORY -> ITEM_KEY -> {lang: value}
    json_data: dict[str, dict[str, dict]] = {}
    for cat in CATEGORIES:
        for item_key, row in buckets[cat].items():
            if cat not in json_data:
                json_data[cat] = {}
            json_data[cat][item_key] = row["langs"]

    json_path = OUTPUT_DIR / "localization.json"
    json_path.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    total = sum(len(v) for v in json_data.values())
    print(f"  localization.json: {total} entries across {len(json_data)} categories")

    # English-only JSON
    en_data = {
        cat: {k: v.get("en", "") for k, v in items.items()}
        for cat, items in json_data.items()
    }
    en_path = OUTPUT_DIR / "localization.en.json"
    en_path.write_text(
        json.dumps(en_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    en_total = sum(len(v) for v in en_data.values())
    print(f"  localization.en.json: {en_total} entries across {len(en_data)} categories")

    # Save keys from miscautogensave_entries.csv
    save_csv = csv_dir / "miscautogensave_entries.csv"
    if save_csv.exists():
        save_keys: dict[str, list[str]] = {}
        with save_csv.open(encoding="utf-8", errors="replace") as f:
            next(f, None)  # skip NAME header
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if ":" in line:
                    cat, key = line.split(":", 1)
                else:
                    cat, key = line, ""
                save_keys.setdefault(cat, []).append(key)

        # Flat sorted list
        flat_keys = sorted(
            f"{cat}:{key}" if key else cat
            for cat, keys in save_keys.items()
            for key in (keys if keys else [""])
        )
        (OUTPUT_DIR / "save_keys.txt").write_text(
            "\n".join(flat_keys) + "\n", encoding="utf-8"
        )
        print(f"  save_keys.txt: {len(flat_keys)} entries")

        # JSON grouped by category
        (OUTPUT_DIR / "save_keys.json").write_text(
            json.dumps(save_keys, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # JSON with English display names where available
        en_map = {k: v for cat_items in en_data.values() for k, v in cat_items.items()}
        save_with_loc = {
            cat: {
                key: en_map.get(key, "")
                for key in keys
            }
            for cat, keys in save_keys.items()
        }
        (OUTPUT_DIR / "save_keys_with_localization.json").write_text(
            json.dumps(save_with_loc, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"  save_keys_with_localization.json: {len(flat_keys)} entries")

    print(f"\nOutput: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
