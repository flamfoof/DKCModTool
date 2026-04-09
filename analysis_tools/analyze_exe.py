"""Quick analysis of DkkStm.exe PE structure to find key offsets."""
import struct
import sys

EXE_PATH = r"Backup\DkkStm.exe"

def read_pe_header(data):
    # DOS header
    dos_magic = data[0:2]
    print(f"DOS Magic: {dos_magic}")
    pe_offset = struct.unpack_from('<I', data, 0x3C)[0]
    print(f"PE Header Offset: 0x{pe_offset:X}")
    
    # PE signature
    pe_sig = data[pe_offset:pe_offset+4]
    print(f"PE Signature: {pe_sig}")
    
    # COFF header
    coff_offset = pe_offset + 4
    machine = struct.unpack_from('<H', data, coff_offset)[0]
    num_sections = struct.unpack_from('<H', data, coff_offset + 2)[0]
    timestamp = struct.unpack_from('<I', data, coff_offset + 4)[0]
    opt_header_size = struct.unpack_from('<H', data, coff_offset + 16)[0]
    
    print(f"Machine: 0x{machine:X}")
    print(f"Number of Sections: {num_sections}")
    print(f"Timestamp: 0x{timestamp:X}")
    print(f"Optional Header Size: 0x{opt_header_size:X}")
    
    # Optional header
    opt_offset = coff_offset + 20
    opt_magic = struct.unpack_from('<H', data, opt_offset)[0]
    print(f"Optional Header Magic: 0x{opt_magic:X} ({'PE32+' if opt_magic == 0x20b else 'PE32'})")
    
    if opt_magic == 0x20b:  # PE32+
        image_base = struct.unpack_from('<Q', data, opt_offset + 24)[0]
        section_align = struct.unpack_from('<I', data, opt_offset + 32)[0]
        file_align = struct.unpack_from('<I', data, opt_offset + 36)[0]
        size_of_image = struct.unpack_from('<I', data, opt_offset + 56)[0]
        size_of_headers = struct.unpack_from('<I', data, opt_offset + 60)[0]
    else:
        image_base = struct.unpack_from('<I', data, opt_offset + 28)[0]
        section_align = struct.unpack_from('<I', data, opt_offset + 32)[0]
        file_align = struct.unpack_from('<I', data, opt_offset + 36)[0]
        size_of_image = struct.unpack_from('<I', data, opt_offset + 56)[0]
        size_of_headers = struct.unpack_from('<I', data, opt_offset + 60)[0]
    
    print(f"Image Base: 0x{image_base:X}")
    print(f"Section Alignment: 0x{section_align:X}")
    print(f"File Alignment: 0x{file_align:X}")
    print(f"Size of Image: 0x{size_of_image:X}")
    print(f"Size of Headers: 0x{size_of_headers:X}")
    
    # Section headers
    section_offset = opt_offset + opt_header_size
    print(f"\nSection headers start at: 0x{section_offset:X}")
    print(f"{'Name':<12} {'VirtSize':>10} {'VirtAddr':>10} {'RawSize':>10} {'RawAddr':>10} {'Chars':>10}")
    print("-" * 70)
    
    sections = []
    for i in range(num_sections):
        off = section_offset + i * 40
        name = data[off:off+8].rstrip(b'\x00').decode('ascii', errors='replace')
        virt_size = struct.unpack_from('<I', data, off + 8)[0]
        virt_addr = struct.unpack_from('<I', data, off + 12)[0]
        raw_size = struct.unpack_from('<I', data, off + 16)[0]
        raw_addr = struct.unpack_from('<I', data, off + 20)[0]
        chars = struct.unpack_from('<I', data, off + 36)[0]
        print(f"{name:<12} 0x{virt_size:08X} 0x{virt_addr:08X} 0x{raw_size:08X} 0x{raw_addr:08X} 0x{chars:08X}")
        sections.append({
            'name': name, 'virt_size': virt_size, 'virt_addr': virt_addr,
            'raw_size': raw_size, 'raw_addr': raw_addr, 'chars': chars
        })
    
    # Old DKCedit values for comparison
    print("\n--- Old DKCedit hardcoded values ---")
    print(f"SECTION_OFFSET (num sections):     0x15E")
    print(f"SECTION_HEADER_OFFSET (new sect):  0x378")
    print(f"DEFAULT_SECTIONS:                  7")
    print(f"VIRTUAL_OFFSET:                    0xB05000")
    print(f"RAW_OFFSET:                        0x5DEA00")
    print(f"IMAGE_SIZE:                        0xB07000")
    
    # Calculate where the current values are
    num_sec_offset = coff_offset + 2
    print(f"\n--- Current exe values ---")
    print(f"Number of sections offset:         0x{num_sec_offset:X}")
    print(f"Number of sections:                {num_sections}")
    print(f"First section header offset:       0x{section_offset:X}")
    print(f"File size:                         0x{len(data):X} ({len(data)} bytes)")
    
    # Last section info
    last = sections[-1]
    last_end_raw = last['raw_addr'] + last['raw_size']
    last_end_virt = last['virt_addr'] + last['virt_size']
    # Align to section alignment
    import math
    next_virt = math.ceil(last_end_virt / section_align) * section_align
    next_raw = last_end_raw  # usually file-aligned
    
    print(f"Last section ends at raw:          0x{last_end_raw:X}")
    print(f"Last section ends at virt:         0x{last_end_virt:X}")
    print(f"Next available virt addr:          0x{next_virt:X}")
    print(f"Next available raw addr:           0x{next_raw:X}")
    
    # Space after last section header for adding new section
    last_sec_header_end = section_offset + num_sections * 40
    print(f"Section headers end at:            0x{last_sec_header_end:X}")
    print(f"First section raw data starts at:  0x{sections[0]['raw_addr']:X}")
    avail_header_space = sections[0]['raw_addr'] - last_sec_header_end
    print(f"Available header space:            0x{avail_header_space:X} ({avail_header_space} bytes)")
    
    # Check for stageBase data patterns
    print("\n--- Searching for known data patterns ---")
    
    # Look for "stageBase" string
    idx = data.find(b'stageBase')
    if idx >= 0:
        print(f"'stageBase' string found at: 0x{idx:X}")
    
    # Look for "Attack" strings (damage formula)
    for pattern in [b'BC  CR', b'BC * CR', b'Attack(']:
        idx = 0
        count = 0
        while True:
            idx = data.find(pattern, idx)
            if idx < 0:
                break
            if count < 3:
                print(f"'{pattern.decode()}' found at: 0x{idx:X}")
            count += 1
            idx += 1
        if count > 3:
            print(f"  ... ({count} total occurrences)")
    
    # Look for known class name strings
    for pattern in [b'Warrior\x00', b'Magician\x00', b'Thief\x00', b'Cleric\x00']:
        idx = data.find(pattern)
        if idx >= 0:
            print(f"'{pattern[:-1].decode()}' found at: 0x{idx:X}")

    # Scan for the old DKCedit section marker
    idx = data.find(b'.dkcedit')
    if idx >= 0:
        print(f"'.dkcedit' section found at: 0x{idx:X} (already modded!)")
    else:
        print("'.dkcedit' section NOT found (unmodded exe)")
    
    # Check DKCedit build string
    idx = data.find(b'DKCedit')
    if idx >= 0:
        print(f"'DKCedit' string found at: 0x{idx:X}")
    
    return sections, num_sections, section_offset, size_of_image, pe_offset, opt_offset, opt_magic

def scan_data_tables(data, sections):
    """Scan for game data structures based on known patterns from the changelog."""
    print("\n=== Scanning for game data tables ===\n")
    
    # From the changelog, we know offsets like 0x1884E for bag data, 0x185AE for level-up data
    # These are offsets into a specific asset file (stageBase_EN.DAT), NOT into the exe directly
    # But let's look for them in the exe too
    
    # Search for the stageBase data within the exe
    # Known pattern: Warrior bag = 06 04 (original), items at offset 0x1884E in stageBase
    # Let's find where stageBase data is embedded in the exe
    
    # Let's search for known byte sequences from the changelog
    # Warrior original bag: offset 0x1884E in stageBase should have the values
    
    # Search for patterns that might indicate job/class data tables
    # Warrior level up original: +2A +1D +1H = 02 00 01 00 00 00 00 00 01 00
    warrior_levelup = bytes([0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00])
    idx = 0
    while True:
        idx = data.find(warrior_levelup, idx)
        if idx < 0:
            break
        print(f"Warrior level-up pattern at: 0x{idx:X}")
        idx += 1
    
    # Warrior bag original: 06 04 
    # Look for class bag data pattern (6 classes in a row)
    # Warrior 06/04, Magician 06/0A, Thief 08/06, Cleric 06/08
    bag_pattern = bytes([0x06, 0x04])  # too generic, let's try wider
    
    # Known hex: stageBase offset 0x14F08 has M Guard DX at 90% (0x5A)
    # Let's search for that
    
    print("\nLooking for identifiable game strings...")
    for s in [b'Escape\x00', b'Celerity\x00', b'Alchemy\x00', b'Poison\x00', b'M Guard\x00', 
              b'Bounce\x00', b'Mirror\x00', b'Hero License\x00', b'Angel Wings\x00',
              b'Gold Voucher\x00', b'DkkStm.exe\x00']:
        idx = data.find(s)
        if idx >= 0:
            print(f"  '{s[:-1].decode()}' at 0x{idx:X}")
        else:
            # Try with different encoding
            pass

with open(EXE_PATH, 'rb') as f:
    data = f.read()

print(f"File size: {len(data)} bytes (0x{len(data):X})")
print()
sections, num_sections, section_offset, size_of_image, pe_offset, opt_offset, opt_magic = read_pe_header(data)
scan_data_tables(data, sections)
