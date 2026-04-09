"""Analyze stageBase_EN.DAT and the exe to understand game data structures."""
import struct
import os

STAGEBASE = r"Mods\JaJo's Balance Patch v1.0.1\Assets\stageBase_EN.DAT"
EXE_PATH = r"Backup\DkkStm.exe"

def analyze_stagebase(path):
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"=== stageBase_EN.DAT Analysis ===")
    print(f"File size: {len(data)} bytes (0x{len(data):X})")
    
    # Check header
    print(f"\nFirst 64 bytes (hex):")
    for i in range(0, min(64, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  0x{i:06X}: {hex_str}  {ascii_str}")
    
    # Look for text strings to understand the format
    print(f"\nSearching for ASCII strings...")
    strings_found = []
    current = b""
    start = 0
    for i, b in enumerate(data):
        if 32 <= b < 127:
            if not current:
                start = i
            current += bytes([b])
        else:
            if len(current) >= 4:
                strings_found.append((start, current.decode('ascii', errors='replace')))
            current = b""
    
    print(f"Found {len(strings_found)} strings (>= 4 chars)")
    print(f"\nFirst 50 strings:")
    for offset, s in strings_found[:50]:
        print(f"  0x{offset:06X}: {s[:80]}")
    
    # Look for known game data patterns
    # From changelog: offset 0x1884E should have bag data for Warrior
    # Original: 06 04 (6 items, 4 magic)
    print(f"\n=== Known data locations from changelog ===")
    
    offsets_to_check = {
        0x1884E: "Warrior bag (item/magic)",
        0x18856: "Warrior bag (2nd copy)", 
        0x1885E: "Magician bag",
        0x18866: "Magician bag (2nd)",
        0x1886E: "Thief bag",
        0x18876: "Thief bag (2nd)",
        0x1887E: "Cleric bag",
        0x18886: "Cleric bag (2nd)",
        0x188BE: "Monk bag",
        0x188C6: "Monk bag (2nd)",
        0x185AE: "Warrior level-up stats",
        0x185CA: "Warrior level-up stats (2nd)",
        0x18360: "Thief skill",
        0x1836C: "Thief skill (2nd)",
        0x14F08: "M Guard DX percentage",
        0xB0DEC: "Attack damage formula text",
        0x51CC: "Clovis shop",
        0x1B041: "Rogue def magic",
        0x1A670: "Squeeze status duration",
    }
    
    for offset, desc in sorted(offsets_to_check.items()):
        if offset < len(data):
            chunk = data[offset:offset+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f"  0x{offset:06X} [{desc}]: {hex_str}")
        else:
            print(f"  0x{offset:06X} [{desc}]: OUT OF BOUNDS")
    
    # Look for table structures - search for repeating patterns
    # Job data typically has fixed-size records
    print(f"\n=== Searching for data table headers ===")
    
    # Look for the text of damage formula
    for pattern in [b'BC  CR', b'BC * CR', b'Attack']:
        idx = 0
        while True:
            idx = data.find(pattern, idx)
            if idx < 0:
                break
            context = data[max(0,idx-4):idx+30]
            hex_str = ' '.join(f'{b:02X}' for b in context)
            print(f"  '{pattern.decode()}' at 0x{idx:X}: {hex_str}")
            idx += 1

    # Try to find class/job name references
    for name in [b'Warrior', b'Magician', b'Thief', b'Cleric', b'Alchemist', b'Monk', b'Acrobat', b'Ninja', b'Hero']:
        idx = data.find(name)
        if idx >= 0:
            print(f"  '{name.decode()}' at 0x{idx:X}")

def analyze_exe_data(path):
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"\n=== EXE data analysis ===")
    print(f"File size: {len(data)} bytes")
    
    # Search for game string tables in the exe
    print("\nSearching for game-related strings in exe...")
    
    game_strings = [b'Warrior', b'Magician', b'Thief', b'Cleric', b'Alchemist', 
                    b'Monk', b'Acrobat', b'Ninja', b'Hero\x00',
                    b'Attack\x00', b'Defense\x00', b'Magic\x00', b'Speed\x00',
                    b'M Guard', b'Bounce', b'Mirror', b'Escape', b'Celerity',
                    b'stageBase', b'DkkStm', b'Dokapon']
    
    for pattern in game_strings:
        idx = 0
        locs = []
        while True:
            idx = data.find(pattern, idx)
            if idx < 0:
                break
            locs.append(idx)
            idx += 1
        if locs:
            loc_str = ', '.join(f'0x{l:X}' for l in locs[:5])
            extra = f" (+{len(locs)-5} more)" if len(locs) > 5 else ""
            print(f"  '{pattern.rstrip(b'\\x00').decode('ascii', errors='replace')}': {loc_str}{extra}")

    # Look for Chinese/CJK characters (UTF-8 encoded)
    # Chinese chars in UTF-8 are 3 bytes: 0xE0-0xEF, 0x80-0xBF, 0x80-0xBF
    print("\nScanning for Chinese/CJK character data regions...")
    cjk_regions = []
    i = 0
    region_start = None
    cjk_count = 0
    while i < len(data) - 2:
        b1, b2, b3 = data[i], data[i+1], data[i+2]
        if 0xE4 <= b1 <= 0xE9 and 0x80 <= b2 <= 0xBF and 0x80 <= b3 <= 0xBF:
            if region_start is None:
                region_start = i
            cjk_count += 1
            i += 3
        else:
            if cjk_count >= 10:
                cjk_regions.append((region_start, i, cjk_count))
            region_start = None
            cjk_count = 0
            i += 1
    
    print(f"Found {len(cjk_regions)} regions with CJK data")
    for start, end, count in cjk_regions[:10]:
        section = "unknown"
        if start < 0x44BA00:
            section = ".text"
        elif start < 0x4F2200:
            section = ".rdata"
        elif start < 0x5B2600:
            section = ".data"
        elif start < 0x5D1E00:
            section = ".pdata"
        elif start < 0x5D2600:
            section = ".rodata/_RDATA"
        elif start < 0x657000:
            section = ".rsrc"
        else:
            section = ".reloc"
        print(f"  0x{start:X} - 0x{end:X} ({count} CJK chars, section: {section})")
    if len(cjk_regions) > 10:
        print(f"  ... and {len(cjk_regions) - 10} more regions")

    # Find where the .rsrc section contains game resources
    # .rsrc starts at raw 0x5D2600
    print(f"\nResource section (.rsrc) analysis:")
    rsrc_start = 0x5D2600
    rsrc_size = 0x84A00
    print(f"  Start: 0x{rsrc_start:X}, Size: 0x{rsrc_size:X}")
    # Check first bytes of rsrc
    rsrc_header = data[rsrc_start:rsrc_start+64]
    hex_str = ' '.join(f'{b:02X}' for b in rsrc_header)
    print(f"  Header: {hex_str}")

analyze_stagebase(STAGEBASE)
analyze_exe_data(EXE_PATH)
