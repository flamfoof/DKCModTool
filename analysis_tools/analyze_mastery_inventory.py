"""Analyze mastery level bonus and inventory count data structures."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint8(data, offset):
    return data[offset]

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def hexdump(data, offset, length=64):
    result = []
    for i in range(0, length, 16):
        chunk = data[offset+i:offset+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"  0x{offset+i:06X}: {hex_str:<48} {ascii_str}")
    return '\n'.join(result)

print("=" * 70)
print("MASTERY LEVEL BONUS ANALYSIS")
print("=" * 70)

data = read_stagebase()

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

# Mastery levels are typically numbered (Mastery 1, Mastery 2, etc.)
# Search for patterns that might represent mastery bonuses
# Look for sequences of small integers that could be mastery levels

print("\nSearching for mastery level patterns:")
# Search for sequences like [1, 2, 3, 4, 5, 6] which could be mastery levels
for offset in range(0x17000, 0x19000):
    if offset + 6 < len(data):
        seq = [data[offset + i] for i in range(6)]
        if seq == [1, 2, 3, 4, 5, 6]:
            print(f"Found [1,2,3,4,5,6] at 0x{offset:X}")
            print(f"  Context: {data[offset-8:offset+14].hex()}")

# Also search near the level-up table
print("\nSearching near level-up table (0x1733E):")
print(hexdump(data, 0x1733E, 128))

# Search for mastery-related strings
print("\nSearching for 'mastery' string:")
mastery_offset = data.lower().find(b'mastery')
if mastery_offset >= 0:
    print(f"Found 'mastery' at 0x{mastery_offset:X}")
    print(f"  Context: {data[mastery_offset-8:mastery_offset+32].hex()}")

# Search for class-specific mastery data
print("\nSearching for class-specific mastery patterns:")
# Look for patterns where class_id is followed by mastery-related data
for offset in range(0x17000, 0x19000):
    if offset + 12 < len(data):
        class_id = data[offset]
        if class_id <= 11:
            # Check if next bytes look like mastery bonuses
            values = [data[offset + i] for i in range(1, 12)]
            # Look for small integers that could be mastery bonuses (0-50)
            if all(0 <= v <= 50 for v in values):
                # Check if not all zeros
                if any(v > 0 for v in values):
                    print(f"0x{offset:X}: Class {class_id} ({JOB_NAMES[class_id]}) - {values[:8]}")

print("\n" + "=" * 70)
print("INVENTORY COUNT ANALYSIS")
print("=" * 70)

# Inventory count might be stored per class or globally
# Search for patterns that look like inventory counts (small integers)

print("\nSearching for inventory count patterns:")
# Search for values that could be inventory counts (typically 1-20)
for offset in range(0x17000, 0x19000):
    val = data[offset]
    if 1 <= val <= 20:
        # Check if this is part of a class-specific pattern
        for i in range(max(0, offset - 4), min(len(data), offset + 4)):
            class_id = data[i]
            if class_id <= 11:
                print(f"0x{offset:X}: potential inventory count {val}, class_id={class_id} at offset {i-offset}")
                break

# Search for 'inventory' string
print("\nSearching for 'inventory' string:")
inventory_offset = data.lower().find(b'inventory')
if inventory_offset >= 0:
    print(f"Found 'inventory' at 0x{inventory_offset:X}")
    print(f"  Context: {data[inventory_offset-8:inventory_offset+32].hex()}")

# Search for 'bag' or related terms
print("\nSearching for 'bag' string:")
bag_offset = data.lower().find(b'bag')
if bag_offset >= 0:
    print(f"Found 'bag' at 0x{bag_offset:X}")
    print(f"  Context: {data[bag_offset-8:bag_offset+32].hex()}")

# Check the bag data region from data_tables.py
# Bag data might be related to inventory
print("\nChecking bag data region (from data_tables.py):")
# Look for BAG_DATA_OFFSET if defined
# Search for bag-related patterns

print("\n" + "=" * 70)
print("SEARCHING FOR CLASS-SPECIFIC DATA TABLES")
print("=" * 70)

# Look for tables with 12 entries (one per class)
# Search for patterns that repeat 12 times with different values

print("\nSearching for 12-entry patterns:")
# Look for regions where class IDs 0-11 appear in sequence
for offset in range(0x17000, 0x18000):
    if offset + 12 < len(data):
        class_ids = [data[offset + i] for i in range(12)]
        if class_ids == list(range(12)):
            print(f"Found class ID sequence at 0x{offset:X}")
            print(f"  Next 12 bytes: {data[offset+12:offset+24].hex()}")
            print(f"  Next 12 bytes: {data[offset+24:offset+36].hex()}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
Mastery level bonus and inventory count analysis:
- Mastery level patterns not clearly identified
- Inventory count patterns not clearly identified
- May need to search in different regions or use DLL injection

Next steps:
- Search in different regions of stageBase_EN.DAT
- Or use DLL injection to log mastery/inventory data at runtime
""")
