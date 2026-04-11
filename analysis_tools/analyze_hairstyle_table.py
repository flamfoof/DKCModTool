"""Analyze the hairstyle table structure at 0x17A3."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Analyzing hairstyle table structure at 0x17A3:")
print("=" * 70)

data = read_stagebase()

TABLE_START = 0x17A3

print(f"\nHairstyle table entries (7-byte structure):")
for i in range(14):  # Check 14 entries
    offset = TABLE_START + i * 7
    if offset + 7 > len(data):
        break
    
    entry = data[offset:offset+7]
    hairstyle_id = entry[0]
    
    print(f"Entry {i} (0x{offset:X}): ID={hairstyle_id}, {entry.hex()}")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

print("""
Table structure (7 bytes per entry):
- Byte 0: Hairstyle ID (0, 1, 2, 3, ...)
- Bytes 1-4: 00 00 2F 00 (constant)
- Bytes 5-6: 01 01 (constant)

Current entries:
- Entry 0: ID 0
- Entry 1: ID 1
- Entry 2: ID 2
- Entry 3: ID 3
- ... (need to check if entries 4-13 exist)

This table seems to list available hairstyles. To unlock all 14 hairstyles,
we need to ensure entries 0-13 exist with IDs 0-13.

If entries 4-13 are missing or have incorrect IDs, we need to add/fix them.
""")

print("\nChecking if entries 4-13 exist:")
for i in range(4, 14):
    offset = TABLE_START + i * 7
    if offset + 7 > len(data):
        print(f"Entry {i}: OUT OF RANGE")
        continue
    
    entry = data[offset:offset+7]
    hairstyle_id = entry[0]
    print(f"Entry {i} (0x{offset:X}): ID={hairstyle_id}, {entry.hex()}")

print("\n" + "=" * 70)
