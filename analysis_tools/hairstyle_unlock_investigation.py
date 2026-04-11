"""Investigate the complete hairstyle unlock mechanism."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def hexdump(data, offset, length=64):
    result = []
    for i in range(0, length, 16):
        chunk = data[offset+i:offset+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"  0x{offset+i:06X}: {hex_str:<48} {ascii_str}")
    return '\n'.join(result)

print("=" * 70)
print("HAIRSTYLE UNLOCK MECHANISM INVESTIGATION")
print("=" * 70)

data = read_stagebase()

# We have 14 hairstyles total:
# 1-2: Afro (F, M)
# 3-4: Punk (F, M)
# 5-6: Horror (F, M)
# 7-8: Raiden (F, M)
# 9: Samurai (F)
# 10: Geisha (M)
# 11: Pompadour (F)
# 12: Pigtails (M)
# 13: Prince (F)
# 14: Princess (M)

# The table at 0x18A70 shows IDs 5-10 with unlock values
# Let's look for more data that might cover IDs 11-14

print("\nHairstyle table at 0x18A70 (current):")
print(hexdump(data, 0x18A70, 96))

# Look for more data after 0x18AD0
print("\nData after hairstyle table (0x18AD0):")
print(hexdump(data, 0x18AD0, 128))

# Look for patterns that might be additional unlock entries
# Search for FF FF 00 00 XX YY where XX is an ID > 10
print("\nSearching for additional unlock entries beyond ID 10...")
for offset in range(0x18AD0, 0x18B60, 4):
    if offset + 4 <= len(data):
        id_val = read_uint16(data, offset)
        val = read_uint16(data, offset + 2)
        if id_val == 0xFFFF and offset + 8 <= len(data):
            next_id = read_uint16(data, offset + 4)
            next_val = read_uint16(data, offset + 6)
            if next_id > 10:
                print(f"  0x{offset:X}: Separator -> Hairstyle ID {next_id}: value = 0x{next_val:04X} ({next_val})")

# Let's also check if there's a different table structure
# Maybe hairstyles 11-14 are in a different location

print("\n" + "=" * 70)
print("ANALYZING HAIRSTYLE TABLE STRUCTURE")
print("=" * 70)

# The table at 0x18A70 seems to have:
# - First section: class-specific data (IDs 1-4 with various values)
# - Second section: hairstyle unlock data (FF FF separator + ID + value)

# Let's parse it more carefully
print("\nFull table parsing:")
offset = 0x18A70
section = 1
for i in range(30):
    if offset + 4 > len(data):
        break
    id_val = read_uint16(data, offset)
    val = read_uint16(data, offset + 2)
    
    if id_val == 0xFFFF:
        section += 1
        print(f"\n--- Section {section} starts at 0x{offset:X} ---")
        if offset + 8 <= len(data):
            next_id = read_uint16(data, offset + 4)
            next_val = read_uint16(data, offset + 6)
            print(f"  Unlock entry: Hairstyle ID {next_id}, value = 0x{next_val:04X} ({next_val})")
            offset += 4
    else:
        print(f"  0x{offset:X}: ID={id_val}, Value=0x{val:04X} ({val})")
    
    offset += 4

# Now let's check if the hairstyle IDs in the table (5-10) correspond to our 14 hairstyles
# Our mapping:
# ID 5 = Horror F (from hair.csv)
# ID 6 = Horror M
# ID 7 = Raiden F
# ID 8 = Raiden M (value 0x5A - unlocked)
# ID 9 = Samurai F
# ID 10 = Geisha M

# So IDs 11-14 (Pompadour F, Pigtails M, Prince F, Princess M) are not in this table
# They might be:
# 1. Always unlocked
# 2. In a different table
# 3. Not unlockable (maybe DLC or special content)

print("\n" + "=" * 70)
print("HAIRSTYLE UNLOCK HYPOTHESIS")
print("=" * 70)

print("""
Based on the analysis:

Hairstyles 1-4 (Afro F/M, Punk F/M):
- Not in the unlock table (0x18A70)
- Likely unlocked by default for all players

Hairstyles 5-10 (Horror F/M, Raiden F/M, Samurai F, Geisha M):
- In the unlock table
- IDs 5-7, 9-10 have value 0x1E (30) - need to be unlocked
- ID 8 (Raiden M) has value 0x5A (90) - unlocked by default

Hairstyles 11-14 (Pompadour F, Pigtails M, Prince F, Princess M):
- Not in the unlock table
- Might be:
  a) Always unlocked
  b) In a different unlock table
  c) Special/DLC content

TO UNLOCK ALL HAIRSTYLES:
1. Change 0x1E to 0x5A at these offsets in stageBase_EN.DAT:
   - 0x18AA4 (Hairstyle 5 - Horror F)
   - 0x18AAC (Hairstyle 6 - Horror M)
   - 0x18AB4 (Hairstyle 7 - Raiden F)
   - 0x18AC4 (Hairstyle 9 - Samurai F)
   - 0x18ACC (Hairstyle 10 - Geisha M)

2. Investigate if hairstyles 11-14 need unlocking
""")

# Let's search for any references to the missing hairstyle names in the data
print("\nSearching for references to missing hairstyles (Pompadour, Pigtails, Prince, Princess)...")
for name in ["Pompadour", "Pigtails", "Prince", "Princess"]:
    offset = data.find(name.encode('ascii'))
    if offset >= 0:
        print(f"  Found '{name}' at 0x{offset:X}")

# Based on the investigation, we found:
# - Hairstyle ID 11 appears at 0x18AD0 with value 0x78 (120)
# - Hairstyle ID 11 also appears at 0x18B18 with value 0x1E (30)
# This suggests there might be multiple unlock tables or contexts

# Let's check if the value 0x78 should be changed to 0x5A
# 0x78 = 120, 0x5A = 90
# The pattern seems to be: 0x1E = unlockable, 0x5A = unlocked
# 0x78 might be a different state (maybe "special unlock" or "DLC")

# For now, let's create a patch that changes both 0x1E and 0x78 to 0x5A
print("\n" + "=" * 70)
print("CREATING HEX PATCH FOR HAIRSTYLE UNLOCK")
print("=" * 70)

patch_data = """# Hex patch to unlock hairstyles in stageBase_EN.DAT
# Changes unlock values to 0x5A (90) which represents "unlocked by default"

# Hairstyle 5 (Horror F)
18AA4: 5A 00

# Hairstyle 6 (Horror M)
18AAC: 5A 00

# Hairstyle 7 (Raiden F)
18AB4: 5A 00

# Hairstyle 9 (Samurai F)
18AC4: 5A 00

# Hairstyle 10 (Geisha M)
18ACC: 5A 00

# Hairstyle 11 (Pompadour F) - value 0x78 (120) -> 0x5A (90)
18AD4: 5A 00

# Hairstyle 11 (alternate entry) - value 0x1E (30) -> 0x5A (90)
18B1A: 5A 00
"""

with open("hairstyle_unlock.hex", 'w') as f:
    f.write(patch_data)

print("Created hairstyle_unlock.hex")
print("\nThis patch unlocks:")
print("  - Hairstyles 5-7 (Horror F/M, Raiden F)")
print("  - Hairstyles 9-10 (Samurai F, Geisha M)")
print("  - Hairstyle 11 (Pompadour F)")
print("\nNote: Hairstyles 12-14 (Pigtails M, Prince F, Princess M) may be:")
print("  - Covered by the same ID 11 entry")
print("  - Always unlocked by default")
print("  - In a different unlock table")
