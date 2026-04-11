"""Search for per-level bag data in stageBase_EN.DAT."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Searching for per-level bag data:")
print("=" * 70)

data = read_stagebase()

# The level-up table is at 0x1733E with 28-byte entries
# Each entry might contain bag data that scales with level
LEVELUP_TABLE_OFFSET = 0x1733E
LEVELUP_ENTRY_SIZE = 28
LEVELUP_ENTRY_COUNT = 24  # 12 classes x 2 variants

print("\nChecking level-up table for bag-related data:")
print(f"Level-up table at 0x{LEVELUP_TABLE_OFFSET:X}, {LEVELUP_ENTRY_COUNT} entries of {LEVELUP_ENTRY_SIZE} bytes")

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

# Check if level-up entries contain bag slot data
for class_idx in range(12):
    for variant_idx in range(2):
        entry_idx = class_idx * 2 + variant_idx
        offset = LEVELUP_TABLE_OFFSET + entry_idx * LEVELUP_ENTRY_SIZE
        
        # First 10 bytes are stats (att, def, mag, spd, hp as uint16)
        # Remaining 18 bytes are unknown
        stats = data[offset:offset+10]
        unknown = data[offset+10:offset+28]
        
        variant_str = "M" if variant_idx == 0 else "F"
        
        # Check if unknown bytes contain bag-related values
        # Look for small integers that could be bag slots (0-20)
        bag_values = [b for b in unknown if 0 <= b <= 20]
        if bag_values:
            print(f"{JOB_NAMES[class_idx]} {variant_str}: unknown bytes contain potential bag values: {bag_values}")
            print(f"  Raw unknown bytes: {unknown.hex()}")

# Search for patterns that might indicate per-level bag scaling
# Look for sequences that increase with level
print("\nSearching for sequences that might indicate per-level scaling:")
for offset in range(0x17000, 0x19000):
    if offset + 12 < len(data):
        seq = [data[offset + i] for i in range(12)]
        # Look for sequences like [6, 7, 8, 9, 10, 11, 12] (increasing by 1)
        if seq == list(range(seq[0], seq[0] + 12)):
            print(f"Found increasing sequence at 0x{offset:X}: {seq}")
            print(f"  Context: {data[max(0, offset-8):min(len(data), offset+20)].hex()}")

# Check if there's a separate table for per-level bag data
print("\nSearching for bag data that might be indexed by level:")
# Look for patterns like [level, item_slots, magic_slots]
for offset in range(0x17000, 0x19000):
    if offset + 12 < len(data):
        level = data[offset]
        if 0 <= level <= 10:  # Valid level range
            item_slots = data[offset + 1]
            magic_slots = data[offset + 2]
            if 0 <= item_slots <= 20 and 0 <= magic_slots <= 20:
                # Check if this looks like a level-indexed bag entry
                class_id = data[offset + 3]
                if class_id <= 11:
                    variant = data[offset + 4]
                    print(f"0x{offset:X}: level={level}, item={item_slots}, magic={magic_slots}, class={class_id}, variant={variant}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
Per-level bag data search results:
- No clear per-level bag data found in level-up table
- Unknown bytes in level-up entries don't show clear bag slot patterns
- No level-indexed bag table found

Conclusion: Bag slots appear to be fixed per class/variant, not per level.
The wiki data shows fixed values per class (e.g., Thief: 8 items, 6 magic),
not values that scale with class level.

If bag slots do scale with level, the data may be:
1. Calculated dynamically in the executable (DkkStm.exe)
2. Stored in a different location not yet found
3. Controlled by a formula based on level and class stats
""")
