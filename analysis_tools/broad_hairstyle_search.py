"""Broad search for hairstyle unlock mechanism across entire file."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

print("Broad search for hairstyle unlock mechanism:")
print("=" * 70)

data = read_stagebase()

# Search for all occurrences of value 3 and check context
print("\nSearching for value 3 with structured context:")
offset = data.find(3)
count = 0
while offset >= 0 and count < 50:  # Limit to first 50 occurrences
    context_start = max(0, offset - 8)
    context_end = min(len(data), offset + 16)
    context = data[context_start:context_end]
    
    # Check if this looks like a structured context (lots of zeros, small integers)
    zero_count = context.count(0)
    small_int_count = sum(1 for b in context if 0 < b < 20)
    
    if zero_count > 5 and small_int_count > 3:
        print(f"0x{offset:X}: {context.hex()} (zeros={zero_count}, small={small_int_count})")
        count += 1
    
    offset = data.find(3, offset + 1)

# Search for arrays of consecutive integers
print("\nSearching for arrays of consecutive integers (0,1,2,3...):")
for offset in range(0, len(data) - 10):
    vals = [data[offset + i] for i in range(10)]
    if vals == list(range(10)):  # Perfect sequence 0-9
        context_start = max(0, offset - 8)
        context_end = min(len(data), offset + 24)
        print(f"Found [0-9] at 0x{offset:X}: {data[context_start:context_end].hex()}")

# Search for pattern [0,1,2] specifically
print("\nSearching for pattern [0,1,2]:")
pattern = bytes([0, 1, 2])
offset = data.find(pattern)
while offset >= 0:
    context_start = max(0, offset - 8)
    context_end = min(len(data), offset + 20)
    context = data[context_start:context_end]
    print(f"0x{offset:X}: {context.hex()}")
    offset = data.find(pattern, offset + 1)
    if offset > 0x20000:  # Don't search too far
        break

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

print("""
If no clear unlock mechanism is found in stageBase_EN.DAT, the hairstyle
unlock might be controlled by:
1. DkkStm.exe (game executable)
2. A different DAT file
3. Calculated dynamically based on save data
4. Requires DLL injection to modify the unlock check function

Recommendation: If hex patching doesn't work, consider using DLL injection
to hook the hairstyle unlock function and force all hairstyles to be available.
""")
