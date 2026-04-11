"""Find all hairstyle unlock status values in the correct region."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Finding all hairstyle unlock status values:")
print("=" * 70)

data = read_stagebase()

# Search region around hairstyle names
REGION_START = 0xBCD0
REGION_END = 0xC200

print(f"\nSearching for 0x1E (locked) values in region 0x{REGION_START:X}-0x{REGION_END:X}:")

unlock_offsets = []
for offset in range(REGION_START, REGION_END):
    if offset + 2 < len(data):
        val = struct.unpack('<H', data[offset:offset+2])[0]
        if val == 0x1E:
            context_start = max(0, offset - 8)
            context_end = min(len(data), offset + 16)
            print(f"0x{offset:X}: {data[context_start:context_end].hex()}")
            unlock_offsets.append(offset)

print(f"\nFound {len(unlock_offsets)} potential unlock status offsets")

# Also check for 0x5A values to see which are already unlocked
print("\nSearching for 0x5A (unlocked) values in same region:")
unlocked_offsets = []
for offset in range(REGION_START, REGION_END):
    if offset + 2 < len(data):
        val = struct.unpack('<H', data[offset:offset+2])[0]
        if val == 0x5A:
            context_start = max(0, offset - 8)
            context_end = min(len(data), offset + 16)
            print(f"0x{offset:X}: {data[context_start:context_end].hex()}")
            unlocked_offsets.append(offset)

print(f"Found {len(unlocked_offsets)} unlocked status offsets")

print("\n" + "=" * 70)
print("CORRECT HEX PATCH")
print("=" * 70)

print("\nTo unlock all hairstyles, patch these offsets:")
print("# Unlock all hairstyles - change 0x1E to 0x5A")
for offset in unlock_offsets:
    print(f"{offset:X}: 5A 00")

print("\nTotal offsets to patch:", len(unlock_offsets))
