#!/usr/bin/env python3
"""
Search for specific localization strings in the decomp directory.
Run: python search_strings.py
"""
from pathlib import Path

TARGET_STRINGS = [
    "Afterimage",
    "Analyser",
    "Analyzer",  # US spelling
    "Black Widow",
    "Bird of Prey",
]

def search_file(file_path: Path, targets: list[str]) -> list[tuple[str, int]]:
    """Search for target strings in a file. Returns list of (string_found, byte_offset)."""
    matches = []
    try:
        with file_path.open('rb') as f:
            data = f.read()
        
        for target in targets:
            # UTF-8
            encoded = target.encode('utf-8')
            offset = 0
            while True:
                pos = data.find(encoded, offset)
                if pos == -1:
                    break
                matches.append((target, pos))
                offset = pos + 1
            
            # UTF-16 LE
            encoded_utf16 = target.encode('utf-16-le')
            offset = 0
            while True:
                pos = data.find(encoded_utf16, offset)
                if pos == -1:
                    break
                matches.append((f"{target} (UTF-16)", pos))
                offset = pos + 2
    except Exception as e:
        pass
    return matches

def main():
    decomp_dir = Path(r'd:\mio\decomp')
    if not decomp_dir.exists():
        print(f"Decomp directory not found: {decomp_dir}")
        return
    
    print(f"Searching for: {TARGET_STRINGS}")
    print("-" * 50)
    
    found_any = False
    count = 0
    for file_path in decomp_dir.rglob('*'):
        if not file_path.is_file():
            continue
        size = file_path.stat().st_size
        if size == 0 or size > 5_000_000:  # Skip empty and files > 5MB (likely textures)
            continue
        count += 1
        if count % 5000 == 0:
            print(f"Scanned {count} files...")
        matches = search_file(file_path, TARGET_STRINGS)
        if matches:
            found_any = True
            rel_path = file_path.relative_to(decomp_dir)
            print(f"\n{rel_path}")
            seen = set()
            for s, offset in matches:
                if (s, offset) not in seen:
                    seen.add((s, offset))
                    print(f"  -> {s} at offset {offset}")
    
    if not found_any:
        print("No matches found. Strings may be in a different encoding or format.")

if __name__ == '__main__':
    main()
