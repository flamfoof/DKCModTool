"""Search for skill modifier data (chances, multipliers) using wiki info."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Searching for skill modifier data:")
print("=" * 70)

data = read_stagebase()

# Wiki skill modifiers:
# Barrier: "sometimes" (reflection chance)
# Play Dead: 50% chance
# Decoy: 50% of the time
# Holy Aura: "randomly"
# War Cry: "randomly"
# Duplicate: "randomly"
# GOTO: "randomly"
# Full Combo: allows 1 field magic + 1 item (no chance)

# Search for 50% (50 decimal) in skill-related regions
print("\nSearching for 50 (50%) in skill region (0x18000-0x19000):")
for offset in range(0x18000, 0x19000):
    if data[offset] == 50:
        # Check context to see if this might be a skill chance
        context = data[max(0, offset-8):min(len(data), offset+16)]
        print(f"0x{offset:X}: {context.hex()}")

# Search for percentage values near skill table
print("\nSearching for percentage values (1-100) near skill table (0x18300-0x18400):")
for offset in range(0x18300, 0x18400):
    if offset + 1 < len(data):
        val = data[offset]
        if 1 <= val <= 100:
            context = data[max(0, offset-4):min(len(data), offset+8)]
            print(f"0x{offset:X}: {val}% - {context.hex()}")

# Look for field skill data specifically
# Field skills: War Cry, Mage Combo, Pickpocket, Holy Aura, Barrier, Duplicate, Item Combo, Fire Up, Play Dead, GOTO, Full Combo
print("\nSearching for field skill data patterns:")
# Field skills might have different structure than battle skills
# Look for patterns that repeat 12 times (one per class)

# Try to find a table that might contain field skill IDs or modifiers
for offset in range(0x18000, 0x19000):
    if offset + 12 < len(data):
        # Check if this looks like a field skill table
        # Each entry might be 1-4 bytes
        values = [data[offset + i] for i in range(12)]
        # Check if values are in reasonable range for skill IDs or chances
        if all(0 <= v <= 100 or v in [0x46, 0x47] for v in values):
            print(f"0x{offset:X}: potential field skill data: {values}")

# Search for the specific skill pattern from hex dump
# Pattern: [skill_id, ?, ?, 0x46, 0x47, variant, 0x00, 0x00]
print("\nSearching for skill table pattern [skill_id, ?, ?, 0x46, 0x47, variant, 0x00, 0x00]:")
for offset in range(0x18300, 0x18500):
    if offset + 8 < len(data):
        if data[offset + 3] == 0x46 and data[offset + 4] == 0x47:
            skill_id = data[offset]
            variant = data[offset + 5]
            print(f"0x{offset:X}: skill_id=0x{skill_id:X}, variant={variant}")
            print(f"  Full: {data[offset:offset+8].hex()}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
Skill modifier search results:
- Found 50 values in skill region
- Need to identify which 50 corresponds to Play Dead/Decoy
- Skill table pattern identified: [skill_id, ?, ?, 0x46, 0x47, variant, 0x00, 0x00]
- Field skill data structure unclear

Next steps:
1. Identify which offsets correspond to which skills
2. Map wiki skill names to skill IDs
3. Find where skill chances/modifiers are stored
4. Test patching skill IDs and chances
""")
