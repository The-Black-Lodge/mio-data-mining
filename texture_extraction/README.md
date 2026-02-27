# MIO Texture Extractor

Extracts all 549 textures from **MIO: Memories in Orbit** as named PNG files mirroring the
original game folder structure (e.g. `assets/gui/icons/TRINKET_BERSERKER.png`).

---

## Prerequisites

- **MIO: Memories in Orbit** installed via Steam
- **Python 3.10+** — https://www.python.org/downloads/
  - On the installer screen, check **"Add Python to PATH"**
- **ImageMagick** — https://imagemagick.org/script/download.php#windows
  - During setup, check **"Install legacy utilities (e.g. convert)"**
- **texconv.exe** — download the latest `texconv.exe` from
  https://github.com/microsoft/DirectXTex/releases and place it somewhere convenient
  (e.g. the same folder as these scripts)

---

## Step 1 — Create a virtual environment

Open a terminal in the folder where you cloned/saved these scripts and run:

```
python -m venv .
```

Activate it:

```
Scripts\activate
```

Your prompt should now show `(mio)` or similar.

---

## Step 2 — Install the decompiler

```
pip install mio-decomp
```

Verify:

```
mio-decomp --version
```

---

## Step 3 — Decompile `assets.gin`

`assets.gin` lives in the `flamby` folder of your MIO install. On a default Steam install:

```
C:\Program Files (x86)\Steam\steamapps\common\MIO Memories in Orbit\flamby\assets.gin
```

Run the decompiler, pointing `-o` at wherever you want the output:

```
mio-decomp decompile "C:\...\flamby\assets.gin" -o decomp\assets
```

This produces `decomp\assets\decompiled\assets\texture_0` through `texture_548` (raw DDS
files without extensions), plus `ARCHIVE_METADATA` and its sidecar files.  It takes a minute
or two — `assets.gin` is ~2.9 GB.

---

## Step 4 — Install image-conversion dependencies

```
pip install -r requirements.txt
```

The script tries four backends in order and uses whichever works for each file:

| Backend | Handles |
|---------|---------|
| imageio + numpy | Most DXT/BC formats including BC5 |
| Wand (ImageMagick) | HDR/BC6H, exotic formats |
| Pillow | Simple fallback |
| texconv | Last resort for any remaining formats |

---

## Step 5 — Edit paths in `extract_final.py`

Open `extract_final.py` and update the four lines at the top of the configuration block:

```python
TEXTURE_DIR  = r"decomp\assets\decompiled\assets"   # folder containing texture_0..548
ARCHIVE_META = r"decomp\assets\decompiled\assets\ARCHIVE_METADATA"
OUTPUT_DIR   = r"textures_final"                    # where PNGs will be written
TEXCONV      = r"texconv.exe"                       # path to texconv.exe
```

Use absolute paths if the script is not in the same folder as `decomp\`.

---

## Step 6 — Run the extractor

```
python extract_final.py
```

Expected output:

```
Parsing ARCHIVE_METADATA...
  549 named textures (of 549 total)

  [OK:imageio ] texture_0   -> assets/luts/neutral.png
  [OK:imageio ] texture_1   -> assets/patches/atlas.png
  ...
  [OK:imageio ] texture_548 -> assets/sprites/decals/luras_theme.png

============================================================
Done.
  Named (549): 549 converted
  Failed:      0
Output: textures_final
```

All 549 PNGs land in `textures_final\` under their original game paths.

---

## Troubleshooting

**`mio-decomp` not found after install**
Make sure the virtual environment is activated (`Scripts\activate`).

**`[FAIL] texture_N — All backends failed`**
Install ImageMagick and re-run.  If that still fails, make sure `texconv.exe` is at the path
set in `TEXCONV`.

**Wrong number of textures decompiled**
Make sure you are decompiling `assets.gin`, not one of the smaller `.gin` files.
