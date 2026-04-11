"""Deep analysis of hairstyle unlock mechanism."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Deep analysis of hairstyle unlock mechanism:")
print("=" * 70)

data = read_stagebase()

# Hairstyle name table region
HAIRSTYLE_NAME_START = 0xBCD0

print("\nHairstyle name entries (looking for pattern):")
for i in range(14):  # 14 hairstyles
    entry_offset = HAIRSTYLE_NAME_START + i * 32  # Assuming 32-byte entries
    if entry_offset + 32 > len(data):
        break
    
    entry = data[entry_offset:entry_offset+32]
    # Extract name (look for text)
    name = ""
    for j in range(32):
        if 32 <= entry[j] < 127:
            name += chr(entry[j])
        elif entry[j] == 0 and name:
            break
    
    print(f"Hairstyle {i}: 0x{entry_offset:X} - {name:20s} - {entry.hex()}")

# Look for a bitmask or array that controls unlock status
print("\nSearching for unlock bitmask/arrays:")

# Look for patterns of 0/1 or FF/00 that might be bitmasks
# Search near the hairstyle name table
REGION_START = 0xBC00
REGION_END = 0xBD00

print(f"\nSearching for bitmask patterns in region 0x{REGION_START:X}-0x{REGION_END:X}:")
for offset in range(REGION_START, REGION_END):
    if offset + 4 < len(data):
        # Look for patterns like 00 00 00 01, 00 00 00 03, etc. (bitmasks)
        val = struct.unpack('<I', data[offset:offset+4])[0]
        if val in [0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF]:
            context_start = max(0, offset - 8)
            context_end = min(len(data), offset + 16)
            print(f"0x{offset:X}: {data[context_start:context_end].hex()} (mask: 0x{val:08X})")

# Look for arrays of small integers (0-13) that might be hairstyle IDs
print(f"\nSearching for hairstyle ID arrays (0-13):")
for offset in range(REGION_START, REGION_END):
    if offset + 16 < len(data):
        # Look for sequence of small integers
        vals = [data[offset + i] for i in range(16)]
        if all(v < 20 for v in vals):  # All small values
            if sum(vals) > 0:  # Not all zeros
                context_start = max(0, offset - 4)
                context_end = min(len(data), offset + 20)
                print(f"0x{offset:X}: {data[context_start:context_end].hex()} - {vals}")

print("\n" + "=" * 70)
