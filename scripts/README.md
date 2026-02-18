# Python Scripts in MIO

Summary of each Python script in the project directory.

---

## extract_strings.py

**Purpose:** Extract readable strings from binary files in the decomp directory.

**What it does:**
- Recursively scans `decomp/` for all files
- Extracts strings in ASCII, UTF-8, and UTF-16LE/BE encodings
- Filters for sequences of printable characters (min length 6)
- Outputs:
  - `extracted_strings.txt` — all unique strings
  - `relevant_strings.txt` — subset filtered by keywords (localization, dialogue, item, etc.) or sentence-like patterns

**Prerequisites:** Run decompiler first to populate `decomp/`.

---

## search_strings.py

**Purpose:** Search for specific item names inside the decomp directory.

**What it does:**
- Searches for a hardcoded list of strings (e.g. "Afterimage", "Analyser", "Black Widow", "Bird of Prey")
- Scans files in `decomp/` in both UTF-8 and UTF-16LE
- Skips empty files and files > 5MB
- Prints file path and byte offset for each match

**Use case:** Finding which decompiled files contain known localization strings.

---

## extract_localization.py

**Purpose:** Extract and organize localization data from the raw strings, then emit JSON.

**What it does:**
- Reads `relevant_strings.txt` (from `extract_strings.py`)
- Filters lines matching known categories (ITEM_NAME_TRINKET, HOVERTEXT, etc.) and drops truncated lines
- Writes one `.txt` file per category in `extracted_strings/` (e.g. `item_name_trinket.txt`)
- Parses CSV-style lines (key + 15 language columns)
- Outputs:
  - `localization.json` — `{ CATEGORY: { ITEM_KEY: { en, fr, de, ... } } }`
  - `localization.en.json` — `{ CATEGORY: { ITEM_KEY: "en string" } }`

**Prerequisites:** `relevant_strings.txt` from `extract_strings.py`.

---

## extract_save_keys.py

**Purpose:** Extract CATEGORY:ITEM keys from the save file.

**What it does:**
- Reads `slot_0.save`
- Uses regex `String\("([A-Z_]+):([A-Z_0-9]+)"\)` to find keys like `DATAPAD:CURIO_SHOE`, `BOSS:BAMBY`
- Deduplicates and groups by category
- Outputs:
  - `save_keys.json` — `{ CATEGORY: [ITEM1, ITEM2, ...] }`
  - `save_keys.txt` — flat `CATEGORY:ITEM` list, one per line

---

## find_save_localization_matches.py

**Purpose:** Find save keys that have corresponding localization entries.

**What it does:**
- Loads `localization.json` and `save_keys.json`
- Builds a set of all item keys present in localization
- Keeps only save keys whose ITEM appears in that set
- Outputs:
  - `save_keys_with_localization.json` — save keys that have localized names/descriptions (e.g. TRINKET:ANALYZER → ITEM_NAME_TRINKET:ANALYZER)

**Prerequisites:** `localization.json` and `save_keys.json` from the other scripts.

---

## Typical Workflow

1. Decompile game assets with `mio_decomp`
2. `python extract_strings.py` → raw and filtered strings
3. `python extract_localization.py` → category txt files + localization JSON
4. `python extract_save_keys.py` → save keys from slot_0.save
5. `python find_save_localization_matches.py` → mapping of save keys to localization
