"""Analyze skill data structure using skill name locations."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint8(data, offset):
    return data[offset]

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

print("=" * 70)
print("SKILL DATA STRUCTURE ANALYSIS")
print("=" * 70)

data = read_stagebase()

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

SKILL_NAME_OFFSETS = {
    "Charge": 0x13D87,
    "Muscle": 0x1473C,
    "Escape": 0x14884,
    "Celerity": 0x14774,
    "Super Cure": 0x13CEC,
    "Alchemy": 0x148D4,
    "Vanish": 0xCFD0,
    "Poison": 0x23B4,
    "Counter": 0x138BC,
    "Steal": 0x14868,
    "Pierce": 0x148C4,
    "Transform": 0x14970,
}

print("\nAnalyzing skill name regions for class-skill mappings:")

for skill_name, offset in SKILL_NAME_OFFSETS.items():
    print(f"\n{skill_name} at 0x{offset:X}:")
    
    # Look backwards from the skill name to find class IDs
    # Search for patterns like [class_id, skill_id] pairs
    for i in range(offset - 32, offset):
        if i < 0:
            continue
        
        # Check if this looks like a class_id (0-11)
        class_id = data[i]
        if class_id <= 11:
            # Check nearby bytes for skill IDs
            for j in range(i, i + 8):
                if j >= len(data):
                    continue
                skill_id = data[j]
                if skill_id <= 19:  # Valid skill ID range
                    # Check if there's a pattern
                    print(f"  0x{i:X}: class_id={class_id}, skill_id={skill_id} at offset {j-i}")
                    break

# Also search for the skill table pattern from data_tables.py
# Known offsets:
# Warrior_skill1: 0x18348
# Warrior_skill2: 0x18354
# Magician_skill1: 0x18360
# Thief_skill1: 0x18360
# Thief_skill2: 0x1836C
# Alchemist_skill1: 0x183A7
# Alchemist_skill2: 0x183B3

print("\n" + "=" * 70)
print("ANALYZING KNOWN SKILL TABLE OFFSETS")
print("=" * 70)

KNOWN_SKILL_OFFSETS = {
    "Warrior_skill1": 0x18348,
    "Warrior_skill2": 0x18354,
    "Magician_skill1": 0x18360,
    "Thief_skill1": 0x18360,
    "Thief_skill2": 0x1836C,
    "Alchemist_skill1": 0x183A7,
    "Alchemist_skill2": 0x183B3,
}

for name, offset in KNOWN_SKILL_OFFSETS.items():
    val = read_uint8(data, offset)
    print(f"{name} at 0x{offset:X}: 0x{val:02X}")

# The values don't match known SKILL_NAMES (0x30, 0x31, 0x32, etc.)
# These might be encoded differently or be indices into a different table
# Let's search for where these values (0x30-0x34) are used

print("\nSearching for skill ID pattern (0x30-0x34) with class IDs:")
for offset in range(0x18300, 0x18400):
    val = read_uint8(data, offset)
    if 0x30 <= val <= 0x34:
        # Check if there's a class ID nearby
        for i in range(max(0, offset - 4), min(len(data), offset + 4)):
            class_id = data[i]
            if class_id <= 11:
                print(f"0x{offset:X}: skill_id=0x{val:02X}, class_id={class_id} at offset {i-offset}")
                break

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
Skill data structure analysis:
- Skill names found at various offsets in stageBase_EN.DAT
- Known skill table offsets contain values (0x30-0x34) that don't match SKILL_NAMES
- These might be encoded skill IDs or indices into a different table
- Need further analysis to decode the skill-to-class mapping

Next steps:
- Try to find where the skill ID mapping table is located
- Or use DLL injection to log skill data at runtime
""")
