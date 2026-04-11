"""Search for wiki bag values in stageBase_EN.DAT."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Searching for wiki bag values in stageBase_EN.DAT:")
print("=" * 70)

data = read_stagebase()

# Wiki values:
# Warrior: 6 items, 4 magic
# Magician: 6 items, 10 magic
# Thief: 8 items, 6 magic
# Cleric: 6 items, 8 magic
# Spellsword: 8 items, 8 magic
# Alchemist: 6 items, 10 magic
# Ninja: 10 items, 6 magic
# Monk: 8 items, 6 magic
# Acrobat: 6 items, 6 magic
# Robo Knight: 10 items, 8 magic
# Hero: 12 items, 12 magic

wiki_values = [
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
    (12, 12), # Hero
]

print("\nSearching for wiki [item, magic] pairs:")
for item, magic in wiki_values:
    print(f"\nSearching for [{item}, {magic}]:")
    found = False
    for offset in range(len(data) - 1):
        if data[offset] == item and data[offset + 1] == magic:
            print(f"  Found at 0x{offset:X}")
            print(f"    Context: {data[max(0, offset-8):min(len(data), offset+16)].hex()}")
            found = True
            # Only show first few occurrences
            if found:
                count = 0
                for i in range(offset + 2, min(len(data), offset + 100)):
                    if data[i] == item and data[i+1] == magic and i + 1 < len(data):
                        count += 1
                        if count >= 3:
                            break
                break
    if not found:
        print(f"  Not found")

# Also search for the reverse [magic, item] pattern
print("\nSearching for [magic, item] pairs (reverse):")
for item, magic in wiki_values:
    print(f"\nSearching for [{magic}, {item}]:")
    found = False
    for offset in range(len(data) - 1):
        if data[offset] == magic and data[offset + 1] == item:
            print(f"  Found at 0x{offset:X}")
            print(f"    Context: {data[max(0, offset-8):min(len(data), offset+16)].hex()}")
            found = True
            break
    if not found:
        print(f"  Not found")

# Search for class_id followed by wiki values
print("\nSearching for class_id followed by wiki values:")
JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero"]

for class_idx, (item, magic) in enumerate(wiki_values):
    if class_idx >= len(JOB_NAMES):
        break
    
    print(f"\n{JOB_NAMES[class_idx]} (class {class_idx}): {item} items, {magic} magic")
    
    # Search for class_id followed by [item, magic]
    for offset in range(len(data) - 10):
        if data[offset] == class_idx:
            if offset + 2 < len(data) and data[offset + 1] == item and data[offset + 2] == magic:
                print(f"  Found at 0x{offset:X}: class_id={class_idx}, item={item}, magic={magic}")
                print(f"    Context: {data[max(0, offset-4):min(len(data), offset+12)].hex()}")
                break
