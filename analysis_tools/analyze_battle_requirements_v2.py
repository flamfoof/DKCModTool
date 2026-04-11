"""Analyze battle requirements by checking the 0x18B60 region more carefully."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint8(data, offset):
    return data[offset]

print("=" * 70)
print("BATTLE REQUIREMENTS DATA STRUCTURE ANALYSIS")
print("=" * 70)

data = read_stagebase()

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

# The pattern at 0x18B60 shows [0, 3, 0, 2, 0, 3, 0, 3, 0, 4, 0, 3]
# Let's check if there's a separate table for battle requirements
# Maybe it's stored as: [class_id, CL1, CL2, CL3, CL4, CL5, CL6]

print("\nSearching for battle requirement table pattern:")
# Look for patterns where class_id is followed by 6 small integers (1-6)
for offset in range(0x18000, 0x19000):
    if offset + 7 < len(data):
        class_id = data[offset]
        if class_id <= 11:  # Valid class ID
            battles = [data[offset + i] for i in range(1, 7)]
            # Check if all are reasonable battle counts (0-10)
            if all(0 <= b <= 10 for b in battles):
                # Check if not all zeros
                if any(b > 0 for b in battles):
                    print(f"0x{offset:X}: Class {class_id} ({JOB_NAMES[class_id]}) - Battles: {battles}")

# Also check if battle requirements are stored in a different format
# Maybe as uint16 values

print("\nSearching for uint16 battle requirement pattern:")
for offset in range(0x18000, 0x19000, 2):
    if offset + 12 < len(data):
        class_id = struct.unpack_from('<H', data, offset)[0]
        if class_id <= 11:
            battles = [struct.unpack_from('<H', data, offset + i)[0] for i in range(2, 14, 2)]
            if all(0 <= b <= 10 for b in battles):
                if any(b > 0 for b in battles):
                    print(f"0x{offset:X}: Class {class_id} ({JOB_NAMES[class_id]}) - Battles: {battles}")

# Let's also check the job unlock region more carefully
print("\nJob unlock region (0x18B60) detailed analysis:")
for i in range(12):
    offset = 0x18B60 + i * 16
    if offset + 16 < len(data):
        print(f"\nClass {i} ({JOB_NAMES[i]}) at 0x{offset:X}:")
        values = [data[offset + j] for j in range(16)]
        print(f"  Full bytes: {values}")
        
        # Try to interpret as battle requirements
        # Pattern might be: [?, CL1, ?, CL2, ?, CL3, ?, CL4, ?, CL5, ?, CL6]
        battles = []
        for j in range(1, 12, 2):
            battles.append(values[j])
        print(f"  Battles (odd positions): {battles}")

# Check if there's a table with class_id followed by 6 battle counts
# Search for: [class_id, 1, 2, 3, 4, 5, 6] pattern

print("\nSearching for [class_id, 1, 2, 3, 4, 5, 6] pattern:")
for offset in range(0x18000, 0x19000):
    if offset + 7 < len(data):
        class_id = data[offset]
        if class_id <= 11:
            seq = [data[offset + i] for i in range(7)]
            if seq[1:] == [1, 2, 3, 4, 5, 6]:
                print(f"Found at 0x{offset:X}: Class {class_id} ({JOB_NAMES[class_id]})")
                print(f"  Context: {data[offset-4:offset+12].hex()}")

# Also check for [class_id, 1, 1, 1, 1, 1, 1] pattern (all 1 battle)

print("\nSearching for [class_id, 1, 1, 1, 1, 1, 1] pattern:")
for offset in range(0x18000, 0x19000):
    if offset + 7 < len(data):
        class_id = data[offset]
        if class_id <= 11:
            seq = [data[offset + i] for i in range(7)]
            if seq[1:] == [1, 1, 1, 1, 1, 1]:
                print(f"Found at 0x{offset:X}: Class {class_id} ({JOB_NAMES[class_id]})")
                print(f"  Context: {data[offset-4:offset+12].hex()}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
Battle requirements analysis:
- No clear pattern found for [class_id, CL1, CL2, CL3, CL4, CL5, CL6]
- The 0x18B60 region contains job descriptions for classes 3+
- Battle requirements might be:
  a) Computed dynamically (not stored in data)
  b) Stored in a different location
  c) Embedded in the level-up table structure
  d) Hardcoded in the executable

Next steps:
- Check the executable for battle requirement logic
- Or accept that battle requirements might not be easily modifiable
""")
