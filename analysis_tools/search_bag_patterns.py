"""Search for bag slot patterns in stageBase_EN.DAT."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Searching for bag slot patterns from wiki:")
print("=" * 70)

data = read_stagebase()

# Wiki bag values
BAG_PATTERNS = [
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

print("\nSearching for [item, magic] patterns:")
for item, magic in BAG_PATTERNS:
    print(f"  Pattern: [{item}, {magic}]")
    
    # Search for [item, magic] as consecutive bytes
    pattern = bytes([item, magic])
    offset = data.find(pattern)
    if offset >= 0:
        print(f"    Found at 0x{offset:X}: {data[offset:offset+16].hex()}")
    
    # Search for [magic, item] as consecutive bytes
    pattern_rev = bytes([magic, item])
    offset = data.find(pattern_rev)
    if offset >= 0:
        print(f"    Found reversed at 0x{offset:X}: {data[offset:offset+16].hex()}")

# Search for all patterns together (class 0-9)
print("\nSearching for all class patterns in sequence:")
# Try different entry sizes
for entry_size in [4, 6, 8, 12, 16]:
    print(f"\nTrying entry size {entry_size}:")
    
    # Check if we can find a sequence of patterns
    found_count = 0
    for offset in range(0x17000, 0x19000, entry_size):
        if offset + entry_size * 10 > len(data):
            break
        
        # Check if we can find the first 10 patterns in sequence
        match = True
        for i, (item, magic) in enumerate(BAG_PATTERNS[:10]):
            entry_offset = offset + i * entry_size
            if entry_offset + 2 > len(data):
                match = False
                break
            
            # Check if this entry contains the pattern
            entry = data[entry_offset:entry_offset+entry_size]
            if item not in entry or magic not in entry:
                match = False
                break
        
        if match:
            print(f"  Potential match at 0x{offset:X} with entry_size={entry_size}")
            for i in range(10):
                entry_offset = offset + i * entry_size
                entry = data[entry_offset:entry_offset+entry_size]
                print(f"    Class {i}: {entry.hex()}")
            found_count += 1
            break
    
    if found_count == 0:
        print(f"  No matches found")

# Search for the specific wiki values in any order
print("\nSearching for individual bag values (6, 8, 10, 12):")
for val in [6, 8, 10, 12]:
    count = data.count(val)
    print(f"  Value {val}: found {count} occurrences")
    
    # Show first few occurrences
    offset = data.find(val)
    if offset >= 0:
        print(f"    First at 0x{offset:X}: {data[max(0,offset-8):min(len(data),offset+8)].hex()}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
If no clear bag data pattern is found, the bag slots may be:
1. Stored in a different format (e.g., packed bits)
2. Calculated dynamically by the game
3. Located in a different file (e.g., DkkStm.exe)
4. Not stored as simple byte values

Recommendation:
- If no pattern found, bag slots may require DLL injection to modify
""")
