"""Verify hairstyle hex patch offsets in stageBase_EN.DAT."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Verifying hairstyle hex patch offsets:")
print("=" * 70)

data = read_stagebase()

# Offsets from the hex patch
OFFSETS = [
    0x18AA4, 0x18AAC, 0x18AB4, 0x18AC4, 0x18ACC,
    0x18AD4, 0x18AD8, 0x18AE0, 0x18AE8, 0x18AF0,
    0x18AF8, 0x18B00, 0x18B08, 0x18B10, 0x18B18,
    0x18B1A, 0x18B20
]

print("\nChecking current values at hex patch offsets:")
for offset in OFFSETS:
    if offset + 2 <= len(data):
        value = struct.unpack('<H', data[offset:offset+2])[0]
        print(f"0x{offset:X}: 0x{value:04X} ({value})")
    else:
        print(f"0x{offset:X}: OUT OF RANGE")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

print("""
The hex patch changes values to 0x5A (90) to unlock hairstyles.
If the current values are already 0x5A, the patch won't change anything.
If the current values are different, the patch should work.

Common unlock values:
- 0x5A (90) = unlocked by default
- 0x1E (30) = locked (needs unlock)
- 0x78 (120) = locked (special case)

If the mod isn't working, possible issues:
1. Offsets are incorrect for the game version
2. Unlock logic uses different values than expected
3. There are additional offsets not covered by the patch
""")
