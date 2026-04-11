"""Search for Thief bag data with 6 items and 10 magic."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Searching for Thief (class 2) bag data with 6 items and 10 magic:")
print("=" * 70)

data = read_stagebase()

# Search for the pattern [6, 10] anywhere in the file
print("\nSearching for [6, 10] pattern in entire file:")
for offset in range(len(data) - 1):
    if data[offset] == 6 and data[offset + 1] == 10:
        print(f"Found [6, 10] at 0x{offset:X}")
        print(f"  Context: {data[max(0, offset-8):min(len(data), offset+16)].hex()}")

# Search for [10, 6] pattern
print("\nSearching for [10, 6] pattern in entire file:")
for offset in range(len(data) - 1):
    if data[offset] == 10 and data[offset + 1] == 6:
        print(f"Found [10, 6] at 0x{offset:X}")
        print(f"  Context: {data[max(0, offset-8):min(len(data), offset+16)].hex()}")

# Search for class_id=2 followed by 6 and 10
print("\nSearching for class_id=2 followed by 6 and 10:")
for offset in range(len(data) - 10):
    if data[offset] == 2:
        # Check next bytes for 6 and 10
        for i in range(1, 10):
            if offset + i < len(data) and data[offset + i] == 6:
                if offset + i + 1 < len(data) and data[offset + i + 1] == 10:
                    print(f"Found class_id=2 at 0x{offset:X}, then 6 at +{i}, 10 at +{i+1}")
                    print(f"  Context: {data[max(0, offset-4):min(len(data), offset+16)].hex()}")

# Search in the bag data region specifically
print("\nSearching bag data region (0x1884E) for class 2:")
BAG_TABLE_OFFSET = 0x1884E
BAG_ENTRY_SIZE = 8

for i in range(20):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    class_idx = data[offset + 6]
    if class_idx == 2:
        variant = data[offset + 7]
        print(f"Entry {i} at 0x{offset:X}: class_idx=2, variant={variant}")
        print(f"  Raw bytes: {data[offset:offset+8].hex()}")
        print(f"  item_slots (offset 0): {data[offset]}")
        print(f"  magic_slots (offset 1): {data[offset+1]}")
        print(f"  total_cap (offset 2): {data[offset+2]}")
