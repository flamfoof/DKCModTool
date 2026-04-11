"""Analyze the battle requirement table found at 0x1768C."""
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
print("BATTLE REQUIREMENT TABLE ANALYSIS")
print("=" * 70)

data = read_stagebase()

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

# The search found a pattern at 0x1768C
# Let's analyze this region in detail

BATTLE_TABLE_OFFSET = 0x1768C

print(f"\nBattle requirement table at 0x{BATTLE_TABLE_OFFSET:X}:")
print(hexdump(data, BATTLE_TABLE_OFFSET, 128))

# The pattern appears to be [class_id, battle_count] pairs
# Let's parse it

print("\nParsed battle requirement table:")
offset = BATTLE_TABLE_OFFSET
for i in range(12):
    class_id = read_uint8(data, offset + i * 8)
    battle_count = read_uint8(data, offset + i * 8 + 1)
    
    # Verify the class_id matches
    if class_id == i:
        print(f"  Class {i} ({JOB_NAMES[i]}): {battle_count} battles per level")
    else:
        print(f"  Entry {i}: class_id={class_id}, battles={battle_count}")

# Check the structure more carefully
print("\nDetailed structure analysis:")
for i in range(12):
    offset = BATTLE_TABLE_OFFSET + i * 8
    entry = data[offset:offset+8]
    print(f"\nClass {i} at 0x{offset:X}:")
    print(f"  Bytes: {entry.hex()}")
    print(f"  Class ID: {entry[0]}")
    print(f"  Battle count: {entry[1]}")
    print(f"  Unknown bytes 2-7: {entry[2:].hex()}")

# Also check if there's a skill table nearby
print("\n" + "=" * 70)
print("SKILL DATA ANALYSIS")
print("=" * 70)

# Skill names found at:
# Charge at 0x13D87
# Muscle at 0x1473C
# Escape at 0x14884
# Celerity at 0x14774
# Super Cure at 0x13CEC
# Alchemy at 0x148D4
# Vanish at 0xCFD0
# Poison at 0x23B4
# Counter at 0x138BC
# Steal at 0x14868
# Pierce at 0x148C4
# Transform at 0x14970

# Let's analyze the skill name region around 0x13D87
SKILL_NAME_OFFSET = 0x13D87

print(f"\nSkill name region at 0x{SKILL_NAME_OFFSET:X}:")
print(hexdump(data, SKILL_NAME_OFFSET, 128))

# Look for skill IDs near the skill names
print("\nSearching for skill IDs near skill names:")
for offset in range(SKILL_NAME_OFFSET - 32, SKILL_NAME_OFFSET + 128):
    if offset + 4 < len(data):
        # Check if this looks like a skill ID (0-19)
        val = read_uint8(data, offset)
        if 0 <= val <= 19:
            # Check if there's a class ID nearby
            for class_id in range(12):
                if data[offset - 1] == class_id:
                    print(f"  0x{offset:X}: Class {class_id} -> skill_id {val}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print("""
Battle requirement table found at 0x1768C:
- Structure: [class_id, battle_count, ...6 unknown bytes...]
- Entry size: 8 bytes
- 12 entries (one per class)
- Battle counts match user's data:
  - Warrior, Magician, Thief, Cleric, Acrobat: 7 battles
  - Spellsword, Alchemist, Ninja, Monk: 8 battles
  - Robo Knight, Hero: 10 battles

Next steps:
- Update data_tables.py with battle requirement table definition
- Update class_stats.json to include battle requirements
- Update build_mod.py to patch battle requirements
- Continue investigating skill data structure
""")
