"""Re-analyze battle requirement table with correct structure."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint8(data, offset):
    return data[offset]

print("=" * 70)
print("BATTLE REQUIREMENT TABLE RE-ANALYSIS")
print("=" * 70)

data = read_stagebase()

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

# The battle requirement table is at 0x1768C
# Structure appears to be: [class_id, variant, battle_count, 0x00, 0x3E, 0x00, 0x00, 0x00]
# Entry size: 8 bytes
# 24 entries (12 classes x 2 variants)

BATTLE_TABLE_OFFSET = 0x1768C

print(f"\nBattle requirement table at 0x{BATTLE_TABLE_OFFSET:X}:")
print(f"Structure: [class_id, variant, battle_count, 0x00, 0x3E, 0x00, 0x00, 0x00]")

print("\nParsed battle requirement table:")
for class_idx in range(12):
    for variant in range(2):
        offset = BATTLE_TABLE_OFFSET + (class_idx * 2 + variant) * 8
        class_id = read_uint8(data, offset)
        variant_id = read_uint8(data, offset + 1)
        battle_count = read_uint8(data, offset + 2)
        
        variant_str = "M" if variant_id == 0 else "F"
        print(f"  Class {class_idx} ({JOB_NAMES[class_idx]}) {variant_str}: {battle_count} battles per level")

print("\nExpected battle requirements:")
print("  Warrior, Magician, Thief, Cleric, Acrobat: 7 battles")
print("  Spellsword, Alchemist, Ninja, Monk: 8 battles")
print("  Robo Knight, Hero: 10 battles")
print("  Darkling: ? battles")

# Update data_tables.py with this structure
print("\n" + "=" * 70)
print("UPDATING data_tables.py")
print("=" * 70)

DATA_TABLES_PATH = r"..\data_tables.py"

# Read the current data_tables.py
with open(DATA_TABLES_PATH, 'r') as f:
    content = f.read()

# Add the battle requirement table definition
battle_table_def = '''
# --- Class Level-Up Battle Requirements ---
# Battles required to level up each class level
# Structure: [class_id, variant, battle_count, 0x00, 0x3E, 0x00, 0x00, 0x00]
# Entry size: 8 bytes
# 24 entries (12 classes x 2 variants)
BATTLE_REQ_OFFSET = 0x1768C
BATTLE_REQ_ENTRY_SIZE = 8
BATTLE_REQ_ENTRY_COUNT = 24
'''

# Find where to insert it (after SKILL_NAMES)
insert_pos = content.find('# --- Job Unlock Requirements ---')
if insert_pos >= 0:
    content = content[:insert_pos] + battle_table_def + '\n' + content[insert_pos:]
    
    with open(DATA_TABLES_PATH, 'w') as f:
        f.write(content)
    
    print("Added battle requirement table definition to data_tables.py")
else:
    print("Could not find insertion point in data_tables.py")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print("""
Battle requirement table structure identified:
- Offset: 0x1768C
- Entry size: 8 bytes
- Structure: [class_id, variant, battle_count, 0x00, 0x3E, 0x00, 0x00, 0x00]
- 24 entries (12 classes x 2 variants)
- Battle count at offset +2

Next steps:
- Update class_stats.json to include battle requirements
- Update build_mod.py to patch battle requirements
- Continue investigating skill data structure
- Consider DLL injection for runtime analysis if needed
""")
