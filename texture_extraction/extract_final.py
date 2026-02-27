"""
extract_final.py

Converts all MIO texture_N DDS files to PNG with correct original game-path names.

Pipeline:
  1. Parse ARCHIVE_METADATA binary to build a complete texture_N -> original path mapping
     for all 549 textures.

     The binary contains a 1024-slot open-addressing hash table at offset table_off.
     A companion array at comp_off (one u32 per N, indexed 0..548) stores the SLOT INDEX
     in that 1024-slot table for each texture_N.  This gives us the correct path for every
     texture, including the 274 that were previously "unmatched" because they live in slots
     549-1023 (beyond the 549-entry count the old code used as a loop bound).

     Old approach (275/549):  iterate i in range(549), decode N from entry's extra_lo
     New approach (549/549):  for each N, read slot = companion[N], then read entry at slot

  2. For each texture_N, copy the raw DDS to a temp file.
  3. Convert to PNG via multi-backend stack (imageio -> Wand -> Pillow -> texconv).
  4. All 549 textures save to OUTPUT_DIR mirroring the original game folder structure.

Requirements:
  pip install imageio numpy        (handles most DDS formats incl. BC5)
  pip install Wand                 (optional fallback; needs ImageMagick)
  texconv.exe from https://github.com/microsoft/DirectXTex/releases
"""

import os
import re
import shutil
import struct
import subprocess
import tempfile

# ── Configuration ─────────────────────────────────────────────────────────────
TEXTURE_DIR   = r"D:\mio\decomp\assets\decompiled\assets"
ARCHIVE_META  = r"D:\mio\decomp\assets\decompiled\assets\ARCHIVE_METADATA"
OUTPUT_DIR    = r"D:\mio\textures_final"
TEXCONV       = r"D:\mio\texconv.exe"

TEXTURE_BASE  = 156555   # gin section table position of texture_0
N_TEXTURES    = 549
# ─────────────────────────────────────────────────────────────────────────────


# ── Conversion backends ───────────────────────────────────────────────────────

def try_imageio(src, dst):
    import imageio.v3 as iio
    import numpy as np
    img = iio.imread(src)
    # BC5 is RG-only (2 channels); pad to RGBA so PNG writers are happy
    if img.ndim == 3 and img.shape[2] == 2:
        h, w, _ = img.shape
        rgba = np.zeros((h, w, 4), dtype=img.dtype)
        rgba[:, :, 0] = img[:, :, 0]
        rgba[:, :, 1] = img[:, :, 1]
        img = rgba
    iio.imwrite(dst, img)


def try_wand(src, dst):
    from wand.image import Image
    with Image(filename=src) as img:
        img.format = 'png'
        img.save(filename=dst)


def try_pillow(src, dst):
    from PIL import Image
    Image.open(src).save(dst, 'PNG')


def try_texconv(src, dst):
    out_dir = os.path.dirname(dst)
    stem    = os.path.splitext(os.path.basename(src))[0]
    result  = subprocess.run(
        [TEXCONV, '-ft', 'png', '-o', out_dir, '-y', '-nologo', src],
        capture_output=True, text=True
    )
    expected = os.path.join(out_dir, stem + '.png')
    if os.path.exists(expected):
        if expected != dst:
            os.replace(expected, dst)
        return
    raise RuntimeError(result.stdout.strip() or result.stderr.strip() or 'no output file')


BACKENDS = [
    ('imageio', try_imageio),
    ('Wand',    try_wand),
    ('Pillow',  try_pillow),
    ('texconv', try_texconv),
]


def convert(src, dst):
    """Try each backend in order; raise if all fail."""
    errors = []
    for name, fn in BACKENDS:
        try:
            fn(src, dst)
            if os.path.exists(dst):
                return name
        except ImportError:
            pass
        except Exception as e:
            errors.append(f'{name}: {e}')
    raise RuntimeError('All backends failed:\n    ' + '\n    '.join(errors))


# ── Metadata parsing ──────────────────────────────────────────────────────────

def parse_texture_map(meta_path):
    """
    Parse ARCHIVE_METADATA to produce {texture_index: game_asset_path} for all 549 textures.

    The binary has two relevant structures:
      - A 1024-slot hash table at table_off (each 32-byte slot holds hash, str_abs, str_len,
        extra_lo/hi; extra_lo = TEXTURE_BASE + N for occupied slots).
      - A companion array at comp_off (549 u32 values, one per N) where comp[N] is the slot
        index in the 1024-slot table for texture_N.

    Using comp[N] lets us find every texture's path string regardless of which half of the
    table it lives in, recovering all 549 paths instead of just the 275 in the first 549 slots.
    """
    with open(meta_path, 'rb') as f:
        data = f.read()

    table_off = struct.unpack_from('<I', data, 0x0080)[0]
    comp_off  = struct.unpack_from('<I', data, 0x0098)[0]

    index_map = {}
    for n in range(N_TEXTURES):
        slot     = struct.unpack_from('<I', data, comp_off + n * 4)[0]
        off      = table_off + slot * 32
        if off + 32 > len(data):
            continue
        str_abs  = struct.unpack_from('<Q', data, off + 8)[0]
        str_len  = struct.unpack_from('<Q', data, off + 16)[0]
        if str_len > 0 and 0 < str_abs < len(data):
            path = data[str_abs:str_abs + str_len].decode('ascii', errors='replace')
            index_map[n] = path

    return index_map


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f'Parsing ARCHIVE_METADATA...')
    index_map = parse_texture_map(ARCHIVE_META)
    named   = len(index_map)
    unnamed = N_TEXTURES - named
    print(f'  {named} named textures (of {N_TEXTURES} total)')
    if unnamed:
        print(f'  {unnamed} textures still have no path -> _unmatched/')
    print()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    unmatched_dir = os.path.join(OUTPUT_DIR, '_unmatched')

    ok      = 0
    failed  = []   # (n, game_path, error_string)
    missing = []   # texture_N file not found on disk

    with tempfile.TemporaryDirectory() as tmp_dir:
        for n in range(N_TEXTURES):
            key      = f'texture_{n}'
            src_file = os.path.join(TEXTURE_DIR, key)

            if not os.path.exists(src_file):
                missing.append(n)
                print(f'  [MISSING] {key}')
                continue

            # Copy raw file to temp with .dds extension so backends recognise it
            tmp_dds = os.path.join(tmp_dir, key + '.dds')
            shutil.copy2(src_file, tmp_dds)

            game_path = index_map.get(n)

            if game_path:
                game_dir  = os.path.dirname(game_path)
                game_stem = os.path.splitext(os.path.basename(game_path))[0]
                out_subdir = os.path.join(OUTPUT_DIR, game_dir.replace('/', os.sep))
                os.makedirs(out_subdir, exist_ok=True)
                dst_png = os.path.join(out_subdir, game_stem + '.png')
                label   = f'{game_dir}/{game_stem}.png'
            else:
                os.makedirs(unmatched_dir, exist_ok=True)
                dst_png = os.path.join(unmatched_dir, key + '.png')
                label   = f'_unmatched/{key}.png'

            try:
                backend = convert(tmp_dds, dst_png)
                tag = f'OK:{backend:<8}' if game_path else 'UNMATCHED  '
                print(f'  [{tag}] {key} -> {label}')
                ok += 1
            except Exception as e:
                print(f'  [FAIL] {key} -> {label}')
                failed.append((n, label, str(e)))

            try:
                os.remove(tmp_dds)
            except OSError:
                pass

    # ── Summary ───────────────────────────────────────────────────────────────
    failed_ns = {f[0] for f in failed}
    print(f'\n{"="*60}')
    print(f'Done.')
    print(f'  Named ({named}): {sum(1 for n in range(N_TEXTURES) if n in index_map and n not in failed_ns)} converted')
    if unnamed:
        print(f'  Unmatched ({unnamed}): saved to _unmatched/')
    print(f'  Failed:          {len(failed)}')
    if missing:
        print(f'  Missing on disk: {len(missing)}')
    print(f'Output: {OUTPUT_DIR}')

    if failed:
        ns_str = ', '.join(str(f[0]) for f in failed)
        print(f'\nFailed ({len(failed)}) — copy-paste for debugging:')
        print(f'  FAILED_N = [{ns_str}]')
        print()
        for n, label, err in failed:
            print(f'  texture_{n} ({label}):')
            for line in err.splitlines():
                print(f'    {line}')


if __name__ == '__main__':
    main()
