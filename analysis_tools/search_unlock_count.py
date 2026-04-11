"""Search for hairstyle unlock count mechanism."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Searching for hairstyle unlock count mechanism:")
print("=" * 70)

data = read_stagebase()

# If only 3 hairstyles are showing initially, look for value 3
# Search for small integers that might be unlock counts
print("\nSearching for potential unlock count values (1-14):")
for val in range(1, 15):
    count = data.count(val)
    if count > 0 and count < 100:  # Not too common
        print(f"Value {val}: found {count} occurrences")
        offset = data.find(val)
        if offset >= 0:
            context_start = max(0, offset - 8)
            context_end = min(len(data), offset + 16)
            print(f"  First at 0x{offset:X}: {data[context_start:context_end].hex()}")

# Search specifically for value 3 (initial unlocked count)
print("\nDetailed search for value 3 (initial unlock count):")
offset = data.find(3)
while offset >= 0:
    context_start = max(0, offset - 16)
    context_end = min(len(data), offset + 32)
    context = data[context_start:context_end]
    
    # Only show if it looks like it might be in a structured table
    if context.count(0) > 2:  # Has some zeros around it
        print(f"0x{offset:X}: {context.hex()}")
    
    offset = data.find(3, offset + 1)
    if offset > 0x20000:  # Don't search too far
        break

# Search for arrays that might list unlocked hairstyle IDs
print("\nSearching for arrays that might list unlocked hairstyle IDs:")
# Look for patterns like [0, 1, 2] (first 3 hairstyles)
pattern = bytes([0, 1, 2])
offset = data.find(pattern)
if offset >= 0:
    context_start = max(0, offset - 8)
    context_end = min(len(data), offset + 24)
    print(f"Found pattern [0,1,2] at 0x{offset:X}: {data[context_start:context_end].hex()}")

# Look for patterns like [0, 1, 2, 3] (if more are unlocked)
pattern = bytes([0, 1, 2, 3])
offset = data.find(pattern)
if offset >= 0:
    context_start = max(0, offset - 8)
    context_end = min(len(data), offset + 24)
    print(f"Found pattern [0,1,2,3] at 0x{offset:X}: {data[context_start:context_end].hex()}")

print("\n" + "=" * 70)
