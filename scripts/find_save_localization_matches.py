#!/usr/bin/env python3
"""
Cross-reference save keys with localization data.
Finds save keys (CATEGORY:ITEM) whose ITEM exists in any localization category.
Outputs to extracted_strings/save_keys_with_localization.json
"""
import json
from pathlib import Path


def main():
    out_dir = Path(r"d:\mio\extracted_strings")
    loc_path = out_dir / "localization.json"
    save_keys_path = out_dir / "save_keys.json"
    out_path = out_dir / "save_keys_with_localization.json"

    if not loc_path.exists() or not save_keys_path.exists():
        print("Missing localization.json or save_keys.json")
        return

    loc = json.loads(loc_path.read_text(encoding="utf-8"))
    save_keys = json.loads(save_keys_path.read_text(encoding="utf-8"))

    # Set of all item keys that have localization
    localized_keys = set()
    for cat, items in loc.items():
        if isinstance(items, dict):
            for key in items:
                localized_keys.add(key)

    # Find save keys whose ITEM is localized
    result = {}
    for save_cat, items in save_keys.items():
        matched = [item for item in items if item in localized_keys]
        if matched:
            result[save_cat] = matched

    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    total = sum(len(v) for v in result.values())
    print(f"  save_keys_with_localization.json: {total} save keys with localization across {len(result)} categories")


if __name__ == "__main__":
    main()
