#!/usr/bin/env python3
"""
Extract readable strings from binary files in the decomp directory.
Looks for UTF-8 and UTF-16 strings that might contain localization data.
"""
import os
import re
from pathlib import Path
from typing import Set

def extract_strings_utf8(data: bytes, min_length: int = 4) -> Set[str]:
    """Extract UTF-8 strings from binary data."""
    strings = set()
    try:
        text = data.decode('utf-8', errors='ignore')
        # Find sequences of printable characters (including some Unicode)
        pattern = r'[\x20-\x7E\u00A0-\uFFFF]{' + str(min_length) + ',}'
        matches = re.findall(pattern, text)
        strings.update(matches)
    except:
        pass
    return strings

def extract_strings_utf16(data: bytes, min_length: int = 4) -> Set[str]:
    """Extract UTF-16LE strings from binary data."""
    strings = set()
    try:
        # Try little-endian first
        text = data.decode('utf-16-le', errors='ignore')
        pattern = r'[\x20-\x7E\u00A0-\uFFFF]{' + str(min_length) + ',}'
        matches = re.findall(pattern, text)
        strings.update(matches)
    except:
        pass
    try:
        # Try big-endian
        text = data.decode('utf-16-be', errors='ignore')
        pattern = r'[\x20-\x7E\u00A0-\uFFFF]{' + str(min_length) + ',}'
        matches = re.findall(pattern, text)
        strings.update(matches)
    except:
        pass
    return strings

def extract_ascii_strings(data: bytes, min_length: int = 4) -> Set[str]:
    """Extract ASCII strings (printable characters only)."""
    strings = set()
    # Find sequences of printable ASCII
    pattern = rb'[\x20-\x7E]{' + str(min_length).encode() + rb',}'
    matches = re.findall(pattern, data)
    for match in matches:
        try:
            strings.add(match.decode('ascii'))
        except:
            pass
    return strings

def scan_file(file_path: Path, min_length: int = 6) -> Set[str]:
    """Extract all strings from a file."""
    all_strings = set()
    
    try:
        with file_path.open('rb') as f:
            data = f.read()
        
        # Skip empty or very small files
        if len(data) < min_length:
            return all_strings
        
        # Extract from different encodings
        all_strings.update(extract_ascii_strings(data, min_length))
        all_strings.update(extract_strings_utf8(data, min_length))
        all_strings.update(extract_strings_utf16(data, min_length))
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return all_strings

def filter_relevant_strings(strings: Set[str]) -> Set[str]:
    """Filter strings that might be localization-related."""
    relevant = set()
    
    # Keywords that suggest localization
    keywords = [
        'localization', 'localisation', 'locale', 'lang', 'language',
        'dialogue', 'dialog', 'speech', 'text', 'string', 'ui',
        'menu', 'button', 'option', 'choice', 'quest', 'npc',
        'item', 'description', 'name', 'title', 'subtitle'
    ]
    
    for s in strings:
        s_lower = s.lower()
        # Check if string contains keywords or looks like dialogue/UI text
        if any(kw in s_lower for kw in keywords):
            relevant.add(s)
        # Check if it looks like a sentence (contains spaces, punctuation, multiple words)
        elif ' ' in s and len(s.split()) >= 3:
            relevant.add(s)
        # Check if it's a key-value pattern (common in localization)
        elif ':' in s or '=' in s:
            relevant.add(s)
    
    return relevant

def main():
    decomp_dir = Path(r'd:\mio\decomp')
    output_file = Path(r'd:\mio\extracted_strings.txt')
    relevant_output = Path(r'd:\mio\relevant_strings.txt')
    
    if not decomp_dir.exists():
        print(f"Decomp directory not found: {decomp_dir}")
        return
    
    print(f"Scanning {decomp_dir} for strings...")
    all_strings = set()
    file_count = 0
    
    # Scan all files
    for file_path in decomp_dir.rglob('*'):
        if file_path.is_file():
            file_count += 1
            if file_count % 100 == 0:
                print(f"Processed {file_count} files, found {len(all_strings)} unique strings...")
            
            strings = scan_file(file_path)
            all_strings.update(strings)
    
    print(f"\nScanned {file_count} files")
    print(f"Found {len(all_strings)} unique strings")
    
    # Write all strings
    with output_file.open('w', encoding='utf-8') as f:
        for s in sorted(all_strings):
            f.write(f"{s}\n")
    
    print(f"All strings written to: {output_file}")
    
    # Filter and write relevant strings
    relevant = filter_relevant_strings(all_strings)
    print(f"Found {len(relevant)} potentially relevant strings")
    
    with relevant_output.open('w', encoding='utf-8') as f:
        for s in sorted(relevant):
            f.write(f"{s}\n")
    
    print(f"Relevant strings written to: {relevant_output}")

if __name__ == '__main__':
    main()
