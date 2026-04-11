"""Check the current bag values at the new offset."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Checking bag values at new offset 0x175D0:")
print("=" * 70)

data = read_stagebase()

BAG_TABLE_OFFSET = 0x175D0
BAG_ENTRY_SIZE = 16

CLASS_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist",
               "Ninja", "Monk", "Acrobat", "Robo Knight"]

print("\nCurrent values in original data:")
for i in range(10):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    entry = data[offset:offset+BAG_ENTRY_SIZE]
    item_slots = data[offset + 14]
    magic_slots = data[offset + 15]
    
    print(f"{CLASS_NAMES[i]:<14}: item={item_slots}, magic={magic_slots}")

print("\n" + "=" * 70)
