"""Analyze the 0x44 value at offset +8 in bag entries."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Analyzing potential UI display value at offset +8:")
print("=" * 70)

data = read_stagebase()

BAG_TABLE_OFFSET = 0x175D0
BAG_ENTRY_SIZE = 16

CLASS_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist",
               "Ninja", "Monk", "Acrobat", "Robo Knight"]

BAG_WIKI = [
    (6, 4),   # Warrior
    (6, 10),  # Magician
    (8, 6),   # Thief
    (6, 8),   # Cleric
    (8, 8),   # Spellsword
    (6, 10),  # Alchemist
    (10, 6),  # Ninja
    (8, 6),   # Monk
    (6, 6),   # Acrobat
    (10, 8),  # Robo Knight
]

print("\nComparing offset +8 value with wiki totals:")
for i in range(10):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    entry = data[offset:offset+BAG_ENTRY_SIZE]
    wiki_item, wiki_magic = BAG_WIKI[i]
    wiki_total = wiki_item + wiki_magic
    
    offset_8_value = entry[8]
    
    print(f"{CLASS_NAMES[i]:<14}: wiki_total={wiki_total:2d}, offset+8=0x{offset_8_value:02X} ({offset_8_value:3d})")

print("\n" + "=" * 70)
print("HYPOTHESIS")
print("=" * 70)

print("""
The 0x44 (68) value at offset +8 might be:
1. A UI display constant (max slots shown)
2. A total capacity value
3. A display mask for which slots are visible

If this controls the visual display, patching it to match
the actual total (item + magic) might fix the graphical bug.

Test: Patch offset +8 to item_slots + magic_slots
""")
