"""Analyze skill table structure using known offsets from data_tables.py."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def hexdump(data, offset, length=64):
    result = []
    for i in range(0, length, 16):
        chunk = data[offset+i:offset+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"  0x{offset+i:06X}: {hex_str:<48} {ascii_str}")
    return '\n'.join(result)

print("Analyzing skill table structure:")
print("=" * 70)

data = read_stagebase()

# Known skill table entries from data_tables.py
SKILL_TABLE_ENTRIES = {
    "Warrior_skill1":      {"offset": 0x18348, "size": 1},
    "Warrior_skill2":      {"offset": 0x18354, "size": 1},
    "Magician_skill1":     {"offset": 0x18360, "size": 1},
    "Thief_skill1":        {"offset": 0x18360, "size": 1},
    "Thief_skill2":        {"offset": 0x1836C, "size": 1},
    "Alchemist_skill1":    {"offset": 0x183A7, "size": 1},
    "Alchemist_skill2":    {"offset": 0x183B3, "size": 1},
}

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

print("\nKnown skill table entries:")
for name, entry in SKILL_TABLE_ENTRIES.items():
    offset = entry["offset"]
    skill_id = data[offset]
    skill_name = SKILL_NAMES.get(skill_id, f"Unknown (0x{skill_id:X})")
    print(f"  {name:<20} at 0x{offset:X}: skill_id=0x{skill_id:02X} ({skill_name})")

# Dump the entire skill table region to find patterns
print("\nHex dump of skill table region (0x18340):")
print(hexdump(data, 0x18340, 256))

# Look for a complete skill table pattern
# Each class might have multiple skill entries (level 1, 2, 4, field skill)
print("\nSearching for complete skill table pattern:")
# Try to find a pattern that repeats every X bytes
# Look for skill IDs (0x00-0x13) in sequence
for offset in range(0x18300, 0x18400):
    # Check if this could be start of a skill table
    skills = []
    for i in range(12):  # Check 12 entries (12 classes)
        skill_offset = offset + i
        if skill_offset < len(data):
            skill_id = data[skill_offset]
            if skill_id in SKILL_NAMES:
                skills.append(skill_id)
            else:
                skills.append(None)
    
    # If we found multiple valid skill IDs, this might be a skill table
    valid_skills = [s for s in skills if s is not None]
    if len(valid_skills) >= 6:
        print(f"0x{offset:X}: Found {len(valid_skills)} valid skill IDs: {valid_skills}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
Skill table analysis:
- Known entries exist at specific offsets (0x18348, 0x18354, etc.)
- SKILL_NAMES mapping only has 20 skills (0x00-0x13)
- Wiki skills don't match SKILL_NAMES (e.g., Meditate, Overload, War Cry not in mapping)
- Need to find complete skill table structure for all classes

Next steps:
1. Find complete skill table for all 12 classes
2. Map wiki skill names to actual skill IDs
3. Find skill modifier data (chances, multipliers)
4. Update SKILL_NAMES mapping if needed
""")
