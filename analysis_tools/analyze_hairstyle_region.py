"""Analyze the hairstyle name table region to find unlock data."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Analyzing hairstyle name table region (0xBCD0):")
print("=" * 70)

data = read_stagebase()

# Hairstyle name table region
HAIRSTYLE_NAME_REGION = 0xBCD0

# Hex dump the region
print(f"\nHex dump of hairstyle name table region (0x{HAIRSTYLE_NAME_REGION:X}):")
for i in range(0, 256, 16):
    offset = HAIRSTYLE_NAME_REGION + i
    chunk = data[offset:offset+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"  0x{offset:X}: {hex_str} {ascii_str}")

# Look for patterns that might be hairstyle entries
print("\nSearching for hairstyle entry patterns:")
# Hairstyle entries might have a structure like: [name_offset, unlock_status, ...]
# Look for patterns where unlock_status (0x5A/0x1E) appears near text

for offset in range(HAIRSTYLE_NAME_REGION, HAIRSTYLE_NAME_REGION + 0x1000, 2):
    if offset + 4 < len(data):
        val1 = struct.unpack('<H', data[offset:offset+2])[0]
        val2 = struct.unpack('<H', data[offset+2:offset+4])[0]
        
        # Check if this looks like an entry with unlock status
        if val1 in [0x5A, 0x1E, 0x78] or val2 in [0x5A, 0x1E, 0x78]:
            context_start = max(0, offset - 8)
            context_end = min(len(data), offset + 16)
            print(f"0x{offset:X}: {data[context_start:context_end].hex()}")

print("\n" + "=" * 70)
