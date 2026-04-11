"""Analyze the unlock table region near 0xBF50."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Analyzing unlock table region (0xBF50):")
print("=" * 70)

data = read_stagebase()

# Region with unlock status patterns
UNLOCK_REGION = 0xBF50

print(f"\nHex dump of unlock table region (0x{UNLOCK_REGION:X}):")
for i in range(0, 256, 16):
    offset = UNLOCK_REGION + i
    chunk = data[offset:offset+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"  0x{offset:X}: {hex_str} {ascii_str}")

# Look for the pattern 5A 00 1E 00
print("\nSearching for 5A 00 1E 00 pattern:")
pattern = bytes([0x5A, 0x00, 0x1E, 0x00])
offset = data.find(pattern, UNLOCK_REGION - 0x100, UNLOCK_REGION + 0x200)
while offset >= 0:
    context_start = max(0, offset - 8)
    context_end = min(len(data), offset + 24)
    print(f"Found at 0x{offset:X}: {data[context_start:context_end].hex()}")
    offset = data.find(pattern, offset + 1)

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

print("""
The pattern 5A 00 1E 00 appears multiple times in this region.
This might be the unlock status for hairstyles.

If we change all 1E 00 to 5A 00, it might unlock all hairstyles.
Need to identify which specific offsets correspond to which hairstyles.
""")
