"""Analyze bag/inventory data and mastery level bonus."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint8(data, offset):
    return data[offset]

def hexdump(data, offset, length=64):
    result = []
    for i in range(0, length, 16):
        chunk = data[offset+i:offset+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"  0x{offset+i:06X}: {hex_str:<48} {ascii_str}")
    return '\n'.join(result)

print("=" * 70)
print("BAG/INVENTORY DATA ANALYSIS")
print("=" * 70)

data = read_stagebase()

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

# From data_tables.py:
# BAG_TABLE_OFFSET = 0x1884E
# BAG_ENTRY_SIZE = 8
# BAG_ENTRY_COUNT = 20 (10 classes x 2 variants)
# Structure: [item_slots, magic_slots, total_cap, 0, 0, 0, class_idx, variant]

BAG_TABLE_OFFSET = 0x1884E
BAG_ENTRY_SIZE = 8

print(f"\nBag data table at 0x{BAG_TABLE_OFFSET:X}:")
print(hexdump(data, BAG_TABLE_OFFSET, 160))

print("\nParsed bag data:")
for i in range(20):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    item_slots = read_uint8(data, offset)
    magic_slots = read_uint8(data, offset + 1)
    total_cap = read_uint8(data, offset + 2)
    class_idx = read_uint8(data, offset + 6)
    variant = read_uint8(data, offset + 7)
    
    variant_str = "M" if variant == 0 else "F"
    class_name = JOB_NAMES[class_idx] if class_idx < 12 else f"Unknown({class_idx})"
    
    print(f"  Entry {i}: {class_name:<14} {variant_str:<6} - Items: {item_slots}, Magic: {magic_slots}, Total: {total_cap}")

# Check if there are more bag entries beyond 20
print("\nChecking for additional bag entries:")
for i in range(20, 30):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    if offset + 8 < len(data):
        class_idx = read_uint8(data, offset + 6)
        variant = read_uint8(data, offset + 7)
        item_slots = read_uint8(data, offset)
        magic_slots = read_uint8(data, offset + 1)
        
        if class_idx <= 11:
            variant_str = "M" if variant == 0 else "F"
            class_name = JOB_NAMES[class_idx]
            print(f"  Entry {i}: {class_name:<14} {variant_str:<6} - Items: {item_slots}, Magic: {magic_slots}")

print("\n" + "=" * 70)
print("MASTERY LEVEL BONUS ANALYSIS")
print("=" * 70)

# Mastery levels are typically numbered (Mastery 1, Mastery 2, etc.)
# Search for patterns that might represent mastery bonuses
# Look for sequences that could be mastery level bonuses

print("\nSearching for mastery-related strings:")
mastery_offset = data.lower().find(b'mastery')
if mastery_offset >= 0:
    print(f"Found 'mastery' at 0x{mastery_offset:X}")
    print(f"  Context: {data[mastery_offset-8:mastery_offset+48].hex()}")
else:
    print("'mastery' string not found")

# Search for 'master' string
master_offset = data.lower().find(b'master')
if master_offset >= 0:
    print(f"Found 'master' at 0x{master_offset:X}")
    print(f"  Context: {data[master_offset-8:master_offset+48].hex()}")

# Search for patterns that look like mastery bonuses
# Mastery bonuses are typically small integers (1-50) that might be stored per class
print("\nSearching for mastery bonus patterns:")
# Look for patterns where class_id is followed by mastery-related data
for offset in range(0x18000, 0x19000):
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

# Search for level-related data that might be mastery
print("\nSearching for level/mastery patterns:")
# Look for sequences like [1, 2, 3, 4, 5, 6] which could be mastery levels
for offset in range(0x18000, 0x19000):
    if offset + 6 < len(data):
        seq = [data[offset + i] for i in range(6)]
        if seq == [1, 2, 3, 4, 5, 6]:
            print(f"Found [1,2,3,4,5,6] at 0x{offset:X}")
            print(f"  Context: {data[offset-8:offset+14].hex()}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
Bag/Inventory data:
- Bag table at 0x1884E with 20 entries (10 classes x 2 variants)
- Structure: [item_slots, magic_slots, total_cap, 0, 0, 0, class_idx, variant]
- Entry size: 8 bytes
- First 10 classes covered (Warrior through Acrobat)
- Need to check if Hero/Darkling have bag data elsewhere

Mastery level bonus:
- No clear 'mastery' string found
- Mastery bonus patterns not clearly identified
- May need to search in different regions or use DLL injection

Next steps:
- Check if Hero/Darkling have bag data in different location
- Search for mastery data in different regions
- Or use DLL injection to log mastery data at runtime
""")
