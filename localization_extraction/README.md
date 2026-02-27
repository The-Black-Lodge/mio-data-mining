# MIO Localization Extractor

Extracts all in-game text from **MIO: Memories in Orbit** into organized files:

| Output file | Contents |
|-------------|----------|
| `item_name_trinket.txt` | Trinket names in all 15 languages |
| `item_description_trinket.txt` | Trinket descriptions |
| `item_flavour_trinket.txt` | Trinket flavour text |
| `item_name_key.txt` / `_description` / `_flavour` | Key item text |
| `item_name_resource.txt` / etc. | Resource names |
| `item_name_unlock.txt` / etc. | Unlock names |
| `item_name_voice.txt` / etc. | Character voice pack names |
| `item_name_shop_upgrade.txt` / etc. | Shop upgrade names |
| `hovertext.txt` | UI hover text (button prompts, door labels, etc.) |
| `trinket_names.txt` | Alias for `item_name_trinket.txt` |
| `localization.json` | All of the above in one JSON, all 15 languages |
| `localization.en.json` | English-only version of the above |
| `save_keys.txt` | All save-state keys (flags, counters, unlocks) |
| `save_keys.json` | Same, grouped by category |
| `save_keys_with_localization.json` | Save keys with English display names |

**No extra Python packages required** — only the standard library.

---

## Prerequisites

- **MIO: Memories in Orbit** installed via Steam
- **Python 3.10+** — https://www.python.org/downloads/
  - On the installer screen, check **"Add Python to PATH"**

---

## Step 1 — Create a virtual environment and install the decompiler

Open a terminal in the folder where you want to work and run:

```
python -m venv .
Scripts\activate
pip install mio-decomp
```

---

## Step 2 — Decompile `misc_files.gin`

The localization data lives in `misc_files.gin` inside the game's `flamby` folder.
On a default Steam install:

```
C:\Program Files (x86)\Steam\steamapps\common\MIO Memories in Orbit\flamby\misc_files.gin
```

Run the decompiler, pointing `-o` at a `decomp` folder next to this script:

```
mio-decomp decompile "C:\...\flamby\misc_files.gin" -o decomp\misc_files
```

This produces the three source CSV files under
`decomp\misc_files\decompiled\misc_files\`:

- `assetslocalockit_other.csv` — item names, descriptions, flavour text, hover text
- `assetslocalockit_non_spoken.csv` — NPC dialogue lines
- `assetslocalockit_spoken.csv` — voiced line transcripts
- `miscautogensave_entries.csv` — save-state key list

---

## Step 3 — Edit the paths in `extract_localization.py`

Open `extract_localization.py` and update the two lines at the top of the
configuration block to match where your `decomp` folder is and where you want
the output to go:

```python
DECOMP_DIR = Path(r"decomp")          # folder produced by mio-decomp
OUTPUT_DIR = Path(r"extracted_strings")  # where output files will be written
```

Use absolute paths if you are not running the script from the same directory
as `decomp\`.

---

## Step 4 — Run the extractor

```
python extract_localization.py
```

Expected output:

```
Reading CSVs from: decomp\misc_files\decompiled\misc_files
  assetslocalockit_other.csv: 312 matching rows
  ...

  item_name_trinket.txt: 45 entries
  item_description_trinket.txt: 45 entries
  hovertext.txt: 78 entries
  trinket_names.txt: 45 entries
  ...
  localization.json: 312 entries across 21 categories
  localization.en.json: 312 entries across 21 categories
  save_keys.txt: 444 entries
  save_keys_with_localization.json: 444 entries

Output: extracted_strings\
```

---

## Output format

**`.txt` files** — one entry per line, CSV format:
```
ITEM_NAME_TRINKET:BERSERKER,The Hand's Greed,Avidité de la Main,...
```

**`localization.json`** — nested JSON: `CATEGORY → ITEM_KEY → {lang_code: value}`
```json
{
  "ITEM_NAME_TRINKET": {
    "BERSERKER": {
      "en": "The Hand's Greed",
      "fr": "Avidité de la Main",
      ...
    }
  }
}
```

**Language codes:** `en` `fr` `de` `it` `es` `es-LA` `pt` `pl` `ru` `zh-TW` `zh-CN` `ko` `ja` `uk` `tr`
