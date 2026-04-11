"""Search for UI display values for bag slots."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Searching for UI display values for bag slots:")
print("=" * 70)

data = read_stagebase()

BAG_TABLE_OFFSET = 0x175D0
BAG_ENTRY_SIZE = 16

CLASS_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist",
               "Ninja", "Monk", "Acrobat", "Robo Knight"]

print("\nFull bag entry structure at 0x175D0:")
for i in range(10):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    entry = data[offset:offset+BAG_ENTRY_SIZE]
    
    print(f"\n{CLASS_NAMES[i]} (class {i}):")
    print(f"  Full entry: {entry.hex()}")
    
    # Show each byte with offset
    for j in range(16):
        print(f"    Offset +{j:2d}: 0x{entry[j]:02X} ({entry[j]:3d})")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

print("""
Looking at the entry structure:
- Bytes 0-13: Unknown (may contain UI display data)
- Byte 14: item_slots
- Byte 15: magic_slots

The UI display bug suggests there's a separate value that controls
which slots are visually shown as available.

Possible locations:
1. Bytes 0-13 in the bag entry (total_cap or display_mask)
2. Separate UI table elsewhere in the file
3. Calculated dynamically by the game

Recommendation:
- Look for a value that matches the wiki total_cap (item + magic)
- Warrior: 6+4=10, Magician: 6+10=16, Thief: 8+6=14, etc.
- Check if any byte in bytes 0-13 matches these totals
""")
