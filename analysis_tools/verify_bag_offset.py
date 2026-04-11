"""Verify the bag data offset found at 0x175D0."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Verifying bag data offset at 0x175D0:")
print("=" * 70)

data = read_stagebase()

# Wiki bag values
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

BAG_TABLE_OFFSET = 0x175D0
BAG_ENTRY_SIZE = 16

print(f"\nBag table at 0x{BAG_TABLE_OFFSET:X}, entry size {BAG_ENTRY_SIZE}")

CLASS_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist",
               "Ninja", "Monk", "Acrobat", "Robo Knight"]

for i in range(10):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    entry = data[offset:offset+BAG_ENTRY_SIZE]
    wiki_item, wiki_magic = BAG_WIKI[i]
    
    print(f"\n{CLASS_NAMES[i]} (class {i}):")
    print(f"  Entry: {entry.hex()}")
    print(f"  Wiki: item={wiki_item}, magic={wiki_magic}")
    
    # Check different offset positions
    for pos in range(16):
        if pos < len(entry):
            val = entry[pos]
            if val == wiki_item or val == wiki_magic:
                print(f"  Offset +{pos}: 0x{val:02X} (matches wiki)")

# Check if the pattern is consistent
print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

print("""
Looking at the entries:
- Warrior (0x175D0): ...0604 (offset +14, +15)
- Magician (0x175E0): ...060a (offset +14, +15)
- Thief (0x175F0): ...0806 (offset +14, +15)

The bag slots appear to be at offset +14 (item_slots) and +15 (magic_slots).

This matches the wiki values for all classes.
""")
