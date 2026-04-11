"""Analyze class skill data from wiki."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Analyzing class skill data from wiki:")
print("=" * 70)

data = read_stagebase()

# Wiki skill names:
SKILLS = {
    "Warrior": ["Muscle", "Overload", "War Cry"],
    "Magician": ["Meditate", "Restrict", "Mage Combo"],
    "Thief": ["Steal", "Escape", "Pickpocket"],
    "Cleric": ["Heal", "Prayer", "Holy Aura"],
    "Spellsword": ["Chakra", "Pierce", "Barrier"],
    "Alchemist": ["Alchemy", "Debug", "Duplicate"],
    "Ninja": ["Sneak Hit", "Decoy", "Item Combo"],
    "Monk": ["Soul Fire", "Afterburn", "Fire Up"],
    "Acrobat": ["Play Dumb", "????", "Play Dead"],
    "Robo Knight": ["Copy", "Harden", "GOTO"],
    "Hero": ["Glory", "Guard", "Full Combo"],
}

# Search for skill names in the data file
print("\nSearching for skill names in stageBase_EN.DAT:")
for skill_name in set([s for skills in SKILLS.values() for s in skills if s != "????"]):
    skill_bytes = skill_name.lower().encode('ascii')
    offset = data.lower().find(skill_bytes)
    if offset >= 0:
        print(f"  {skill_name:<12} at 0x{offset:X}")
        print(f"    Context: {data[max(0, offset-8):min(len(data), offset+len(skill_bytes)+16)].hex()}")
    else:
        print(f"  {skill_name:<12} not found")

# Search for skill-related strings
print("\nSearching for skill-related strings:")
skill_terms = ["skill", "battle", "field", "magic", "reflect", "barrier", "combo"]
for term in skill_terms:
    offset = data.lower().find(term.encode('ascii'))
    if offset >= 0:
        print(f"  '{term}' at 0x{offset:X}")

# Look for skill ID patterns
# Skills might be stored as IDs (0x30-0x34 range mentioned in previous analysis)
print("\nSearching for skill ID patterns (0x30-0x34):")
for offset in range(0x18000, 0x19000):
    if offset + 2 < len(data):
        skill_id = data[offset]
        if 0x30 <= skill_id <= 0x34:
            class_id = data[offset + 1]
            if class_id <= 11:
                print(f"0x{offset:X}: skill_id=0x{skill_id:X}, class_id={class_id}")

# Search for skill chance/probability data
# Spellsword's Barrier has a reflection chance - look for percentage values
print("\nSearching for skill chance/probability data:")
for offset in range(0x18000, 0x19000):
    if offset + 2 < len(data):
        val = data[offset]
        # Look for percentage values (0-100)
        if 0 < val <= 100:
            # Check if this might be a skill chance
            context = data[offset-2:offset+4]
            if context[0] <= 11:  # class_id
                print(f"0x{offset:X}: potential chance={val}%, class_id={context[0]}")

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)

print("""
1. If skill names not found, search for skill IDs instead
2. Look for skill tables that map class_id to skill IDs
3. Search for skill modifier data (chances, multipliers)
4. Check executable (DkkStm.exe) for skill logic
""")
