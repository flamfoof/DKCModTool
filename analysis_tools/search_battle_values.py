"""Search for battle requirement values (7, 8, 10) in stageBase_EN.DAT."""
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
print("SEARCHING FOR BATTLE REQUIREMENT VALUES")
print("=" * 70)

data = read_stagebase()

# Known battle requirements:
# 7 battles: Acrobat, Cleric, Magician, Thief, Warrior (classes 0,1,2,3,8)
# 8 battles: Alchemist, Monk, Ninja, Spellsword (classes 5,6,7,4)
# 10 battles: Hero, Robo Knight (classes 10,9)

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

# Search for patterns that match the class battle requirements
# Look for sequences like [7, 7, 7, 7, 7, 7] (6 levels for a class with 7 battles each)
# Or [8, 8, 8, 8, 8, 8] for classes with 8 battles
# Or [10, 10, 10, 10, 10, 10] for classes with 10 battles

print("\nSearching for class battle requirement patterns:")

# Search for 7 repeated 6 times (for classes with 7 battles)
for offset in range(0x17000, 0x19000):
    if offset + 6 < len(data):
        seq = [data[offset + i] for i in range(6)]
        if seq == [7, 7, 7, 7, 7, 7]:
            print(f"Found [7,7,7,7,7,7] at 0x{offset:X}")
            print(f"  Context: {data[offset-8:offset+14].hex()}")

# Search for 8 repeated 6 times
for offset in range(0x17000, 0x19000):
    if offset + 6 < len(data):
        seq = [data[offset + i] for i in range(6)]
        if seq == [8, 8, 8, 8, 8, 8]:
            print(f"Found [8,8,8,8,8,8] at 0x{offset:X}")
            print(f"  Context: {data[offset-8:offset+14].hex()}")

# Search for 10 repeated 6 times
for offset in range(0x17000, 0x19000):
    if offset + 6 < len(data):
        seq = [data[offset + i] for i in range(6)]
        if seq == [10, 10, 10, 10, 10, 10]:
            print(f"Found [10,10,10,10,10,10] at 0x{offset:X}")
            print(f"  Context: {data[offset-8:offset+14].hex()}")

# Also search for patterns that might represent the class-to-battle mapping
# Maybe stored as: [class_id, battle_count] pairs

print("\nSearching for [class_id, battle_count] patterns:")
for offset in range(0x17000, 0x19000):
    if offset + 2 < len(data):
        class_id = data[offset]
        battle_count = data[offset + 1]
        if class_id <= 11 and battle_count in [7, 8, 10]:
            print(f"0x{offset:X}: Class {class_id} ({JOB_NAMES[class_id]}) -> {battle_count} battles")
            print(f"  Context: {data[offset-4:offset+8].hex()}")

# Search in uint16 format
print("\nSearching for uint16 [class_id, battle_count] patterns:")
for offset in range(0x17000, 0x19000, 2):
    if offset + 4 < len(data):
        class_id = struct.unpack_from('<H', data, offset)[0]
        battle_count = struct.unpack_from('<H', data, offset + 2)[0]
        if class_id <= 11 and battle_count in [7, 8, 10]:
            print(f"0x{offset:X}: Class {class_id} ({JOB_NAMES[class_id]}) -> {battle_count} battles")
            print(f"  Context: {data[offset-4:offset+8].hex()}")

# Also search near the level-up table
print("\nSearching near level-up table (0x1733E):")
for offset in range(0x17300, 0x17500):
    if offset + 2 < len(data):
        class_id = data[offset]
        battle_count = data[offset + 1]
        if class_id <= 11 and battle_count in [7, 8, 10]:
            print(f"0x{offset:X}: Class {class_id} ({JOB_NAMES[class_id]}) -> {battle_count} battles")

# Search in the job unlock region
print("\nSearching in job unlock region (0x18B00-0x18C00):")
for offset in range(0x18B00, 0x18C00):
    if offset + 2 < len(data):
        class_id = data[offset]
        battle_count = data[offset + 1]
        if class_id <= 11 and battle_count in [7, 8, 10]:
            print(f"0x{offset:X}: Class {class_id} ({JOB_NAMES[class_id]}) -> {battle_count} battles")

print("\n" + "=" * 70)
print("SEARCHING FOR SKILL DATA")
print("=" * 70)

# Known skill names to search for
SKILL_NAMES_LIST = ["Charge", "Muscle", "Hustle", "Escape", "Celerity", "Concentrate", "Super Cure", "Alchemy", "Bounty", "Vanish", "Poison", "Counter", "Focus", "Steal", "Pierce", "Transform", "Robo Laser", "Robo Punch", "Item Snatch"]

print("\nSearching for skill names in data:")
for skill_name in SKILL_NAMES_LIST:
    offset = data.find(skill_name.encode('ascii'))
    if offset >= 0:
        print(f"Found '{skill_name}' at 0x{offset:X}")
        print(f"  Context: {data[offset-8:offset+len(skill_name)+8].hex()}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
Search results will show where battle requirements and skill data are located.
If not found in stageBase_EN.DAT, they may be in the executable.
""")
