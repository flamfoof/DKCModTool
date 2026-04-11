"""Analyze class level-up battle requirements more carefully."""
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
print("CLASS LEVEL-UP BATTLE REQUIREMENTS ANALYSIS")
print("=" * 70)

data = read_stagebase()

# From the previous analysis, 0x18B60 shows [0, 3, 0, 2, 0, 3]
# This might be the pattern for battle requirements
# Let's check if this repeats for each class

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

print("\nJob unlock region (0x18B60):")
print(hexdump(data, 0x18B60, 96))

# The pattern at 0x18B60 is: 00 00 03 00 02 00 03 00 03 00 04 00 03 00
# This repeats at 0x18B70
# Let's check if there are 12 entries (one per class)

print("\nChecking for 12 entries (one per class):")
for i in range(12):
    offset = 0x18B60 + i * 16
    if offset + 16 < len(data):
        print(f"\nClass {i} ({JOB_NAMES[i]}) at 0x{offset:X}:")
        values = [read_uint8(data, offset + j) for j in range(16)]
        print(f"  Bytes: {values[:8]}")
        
        # Look for pattern like [0, 3, 0, 2, 0, 3, 0, 3, 0, 4, 0, 3]
        # This could represent battles for CL1-CL6
        # Maybe the pattern is: [?, CL1, ?, CL2, ?, CL3, ?, CL4, ?, CL5, ?, CL6]
        battles = []
        for j in range(1, 12, 2):
            battles.append(values[j])
        print(f"  Battles (odd positions): {battles}")

# Also check the level-up table region
print("\n" + "=" * 70)
print("LEVEL-UP TABLE REGION ANALYSIS")
print("=" * 70)

print("\nLevel-up table region (0x185AE):")
print(hexdump(data, 0x185AE, 128))

# The level-up table has entries that might contain battle requirements
# Each entry is 28 bytes (0x1C)
# LEVELUP_ENTRY_SIZE = 28
# LEVELUP_ENTRY_COUNT = 24 (12 classes x 2 variants)

# Let's check if there's battle data interleaved with the stat data
print("\nChecking level-up entries for battle data:")
for class_idx in range(12):
    for variant in range(2):
        entry_idx = class_idx * 2 + variant
        offset = 0x185AE + entry_idx * 28
        if offset + 28 < len(data):
            # The first 10 bytes are stats (att, def, mag, spd, hp as uint16)
            # Check if there's battle data in the remaining 18 bytes
            print(f"\nClass {class_idx} ({JOB_NAMES[class_idx]}) variant {variant} at 0x{offset:X}:")
            values = [read_uint8(data, offset + j) for j in range(28)]
            print(f"  Bytes 0-9 (stats): {values[:10]}")
            print(f"  Bytes 10-27 (other): {values[10:]}")
            
            # Look for small integers that could be battle counts
            potential_battles = [v for v in values[10:] if 1 <= v <= 50]
            if potential_battles:
                print(f"  Potential battle values: {potential_battles}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print("""
The battle requirements are likely in the 0x18B60 region with a pattern like:
[?, CL1, ?, CL2, ?, CL3, ?, CL4, ?, CL5, ?, CL6]

For most classes, the pattern appears to be:
[0, 3, 0, 2, 0, 3, 0, 3, 0, 4, 0, 3]

This might mean:
- CL1: 3 battles
- CL2: 2 battles  
- CL3: 3 battles
- CL4: 3 battles
- CL5: 4 battles
- CL6: 3 battles

But this needs verification against actual gameplay.
""")
