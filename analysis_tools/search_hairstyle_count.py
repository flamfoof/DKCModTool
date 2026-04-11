"""Search for hairstyle unlock count near hairstyle name table."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Searching for hairstyle unlock count near name table:")
print("=" * 70)

data = read_stagebase()

# Search near hairstyle name table
HAIRSTYLE_NAME_REGION = 0xBCD0

print(f"\nSearching for value 3 (initial unlock count) near 0x{HAIRSTYLE_NAME_REGION:X}:")
for offset in range(HAIRSTYLE_NAME_REGION - 0x200, HAIRSTYLE_NAME_REGION + 0x200):
    if offset + 1 < len(data):
        val = data[offset]
        if val == 3:
            context_start = max(0, offset - 16)
            context_end = min(len(data), offset + 16)
            context = data[context_start:context_end]
            
            # Only show if it looks like a count in a structured context
            # (has zeros or other small integers around it)
            if all(v < 20 for v in context):
                print(f"0x{offset:X}: {context.hex()}")

# Also search for value 14 (total hairstyles)
print(f"\nSearching for value 14 (total hairstyles) near 0x{HAIRSTYLE_NAME_REGION:X}:")
for offset in range(HAIRSTYLE_NAME_REGION - 0x200, HAIRSTYLE_NAME_REGION + 0x200):
    if offset + 1 < len(data):
        val = data[offset]
        if val == 14:
            context_start = max(0, offset - 16)
            context_end = min(len(data), offset + 16)
            context = data[context_start:context_end]
            print(f"0x{offset:X}: {context.hex()}")

print("\n" + "=" * 70)
