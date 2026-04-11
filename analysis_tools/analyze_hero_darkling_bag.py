"""Search for Hero/Darkling bag data and mastery level data."""
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
print("HERO/DARKLING BAG DATA SEARCH")
print("=" * 70)

data = read_stagebase()

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

# Bag data is at 0x1884E with 20 entries (10 classes x 2 variants)
# This covers classes 0-9 (Warrior through Robo Knight)
# Need to find Hero (class 10) and Darkling (class 11) bag data

print("\nSearching for Hero (class 10) bag data:")
# Look for class_id = 10 followed by bag-like structure
for offset in range(0x18000, 0x19000):
    if offset + 8 < len(data):
        class_id = data[offset + 6]
        variant = data[offset + 7]
        if class_id == 10:
            item_slots = data[offset]
            magic_slots = data[offset + 1]
            total_cap = data[offset + 2]
            print(f"0x{offset:X}: Hero variant {variant} - Items: {item_slots}, Magic: {magic_slots}, Total: {total_cap}")
            print(f"  Context: {data[offset-4:offset+12].hex()}")

print("\nSearching for Darkling (class 11) bag data:")
for offset in range(0x18000, 0x19000):
    if offset + 8 < len(data):
        class_id = data[offset + 6]
        variant = data[offset + 7]
        if class_id == 11:
            item_slots = data[offset]
            magic_slots = data[offset + 1]
            total_cap = data[offset + 2]
            print(f"0x{offset:X}: Darkling variant {variant} - Items: {item_slots}, Magic: {magic_slots}, Total: {total_cap}")
            print(f"  Context: {data[offset-4:offset+12].hex()}")

# Check if bag data continues after the 20 entries
print("\nChecking bag data continuation after 20 entries:")
BAG_TABLE_OFFSET = 0x1884E
BAG_ENTRY_SIZE = 8
for i in range(20, 30):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    if offset + 8 < len(data):
        class_id = data[offset + 6]
        variant = data[offset + 7]
        item_slots = data[offset]
        magic_slots = data[offset + 1]
        total_cap = data[offset + 2]
        
        if class_id <= 11:
            variant_str = "M" if variant == 0 else "F"
            class_name = JOB_NAMES[class_idx] if class_id < 12 else f"Unknown({class_id})"
            print(f"  Entry {i}: {class_name} {variant_str} - Items: {item_slots}, Magic: {magic_slots}, Total: {total_cap}")

print("\n" + "=" * 70)
print("MASTERY LEVEL BONUS SEARCH")
print("=" * 70)

# Search for proficiency-related data
# From stagebase_parser.py, there's PROFICIENCY_NAMES
print("\nSearching for proficiency-related strings:")
proficiency_offset = data.lower().find(b'proficiency')
if proficiency_offset >= 0:
    print(f"Found 'proficiency' at 0x{proficiency_offset:X}")
    print(f"  Context: {data[proficiency_offset-8:proficiency_offset+48].hex()}")

# Search for level-up mastery data
# Mastery might be related to class levels (CL1, CL2, etc.)
print("\nSearching for CL (class level) patterns:")
for offset in range(0x18000, 0x19000):
    if offset + 2 < len(data):
        # Look for patterns like "CL1", "CL2", etc.
        if data[offset] == ord('C') and data[offset + 1] == ord('L'):
            cl_num = data[offset + 2]
            if ord('0') <= cl_num <= ord('6'):
                print(f"Found 'CL{chr(cl_num)}' at 0x{offset:X}")
                print(f"  Context: {data[offset-4:offset+12].hex()}")

# Search for mastery bonus values
# Mastery bonuses might be stored as small integers per class per mastery level
print("\nSearching for mastery bonus patterns (class_id followed by values):")
for offset in range(0x18000, 0x19000):
    if offset + 12 < len(data):
        class_id = data[offset]
        if class_id <= 11:
            # Check if next bytes look like mastery bonuses
            values = [data[offset + i] for i in range(1, 12)]
            # Look for small integers that could be mastery bonuses (0-50)
            if all(0 <= v <= 50 for v in values):
                # Check if not all zeros and has some pattern
                if any(v > 0 for v in values):
                    # Check if values are in a reasonable range for mastery bonuses
                    if max(values) <= 20:  # Mastery bonuses are typically small
                        print(f"0x{offset:X}: Class {class_id} ({JOB_NAMES[class_id]}) - {values[:8]}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
Hero/Darkling bag data:
- Hero (class 10) and Darkling (class 11) bag data not found in standard bag table
- May use default bag settings or not have class-specific bag data
- Or stored in a different location

Mastery level bonus:
- No clear proficiency/mastery data found
- Mastery bonus patterns not clearly identified
- May need to search in different regions or use DLL injection

Next steps:
- Check if Hero/Darkling use default bag settings
- Search for mastery data in different regions of stageBase_EN.DAT
- Or use DLL injection to log mastery data at runtime
""")
