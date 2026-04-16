"""
Find class ability/skill data in stageBase_EN.DAT.

Known class abilities (from game wiki):
  Warrior:    Charge (CL1), Muscle (CL3)
  Magician:   Concentrate (CL1), Super Cure (CL3)
  Thief:      Steal (CL1), Escape (CL3)
  Cleric:     Super Cure (CL1), Focus (CL3)
  Spellsword: Celerity (CL1), Counter (CL3)
  Alchemist:  Alchemy (CL1), Bounty (CL3)
  Ninja:      Vanish (CL1), Poison (CL3)
  Monk:       Hustle (CL1), Pierce (CL3)
  Acrobat:    Item Snatch (CL1), Hustle (CL3)
  Robo Knight: Robo Laser (CL1), Robo Punch (CL3)
  Hero:       Transform (CL1)
  Darkling:   (unknown)
"""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

with open(STAGEBASE, 'rb') as f:
    data = f.read()

SKILL_IDS = {
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

# Known ability pairs per class (CL1_skill_id, CL3_skill_id)
CLASS_ABILITIES = {
    "Warrior":     (0x01, 0x02),  # Charge, Muscle
    "Magician":    (0x06, 0x07),  # Concentrate, Super Cure
    "Thief":       (0x0E, 0x04),  # Steal, Escape
    "Cleric":      (0x07, 0x0D),  # Super Cure, Focus
    "Spellsword":  (0x05, 0x0C),  # Celerity, Counter
    "Alchemist":   (0x08, 0x09),  # Alchemy, Bounty
    "Ninja":       (0x0A, 0x0B),  # Vanish, Poison
    "Monk":        (0x03, 0x0F),  # Hustle, Pierce
    "Acrobat":     (0x13, 0x03),  # Item Snatch, Hustle
    "Robo Knight": (0x11, 0x12),  # Robo Laser, Robo Punch
    "Hero":        (0x10, 0x00),  # Transform, None
}

print("=" * 70)
print("SEARCHING FOR CLASS ABILITY DATA IN stageBase_EN.DAT")
print("=" * 70)

# Strategy 1: Search for consecutive skill ID pairs within stride
print("\n--- Strategy 1: Search for skill pair sequences ---")
for stride in [1, 2, 4, 8, 12, 16, 20, 24, 28, 32]:
    for offset in range(len(data) - stride * 12):
        matches = 0
        for i, (class_name, (s1, s2)) in enumerate(CLASS_ABILITIES.items()):
            o1 = offset + i * stride
            if o1 + 1 < len(data) and data[o1] == s1 and data[o1 + 1] == s2:
                matches += 1
        if matches >= 4:
            print(f"  offset=0x{offset:X}, stride={stride}: {matches} class matches")
            for i, (class_name, (s1, s2)) in enumerate(CLASS_ABILITIES.items()):
                o1 = offset + i * stride
                if o1 + 1 < len(data):
                    v1, v2 = data[o1], data[o1+1]
                    match = "✓" if v1 == s1 and v2 == s2 else "✗"
                    print(f"    {class_name:12}: 0x{o1:X} = [{v1:02X}, {v2:02X}] ({SKILL_IDS.get(v1,'?')}, {SKILL_IDS.get(v2,'?')}) {match}")

# Strategy 2: Search for CL1 skills in sequence (just first skill per class)
print("\n--- Strategy 2: Search for CL1 skill sequence ---")
cl1_skills = [s1 for s1, s2 in CLASS_ABILITIES.values()]
# Warrior=01, Magician=06, Thief=0E, Cleric=07, Spellsword=05, Alchemist=08, Ninja=0A, Monk=03, Acrobat=13, RoboKnight=11, Hero=10
print(f"  Looking for sequence: {[f'0x{s:02X}' for s in cl1_skills]}")

for stride in [1, 2, 4, 8, 12, 16, 20, 24, 28, 32]:
    for offset in range(len(data) - stride * 11):
        matches = 0
        for i, skill_id in enumerate(cl1_skills):
            pos = offset + i * stride
            if pos < len(data) and data[pos] == skill_id:
                matches += 1
        if matches >= 5:
            print(f"  offset=0x{offset:X}, stride={stride}: {matches}/11 CL1 skill matches")

# Strategy 3: Search for individual known pairs with various gaps
print("\n--- Strategy 3: Search for Warrior (Charge=01, Muscle=02) with gap ---")
for offset in range(len(data) - 32):
    if data[offset] == 0x01:  # Charge
        for gap in range(1, 32):
            if offset + gap < len(data) and data[offset + gap] == 0x02:  # Muscle
                # Check if Magician follows at same stride
                class_stride_candidates = range(4, 64, 4)
                for class_stride in class_stride_candidates:
                    mag_offset = offset + class_stride
                    if mag_offset < len(data) and data[mag_offset] == 0x06:  # Concentrate
                        if mag_offset + gap < len(data) and data[mag_offset + gap] == 0x07:  # Super Cure
                            thief_offset = offset + 2 * class_stride
                            if thief_offset < len(data) and data[thief_offset] == 0x0E:  # Steal
                                print(f"  MATCH: offset=0x{offset:X}, gap={gap}, class_stride={class_stride}")
                                for i, (cn, (s1, s2)) in enumerate(CLASS_ABILITIES.items()):
                                    o = offset + i * class_stride
                                    if o + gap < len(data):
                                        print(f"    {cn:12}: 0x{o:X} skill1=0x{data[o]:02X} ({SKILL_IDS.get(data[o],'?')}), 0x{o+gap:X} skill2=0x{data[o+gap]:02X} ({SKILL_IDS.get(data[o+gap],'?')})")

# Strategy 4: Search as uint16 values
print("\n--- Strategy 4: Search with uint16 skill IDs ---")
for stride in [2, 4, 8, 12, 16, 20, 24, 28, 32]:
    for offset in range(0, len(data) - stride * 12, 2):
        matches = 0
        for i, (class_name, (s1, s2)) in enumerate(CLASS_ABILITIES.items()):
            o1 = offset + i * stride
            if o1 + 3 < len(data):
                v1 = struct.unpack_from('<H', data, o1)[0]
                v2 = struct.unpack_from('<H', data, o1 + 2)[0]
                if v1 == s1 and v2 == s2:
                    matches += 1
        if matches >= 4:
            print(f"  offset=0x{offset:X}, stride={stride}: {matches} uint16 pair matches")
            for i, (class_name, (s1, s2)) in enumerate(CLASS_ABILITIES.items()):
                o1 = offset + i * stride
                if o1 + 3 < len(data):
                    v1 = struct.unpack_from('<H', data, o1)[0]
                    v2 = struct.unpack_from('<H', data, o1 + 2)[0]
                    match = "✓" if v1 == s1 and v2 == s2 else "✗"
                    print(f"    {class_name:12}: 0x{o1:X} = [{v1:04X}, {v2:04X}] {match}")
