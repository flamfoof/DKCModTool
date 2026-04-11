"""Map out hairstyle data structures in detail."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def read_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

def read_string(data, offset, max_len=64):
    end = offset
    while end < offset + max_len and data[end] != 0:
        end += 1
    return data[offset:end].decode('ascii', errors='replace')

def hexdump(data, offset, length=64):
    result = []
    for i in range(0, length, 16):
        chunk = data[offset+i:offset+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"  0x{offset+i:06X}: {hex_str:<48} {ascii_str}")
    return '\n'.join(result)

print("=" * 70)
print("HAIRSTYLE NAME TABLE ANALYSIS (0xBCD0)")
print("=" * 70)

data = read_stagebase()

# The hairstyle names appear to be in a structured table starting around 0xBCD0
# Let's analyze this region in detail
print("\nHairstyle name region (0xBCD0):")
print(hexdump(data, 0xBCD0, 128))

# Look for the pattern from the earlier analysis:
# 0xBCF0: "Punk" with 01 02 4B 37 19 28 41 01 96 00 00 00 1A 04 68 00
print("\nDetailed analysis of each entry:")

# The pattern seems to be:
# [variant_id, ?, ?, ?, ?, ?, ?, ?, 96 00 00 00 XX 04 68 00, name]
# where XX is the hairstyle ID (1A=26 for Punk? or maybe 1A=26 decimal)

# Let's parse the entries
offset = 0xBCD0
entry_num = 1
while offset < 0xBE00:
    # Look for the pattern 96 00 00 00
    pattern_pos = data.find(b'\x96\x00\x00\x00', offset)
    if pattern_pos < 0 or pattern_pos >= 0xBE00:
        break
    
    # Check if there's a name after 68 00
    name_pos = pattern_pos + 8
    if name_pos + 4 < len(data) and data[name_pos:name_pos+2] == b'\x68\x00':
        name = read_string(data, name_pos + 2, 32)
        id_byte = data[pattern_pos + 4]
        print(f"\nEntry {entry_num} at 0x{pattern_pos:X}:")
        print(f"  ID byte: 0x{id_byte:02X} ({id_byte})")
        print(f"  Name: '{name}'")
        print(hexdump(data, pattern_pos - 8, 48))
        entry_num += 1
        offset = name_pos + len(name) + 1
    else:
        offset = pattern_pos + 1

print("\n" + "=" * 70)
print("HAIRSTYLE TABLE STRUCTURE ANALYSIS (0x18A70)")
print("=" * 70)

print("\nHairstyle table region (0x18A70):")
print(hexdump(data, 0x18A70, 96))

# The pattern shows:
# 01 00 5A 00 02 00 01 00 03 00 02 00 04 00 01 00 01 00 5A 00...
# This looks like pairs of [id, value]
# Let's parse it as pairs
print("\nParsing as [id, value] pairs:")
offset = 0x18A70
pair_count = 0
while offset < 0x18AE0:
    id_val = read_uint16(data, offset)
    val = read_uint16(data, offset + 2)
    print(f"  0x{offset:X}: ID={id_val}, Value=0x{val:04X} ({val})")
    offset += 4
    pair_count += 1
    if pair_count >= 24:
        break

# The FF FF markers might indicate the end of a group or a different data type
print("\n" + "=" * 70)
print("SEARCHING FOR HAIRSTYLE UNLOCK FLAGS")
print("=" * 70)

# Look for byte patterns that might be unlock bitfields
# For 6 hairstyles, we'd expect a 6-bit field or similar
# Let's search for patterns near the hairstyle table

print("\nData around hairstyle table (0x18A00):")
print(hexdump(data, 0x18A00, 256))

# Look for the job unlock table at 0x18B60 (from data_tables.py)
print("\nJob unlock table (0x18B60) for reference:")
print(hexdump(data, 0x18B60, 64))

# The hairstyle table at 0x18A70 is right before job unlock
# Let's see if there's a similar structure for hairstyles
print("\nComparing hairstyle table (0x18A70) with job unlock (0x18B60):")
print("Hairstyle table entry size might be similar")

# Let's try to find where the actual hairstyle unlock data is stored
# It might be in the player data structure or a global unlock table

print("\n" + "=" * 70)
print("SEARCHING FOR HAIRSTYLE MODEL REFERENCES")
print("=" * 70)

# Search for q00, q01, q02, q03, q04, q05 patterns (hairstyle model prefixes)
for q_num in range(6):
    pattern = f"q0{q_num}".encode('ascii')
    offset = data.find(pattern)
    if offset >= 0:
        print(f"\nFound 'q0{q_num}' at 0x{offset:X}:")
        print(hexdump(data, max(0, offset-16), 64))

# Also search for the full model path pattern
offset = data.find(b'dataChrSel')
if offset >= 0:
    print(f"\nFound 'dataChrSel' at 0x{offset:X}:")
    print(hexdump(data, offset, 128))

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
