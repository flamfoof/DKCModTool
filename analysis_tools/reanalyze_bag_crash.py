"""Re-analyze bag data structure to debug crash issue."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Re-analyzing bag data structure to debug crash:")
print("=" * 70)

data = read_stagebase()

# Current offset being used
BAG_TABLE_OFFSET = 0x1884E
BAG_ENTRY_SIZE = 8

print(f"\nCurrent bag table offset: 0x{BAG_TABLE_OFFSET:X}")
print(f"Current entry size: {BAG_ENTRY_SIZE} bytes")

# Hex dump of the region
print("\nHex dump of bag table region (0x18840):")
for i in range(0, 128, 16):
    offset = 0x18840 + i
    chunk = data[offset:offset+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f"  0x{offset:X}: {hex_str}")

# Check if this region looks like valid data
print("\nAnalyzing data structure at 0x1884E:")
for entry_idx in range(20):  # 10 classes x 2 variants
    offset = BAG_TABLE_OFFSET + entry_idx * BAG_ENTRY_SIZE
    if offset + 8 > len(data):
        break
    
    entry = data[offset:offset+8]
    print(f"Entry {entry_idx}: {entry.hex()}")

# Search for patterns that might indicate bag data
# Look for small integers that could be bag slots (0-20)
print("\nSearching for potential bag slot patterns (0-20):")
for offset in range(0x18000, 0x19000):
    if offset + 2 < len(data):
        val = data[offset]
        if 0 <= val <= 20:
            # Check if next byte is also in range
            val2 = data[offset + 1]
            if 0 <= val2 <= 20:
                # Check if this looks like a pattern
                # Look for class_id (0-11) nearby
                class_id = data[offset + 2]
                if 0 <= class_id <= 11:
                    print(f"0x{offset:X}: potential bag data [{val}, {val2}], class_id={class_id}")
                    print(f"  Context: {data[offset-4:offset+8].hex()}")

# Check if 0x1884E is in a valid data region
print("\nChecking if 0x1884E is in valid data region:")
# Look for the job unlock table at 0x18B60 (from data_tables.py)
JOB_UNLOCK_OFFSET = 0x18B60
print(f"Job unlock table at 0x{JOB_UNLOCK_OFFSET:X}")
print(f"Distance from bag table: 0x{JOB_UNLOCK_OFFSET - BAG_TABLE_OFFSET:X}")

# Check what's between 0x1884E and 0x18B60
print("\nData between 0x1884E and 0x18B60:")
print(f"Length: 0x{JOB_UNLOCK_OFFSET - BAG_TABLE_OFFSET:X} bytes ({JOB_UNLOCK_OFFSET - BAG_TABLE_OFFSET} decimal)")
for i in range(0, JOB_UNLOCK_OFFSET - BAG_TABLE_OFFSET, 16):
    offset = BAG_TABLE_OFFSET + i
    chunk = data[offset:offset+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f"  0x{offset:X}: {hex_str}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
If the bag data offset is incorrect, the patching may be corrupting
other data structures, causing the crash.

Possible issues:
1. Offset 0x1884E may be wrong
2. Entry structure may be wrong
3. Bag data may not be at this location at all

Recommendation:
- Temporarily disable bag patching to confirm it's the cause
- Search for actual bag data patterns in the file
- Verify the data structure before patching
""")
