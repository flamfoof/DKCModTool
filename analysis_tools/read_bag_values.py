"""Read current bag values for classes 0-9."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint8(data, offset):
    return data[offset]

print("Bag data for classes 0-9 (Warrior through Acrobat):")
print("=" * 70)

data = read_stagebase()

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight"]

BAG_TABLE_OFFSET = 0x1884E
BAG_ENTRY_SIZE = 8

for class_idx in range(10):
    for variant in range(2):
        offset = BAG_TABLE_OFFSET + (class_idx * 2 + variant) * BAG_ENTRY_SIZE
        item_slots = read_uint8(data, offset)
        magic_slots = read_uint8(data, offset + 1)
        total_cap = read_uint8(data, offset + 2)
        
        variant_str = "M" if variant == 0 else "F"
        print(f"{JOB_NAMES[class_idx]:<14} {variant_str:<6}: item_slots={item_slots}, magic_slots={magic_slots}, total_cap={total_cap}")
