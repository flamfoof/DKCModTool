"""Analyze level-up table structure more carefully to find battle requirements."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint8(data, offset):
    return data[offset]

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def read_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

print("=" * 70)
print("LEVEL-UP TABLE STRUCTURE ANALYSIS")
print("=" * 70)

data = read_stagebase()

# From build_mod.py:
# RAW_LEVELUP_OFFSET = 0x1733E
# ENTRY_SIZE = 28
# Entries are ordered: class0_male, class0_female, class1_male, class1_female, ...

# Let's analyze the level-up table structure more carefully
RAW_LEVELUP_OFFSET = 0x1733E
ENTRY_SIZE = 28

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

print("\nLevel-up table structure analysis:")
print(f"Offset: 0x{RAW_LEVELUP_OFFSET:X}")
print(f"Entry size: {ENTRY_SIZE} bytes")
print(f"Total entries: 24 (12 classes x 2 variants)")

# Analyze first few entries to understand structure
for entry_idx in range(4):
    offset = RAW_LEVELUP_OFFSET + entry_idx * ENTRY_SIZE
    class_idx = entry_idx // 2
    variant = entry_idx % 2
    
    print(f"\nEntry {entry_idx} (Class {class_idx} {JOB_NAMES[class_idx]} variant {variant}) at 0x{offset:X}:")
    
    # Read the entry
    entry_data = data[offset:offset+ENTRY_SIZE]
    
    # First 10 bytes are stats (att, def, mag, spd, hp as uint16 LE)
    att = read_uint16(data, offset)
    def_ = read_uint16(data, offset + 2)
    mag = read_uint16(data, offset + 4)
    spd = read_uint16(data, offset + 6)
    hp = read_uint16(data, offset + 8)
    
    print(f"  Stats: ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp}")
    print(f"  Bytes 10-27: {entry_data[10:].hex()}")
    
    # Look for patterns in the remaining 18 bytes
    # These might contain battle requirements or other data
    for i in range(10, 28):
        val = entry_data[i]
        if 1 <= val <= 10:
            print(f"    Byte {i}: {val} (potential battle count)")

# Now let's check if there's a separate table for battle requirements
# Search for patterns that look like [1, 2, 3, 4, 5, 6] or similar

print("\n" + "=" * 70)
print("SEARCHING FOR BATTLE REQUIREMENT PATTERNS")
print("=" * 70)

# Search for sequences like 1, 2, 3, 4, 5, 6
for offset in range(0x18000, 0x19000):
    if offset + 6 < len(data):
        seq = [data[offset + i] for i in range(6)]
        if seq == [1, 2, 3, 4, 5, 6]:
            print(f"Found sequence [1,2,3,4,5,6] at 0x{offset:X}")
            print(f"  Context: {data[offset-8:offset+14].hex()}")
        elif seq == [1, 1, 1, 1, 1, 1]:
            print(f"Found sequence [1,1,1,1,1,1] at 0x{offset:X}")
            print(f"  Context: {data[offset-8:offset+14].hex()}")

# Also search for the pattern seen in the job unlock region
# [0, 3, 0, 2, 0, 3, 0, 3, 0, 4, 0, 3]
for offset in range(0x18B00, 0x18C00):
    if offset + 12 < len(data):
        seq = [data[offset + i] for i in range(12)]
        if seq == [0, 3, 0, 2, 0, 3, 0, 3, 0, 4, 0, 3]:
            print(f"Found battle pattern at 0x{offset:X}")
            print(f"  Context: {data[offset-4:offset+16].hex()}")

print("\n" + "=" * 70)
print("SKILL DATA ANALYSIS")
print("=" * 70)

# Known skill offsets from data_tables.py
# Warrior_skill1: 0x18348
# Warrior_skill2: 0x18354
# Let's analyze the skill region more carefully

SKILL_OFFSETS = {
    "Warrior_skill1": 0x18348,
    "Warrior_skill2": 0x18354,
    "Magician_skill1": 0x18360,
    "Thief_skill1": 0x18360,
    "Thief_skill2": 0x1836C,
    "Alchemist_skill1": 0x183A7,
    "Alchemist_skill2": 0x183B3,
}

print("\nKnown skill offsets:")
for name, offset in SKILL_OFFSETS.items():
    val = read_uint8(data, offset)
    print(f"  {name} at 0x{offset:X}: 0x{val:02X}")

# The skill IDs (0x30, 0x31, 0x32, etc.) don't match known SKILL_NAMES
# Maybe they're indices into a different skill table or encoded differently
# Let's search for where these values (0x30-0x34) appear

print("\nSearching for skill ID pattern (0x30-0x34):")
for offset in range(0x18300, 0x18400):
    val = read_uint8(data, offset)
    if 0x30 <= val <= 0x34:
        # Check if this is part of a pattern with class IDs
        if offset - 2 >= 0 and data[offset-2] <= 11:
            class_id = data[offset-2]
            print(f"  Class {class_id} at 0x{offset:X}: skill_id = 0x{val:02X}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
The data structure analysis shows:

1. LEVEL-UP TABLE (0x1733E):
   - Each entry is 28 bytes
   - First 10 bytes: stats (att, def, mag, spd, hp as uint16)
   - Remaining 18 bytes: unknown (may contain battle requirements or other data)
   - Need to analyze the 18-byte structure more carefully

2. BATTLE REQUIREMENTS:
   - Pattern [0, 3, 0, 2, 0, 3, 0, 3, 0, 4, 0, 3] found at 0x18B60
   - This might represent battles for CL1-CL6
   - But the pattern changes after class 2 (contains text descriptions)
   - Need to find where the actual battle requirement data is stored

3. SKILLS:
   - Skill IDs at known offsets (0x30, 0x31, 0x32, etc.) don't match SKILL_NAMES
   - These might be indices into a different table or encoded differently
   - Need to find the actual skill-to-class mapping

Next steps:
- Analyze the 18-byte structure in level-up entries
- Find where battle requirements are actually stored
- Decode the skill ID mapping
""")
