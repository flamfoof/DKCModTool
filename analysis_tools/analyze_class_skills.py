"""Analyze class skill data and class level-up battle requirements."""
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
print("CLASS SKILL DATA ANALYSIS")
print("=" * 70)

data = read_stagebase()

# From data_tables.py, skill data starts around 0x18340
# Known entries:
# Warrior_skill1: 0x18348
# Warrior_skill2: 0x18354
# Magician_skill1: 0x18360
# Thief_skill1: 0x18360
# Thief_skill2: 0x1836C
# Alchemist_skill1: 0x183A7
# Alchemist_skill2: 0x183B3

print("\nSkill data region (0x18340):")
print(hexdump(data, 0x18340, 128))

SKILL_NAMES = {
    0x00: "None",
    0x01: "Charge",
    0x02: "Muscle",
    0x03: "Hustle",
    0x04: "Escape",
    0x05: "Celerity",
    0x06: "Concentrate",
    0x07: "Super Cure",
    0x08: "Alchemy",
    0x09: "Bounty",
    0x0A: "Vanish",
    0x0B: "Poison",
    0x0C: "Counter",
    0x0D: "Focus",
    0x0E: "Steal",
    0x0F: "Pierce",
    0x10: "Transform",
    0x11: "Robo Laser",
    0x12: "Robo Punch",
    0x13: "Item Snatch",
}

# Let's analyze the skill region more systematically
# The pattern seems to be: [class_id, skill_id, ...]
# Let's search for all byte values that match skill IDs (0x00-0x13)

print("\n" + "=" * 70)
print("SEARCHING FOR CLASS SKILL PATTERNS")
print("=" * 70)

# Look for patterns in the skill region
offset = 0x18340
class_skills = {}
current_class = None

while offset < 0x18400:
    val = read_uint8(data, offset)
    
    # Check if this looks like a class identifier (0-11)
    if val <= 11:
        current_class = val
        # Check next bytes for skill IDs
        if offset + 4 < len(data):
            skill1 = read_uint8(data, offset + 1)
            skill2 = read_uint8(data, offset + 2)
            if skill1 in SKILL_NAMES or skill2 in SKILL_NAMES:
                print(f"0x{offset:X}: Class {val} - Skill1: 0x{skill1:02X} ({SKILL_NAMES.get(skill1, 'Unknown')}), Skill2: 0x{skill2:02X} ({SKILL_NAMES.get(skill2, 'Unknown')})")
                if val not in class_skills:
                    class_skills[val] = []
                class_skills[val].append({"offset": offset, "skill1": skill1, "skill2": skill2})
    
    offset += 1

# Also check the known offsets from data_tables.py
print("\nKnown skill table entries:")
known_offsets = {
    "Warrior_skill1": 0x18348,
    "Warrior_skill2": 0x18354,
    "Magician_skill1": 0x18360,
    "Thief_skill1": 0x18360,
    "Thief_skill2": 0x1836C,
    "Alchemist_skill1": 0x183A7,
    "Alchemist_skill2": 0x183B3,
}

for name, offset in known_offsets.items():
    val = read_uint8(data, offset)
    print(f"  {name} at 0x{offset:X}: 0x{val:02X} ({SKILL_NAMES.get(val, 'Unknown')})")

print("\n" + "=" * 70)
print("CLASS LEVEL-UP BATTLE REQUIREMENTS ANALYSIS")
print("=" * 70)

# Class level-up battle requirements might be near the job unlock data
# JOB_UNLOCK_OFFSET = 0x18B60
# Let's search around that region

print("\nJob unlock region (0x18B60):")
print(hexdump(data, 0x18B60, 128))

# Search for patterns that might represent battle counts
# Battle counts are likely small integers (1-50)
print("\nSearching for battle count patterns...")
for offset in range(0x18B00, 0x18C00, 2):
    if offset + 2 <= len(data):
        val = read_uint16(data, offset)
        if 1 <= val <= 50:
            # Check if this looks like a sequence
            if offset + 4 <= len(data):
                next_val = read_uint16(data, offset + 2)
                if 1 <= next_val <= 50:
                    print(f"  0x{offset:X}: {val}, 0x{offset+2:X}: {next_val}")

# Also search for the level-up table region
# LEVELUP_TABLE_OFFSET = 0x185AE
# Let's check around there

print("\nLevel-up table region (0x185AE):")
print(hexdump(data, 0x185AE, 64))

# Look for battle requirements near the level-up table
for offset in range(0x18500, 0x18600):
    if offset + 2 <= len(data):
        val = read_uint16(data, offset)
        if 1 <= val <= 50:
            print(f"  0x{offset:X}: Battle count = {val}")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
