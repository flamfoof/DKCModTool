"""Analyze the [0,1,2] pattern at 0x17AB as potential unlock array."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Analyzing [0,1,2] pattern at 0x17AB:")
print("=" * 70)

data = read_stagebase()

OFFSET = 0x17AB

print(f"\nContext around 0x{OFFSET:X}:")
context_start = max(0, OFFSET - 32)
context_end = min(len(data), OFFSET + 64)
context = data[context_start:context_end]
print(f"  {context.hex()}")

print(f"\nDetailed view of array at 0x{OFFSET:X}:")
for i in range(20):  # Check 20 entries
    offset = OFFSET + i
    if offset < len(data):
        val = data[offset]
        print(f"  Offset +{i}: 0x{val:02X} ({val})")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

print("""
The pattern [0,1,2] at 0x17AB looks like an array of unlocked hairstyle IDs.
If this is the unlock mechanism, extending this array to [0,1,2,3,4,5,6,7,8,9,10,11,12,13]
might unlock all 14 hairstyles.

This appears to be a simple byte array where each byte represents an unlocked hairstyle ID.
The game probably reads this array and only shows hairstyles listed in it.

To unlock all hairstyles, we would need to:
1. Change the array length/count if there's one
2. Fill the array with all hairstyle IDs (0-13)

Let me check if there's a count value before this array.
""")

# Check for count value before the array
for i in range(1, 10):
    offset = OFFSET - i
    if offset >= 0:
        val = data[offset]
        print(f"  Offset -{i} (0x{offset:X}): 0x{val:02X} ({val})")

print("\n" + "=" * 70)
