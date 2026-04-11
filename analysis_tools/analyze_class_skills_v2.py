"""Analyze class skills and battle requirements more systematically."""
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
print("CLASS LEVEL-UP BATTLE REQUIREMENTS ANALYSIS")
print("=" * 70)

data = read_stagebase()

# From the analysis, battle counts 1-6 appear in sequence
# This likely represents battles needed for CL1, CL2, CL3, CL4, CL5, CL6
# Let's look at the 0x18500 region more carefully

print("\nBattle requirement region (0x18500):")
print(hexdump(data, 0x18500, 128))

# Look for the pattern: class_id, [battles_for_CL1, CL2, CL3, CL4, CL5, CL6]
JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

print("\nSearching for class battle requirement patterns:")
for class_id in range(12):
    # Search for class_id followed by sequence of small integers
    for offset in range(0x18500, 0x18600):
        if offset + 12 <= len(data):
            if data[offset] == class_id:
                # Check if next bytes are battle counts (1-6)
                battles = [data[offset + i] for i in range(1, 7)]
                if all(1 <= b <= 6 for b in battles):
                    print(f"  Class {class_id} ({JOB_NAMES[class_id]}) at 0x{offset:X}: CL battles = {battles}")
                    break

# Also check the job unlock region
print("\nJob unlock battle requirements region (0x18B00):")
print(hexdump(data, 0x18B00, 128))

print("\nSearching for class battle requirements in job unlock region:")
for class_id in range(12):
    for offset in range(0x18B00, 0x18C00):
        if offset + 12 <= len(data):
            if data[offset] == class_id:
                battles = [data[offset + i] for i in range(1, 7)]
                if all(1 <= b <= 6 for b in battles):
                    print(f"  Class {class_id} ({JOB_NAMES[class_id]}) at 0x{offset:X}: CL battles = {battles}")
                    break

print("\n" + "=" * 70)
print("CLASS SKILL ANALYSIS")
print("=" * 70)

# Skills are typically learned at CL1 and CL3
# Let's search for skill patterns near the class data

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

print("\nSkill data region (0x18340):")
print(hexdump(data, 0x18340, 128))

# Search for pattern: class_id, skill_CL1, skill_CL3
print("\nSearching for class skill patterns (CL1 and CL3):")
for class_id in range(12):
    for offset in range(0x18340, 0x18400):
        if offset + 8 <= len(data):
            if data[offset] == class_id:
                skill1 = data[offset + 2]
                skill2 = data[offset + 4]
                if skill1 in SKILL_NAMES or skill2 in SKILL_NAMES:
                    print(f"  Class {class_id} ({JOB_NAMES[class_id]}) at 0x{offset:X}: CL1 skill = 0x{skill1:02X} ({SKILL_NAMES.get(skill1, 'Unknown')}), CL3 skill = 0x{skill2:02X} ({SKILL_NAMES.get(skill2, 'Unknown')})")
                    break

print("\n" + "=" * 70)
print("SUMMARY OF FINDINGS")
print("=" * 70)

print("""
Based on the analysis, here are the likely data structures:

1. CLASS LEVEL-UP BATTLE REQUIREMENTS:
   - Location: 0x18B00 region
   - Pattern: [class_id, CL1_battles, CL2_battles, CL3_battles, CL4_battles, CL5_battles, CL6_battles]
   - Typical values: CL1=1, CL2=2, CL3=3, CL4=4, CL5=5, CL6=6

2. CLASS SKILLS:
   - Location: 0x18340 region  
   - Pattern: [class_id, ?, skill_CL1, ?, skill_CL3, ...]
   - Skills are learned at CL1 and CL3

Need to verify exact offsets for each class.
""")

# Let's create a structured mapping
print("\nAttempting to map all classes:")

# Battle requirements
print("\nBATTLE REQUIREMENTS (offsets to be verified):")
for class_id in range(12):
    # Try to find the pattern at regular intervals
    base_offset = 0x18B00 + class_id * 16
    if base_offset + 12 < len(data):
        battles = [data[base_offset + i] for i in range(1, 7)]
        print(f"  Class {class_id} ({JOB_NAMES[class_id]}): 0x{base_offset:X} = {battles}")

# Skills
print("\nSKILLS (offsets to be verified):")
for class_id in range(12):
    base_offset = 0x18340 + class_id * 16
    if base_offset + 8 < len(data):
        skill1 = data[base_offset + 2]
        skill3 = data[base_offset + 4]
        print(f"  Class {class_id} ({JOB_NAMES[class_id]}): 0x{base_offset:X} = CL1: 0x{skill1:02X}, CL3: 0x{skill3:02X}")
