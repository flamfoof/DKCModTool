"""Search for actual hairstyle unlock status values in stageBase_EN.DAT."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Searching for hairstyle unlock status values:")
print("=" * 70)

data = read_stagebase()

# Common unlock status values
UNLOCK_VALUES = [0x5A, 0x1E, 0x78]

print("\nSearching for unlock status values (0x5A, 0x1E, 0x78):")
for val in UNLOCK_VALUES:
    count = data.count(val)
    print(f"Value 0x{val:02X} ({val}): found {count} occurrences")
    
    # Show first few occurrences with context
    offset = data.find(val)
    if offset >= 0:
        context_start = max(0, offset - 8)
        context_end = min(len(data), offset + 16)
        print(f"  First at 0x{offset:X}: {data[context_start:context_end].hex()}")

# Search for patterns that might be hairstyle unlock tables
print("\nSearching for potential unlock table patterns:")

# Look for sequences of unlock values near the hairstyle name table
# Hairstyle name table is around 0xBCD0 according to README
HAIRSTYLE_NAME_REGION = 0xBCD0

print(f"\nSearching near hairstyle name table (0x{HAIRSTYLE_NAME_REGION:X}):")
for offset in range(HAIRSTYLE_NAME_REGION - 0x1000, HAIRSTYLE_NAME_REGION + 0x1000):
    if offset + 2 < len(data):
        val = struct.unpack('<H', data[offset:offset+2])[0]
        if val in UNLOCK_VALUES:
            context_start = max(0, offset - 16)
            context_end = min(len(data), offset + 32)
            print(f"0x{offset:X}: 0x{val:04X} - {data[context_start:context_end].hex()}")

print("\n" + "=" * 70)
