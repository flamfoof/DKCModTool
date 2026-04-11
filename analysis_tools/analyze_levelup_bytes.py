"""Analyze the 18-byte structure in level-up entries systematically."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint8(data, offset):
    return data[offset]

print("=" * 70)
print("LEVEL-UP 18-BYTE STRUCTURE ANALYSIS")
print("=" * 70)

data = read_stagebase()

RAW_LEVELUP_OFFSET = 0x1733E
ENTRY_SIZE = 28

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight", "Hero", "Darkling"]

# Collect the 18-byte structures for all entries
byte_structures = []

for entry_idx in range(24):
    offset = RAW_LEVELUP_OFFSET + entry_idx * ENTRY_SIZE
    class_idx = entry_idx // 2
    variant = entry_idx % 2
    
    # Get the 18 bytes after the stats (bytes 10-27)
    structure = data[offset+10:offset+28]
    byte_structures.append({
        "class_idx": class_idx,
        "variant": variant,
        "structure": structure,
        "bytes": list(structure)
    })

# Analyze each byte position across all entries
print("\nAnalyzing byte positions 0-17 across all 24 entries:")
for byte_pos in range(18):
    values = [entry["bytes"][byte_pos] for entry in byte_structures]
    unique_values = sorted(set(values))
    print(f"\nByte position {byte_pos}:")
    print(f"  Unique values: {unique_values}")
    print(f"  Range: {min(values)} - {max(values)}")
    
    # Check if this looks like battle requirements (small integers)
    if all(0 <= v <= 10 for v in unique_values):
        print(f"  -> Could be battle requirement!")
        # Show which classes have which values
        for entry in byte_structures:
            val = entry["bytes"][byte_pos]
            if val > 0:
                variant_str = "M" if entry["variant"] == 0 else "F"
                print(f"    Class {entry['class_idx']} ({JOB_NAMES[entry['class_idx']]} {variant_str}): {val}")

# Look for patterns across byte positions
print("\n" + "=" * 70)
print("LOOKING FOR PATTERNS ACROSS BYTE POSITIONS")
print("=" * 70)

# Check if there's a sequence like [1, 2, 3, 4, 5, 6] in any entry
for entry in byte_structures:
    structure = entry["bytes"]
    for i in range(len(structure) - 5):
        seq = structure[i:i+6]
        if seq == [1, 2, 3, 4, 5, 6]:
            variant_str = "M" if entry["variant"] == 0 else "F"
            print(f"Found [1,2,3,4,5,6] in Class {entry['class_idx']} ({JOB_NAMES[entry['class_idx']]} {variant_str}) at byte pos {i}")

# Check for repeating patterns
print("\nChecking for repeating values within entries:")
for entry in byte_structures:
    structure = entry["bytes"]
    counts = {}
    for val in structure:
        counts[val] = counts.get(val, 0) + 1
    if any(count > 5 for count in counts.values()):
        variant_str = "M" if entry["variant"] == 0 else "F"
        print(f"Class {entry['class_idx']} ({JOB_NAMES[entry['class_idx']]} {variant_str}): {counts}")

# Compare male vs female variants
print("\n" + "=" * 70)
print("COMPARING MALE VS FEMALE VARIANTS")
print("=" * 70)

for class_idx in range(12):
    male_entry = byte_structures[class_idx * 2]
    female_entry = byte_structures[class_idx * 2 + 1]
    
    if male_entry["bytes"] == female_entry["bytes"]:
        print(f"Class {class_idx} ({JOB_NAMES[class_idx]}): Male == Female")
    else:
        diff_count = sum(1 for i in range(18) if male_entry["bytes"][i] != female_entry["bytes"][i])
        print(f"Class {class_idx} ({JOB_NAMES[class_idx]}): {diff_count} bytes differ")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
The 18-byte structure analysis shows:
- Each byte position has limited unique values (mostly 0, 1, 2, 3, etc.)
- Some byte positions could represent battle requirements
- Need to identify which byte positions correspond to CL1-CL6 battle counts
- The pattern might be: [CL1, CL2, CL3, CL4, CL5, CL6, ...other data...]
""")
