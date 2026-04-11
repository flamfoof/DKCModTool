"""Analyze bag data structure more carefully."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Analyzing bag data structure at 0x1884E:")
print("=" * 70)

data = read_stagebase()

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

# From analyze_data.py, the bag data structure might be different
# Let me check what the actual structure is

BAG_TABLE_OFFSET = 0x1884E
BAG_ENTRY_SIZE = 8

print("\nRaw bytes for first 10 entries:")
for i in range(10):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    bytes_data = data[offset:offset+8]
    print(f"Entry {i} at 0x{offset:X}: {bytes_data.hex()}")

# Try different structure interpretations
print("\n" + "=" * 70)
print("Trying different structure interpretations:")
print("=" * 70)

# Interpretation 1: [class_idx, variant, item_slots, magic_slots, total_cap, ...]
print("\nInterpretation 1: [class_idx, variant, item_slots, magic_slots, total_cap, ...]")
for i in range(10):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    class_idx = data[offset]
    variant = data[offset + 1]
    item_slots = data[offset + 2]
    magic_slots = data[offset + 3]
    total_cap = data[offset + 4]
    
    if class_idx <= 11:
        variant_str = "M" if variant == 0 else "F"
        class_name = JOB_NAMES[class_idx]
        print(f"Entry {i}: {class_name} {variant_str} - items={item_slots}, magic={magic_slots}, total={total_cap}")

# Interpretation 2: [item_slots, magic_slots, total_cap, class_idx, variant, ...]
print("\nInterpretation 2: [item_slots, magic_slots, total_cap, class_idx, variant, ...]")
for i in range(10):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    item_slots = data[offset]
    magic_slots = data[offset + 1]
    total_cap = data[offset + 2]
    class_idx = data[offset + 3]
    variant = data[offset + 4]
    
    if class_idx <= 11:
        variant_str = "M" if variant == 0 else "F"
        class_name = JOB_NAMES[class_idx]
        print(f"Entry {i}: {class_name} {variant_str} - items={item_slots}, magic={magic_slots}, total={total_cap}")

# Interpretation 3: Check if the data is uint16 instead of uint8
print("\nInterpretation 3: Using uint16 for some fields")
for i in range(10):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    # Try: [item_slots (uint16), magic_slots (uint16), ...]
    item_slots = struct.unpack_from('<H', data, offset)[0]
    magic_slots = struct.unpack_from('<H', data, offset + 2)[0]
    total_cap = struct.unpack_from('<H', data, offset + 4)[0]
    class_idx = data[offset + 6]
    variant = data[offset + 7]
    
    if class_idx <= 11:
        variant_str = "M" if variant == 0 else "F"
        class_name = JOB_NAMES[class_idx]
        print(f"Entry {i}: {class_name} {variant_str} - items={item_slots}, magic={magic_slots}, total={total_cap}")
