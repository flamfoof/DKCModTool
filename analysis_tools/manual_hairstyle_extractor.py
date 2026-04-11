"""Manually extract hairstyle data based on the pattern we found."""
import struct
import csv

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"
TABLE_SAMPLE_DIR = r"table_sample"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def read_string(data, offset, max_len=64):
    end = offset
    while end < offset + max_len and data[end] != 0:
        end += 1
    return data[offset:end].decode('ascii', errors='replace')

def hexdump(data, offset, length=64):
    result = []
    for i in range(0, length, 16):
        chunk = data[offset+i:offset+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"  0x{offset+i:06X}: {hex_str:<48} {ascii_str}")
    return '\n'.join(result)

print("=" * 70)
print("MANUAL HAIRSTYLE DATA EXTRACTION")
print("=" * 70)

data = read_stagebase()

# From the earlier analysis, we know:
# - Afro is at 0xBCD8 (pattern: 96 00 00 00 18 02 68 00 Afro)
# - Punk is at 0xBCF0 (pattern: 96 00 00 00 19 03 68 00 Punk)
# - Horror is at 0xBD20 (pattern: 96 00 00 00 1A 04 68 00 Horror)
# - Raiden is at 0xBD38 (pattern: 96 00 00 00 1B 05 68 00 Raiden)

# The pattern seems to be:
# 96 00 00 00 [id_byte] [variant_byte] 68 00 [name]
# where id_byte seems to increment: 0x18=24, 0x19=25, 0x1A=26, 0x1B=27
# variant_byte: 0x02 for first variant, 0x03 for second, etc.

print("\nHairstyle name region (0xBCD0):")
print(hexdump(data, 0xBCD0, 128))

# Let's manually extract based on the pattern we see
# Pattern: 96 00 00 00 [id_byte] [variant_byte] 68 00 [name]
# The id_byte increments: 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F
# The variant byte: 0x02 for M, 0x03 for F (alternating)

hairstyles = []
# The pattern 96 00 00 00 starts at these offsets
expected_offsets = [0xBCD0, 0xBCE0, 0xBCF0, 0xBD00, 0xBD10, 0xBD20, 0xBD30, 0xBD40]
id_bytes = [0x18, 0x19, 0x19, 0x1A, 0x1A, 0x1B, 0x1B, 0x1D]
variants = ["M", "F", "M", "F", "M", "F", "M", "F"]
names = ["Afro", "Afro", "Punk", "Punk", "Horror", "Horror", "Horror", "Horror"]

for i, (offset, expected_id, variant, expected_name) in enumerate(zip(expected_offsets, id_bytes, variants, names)):
    if offset + 8 < len(data):
        if data[offset:offset+4] == b'\x96\x00\x00\x00':
            id_byte = data[offset + 4]
            variant_byte = data[offset + 5]
            if data[offset+6:offset+8] == b'\x68\x00':
                name = read_string(data, offset + 8, 32)
                hairstyles.append({
                    "id": i + 1,
                    "hair_name": name,
                    "variant": variant,
                    "id_byte": id_byte,
                    "offset": f"0x{offset:X}"
                })
                print(f"Entry {i+1}: {name} ({variant}) - ID byte 0x{id_byte:02X} at 0x{offset:X}")

print(f"\nTotal hairstyles found: {len(hairstyles)}")

# Update hair.csv
with open(TABLE_SAMPLE_DIR + "/hair.csv", 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["id", "hair_name", "variant"])
    for h in hairstyles:
        writer.writerow([h['id'], h['hair_name'], h['variant']])

print(f"Updated hair.csv with {len(hairstyles)} entries")

# Now analyze the hairstyle table at 0x18A70 to understand the unlock mechanism
print("\n" + "=" * 70)
print("HAIRSTYLE UNLOCK TABLE ANALYSIS")
print("=" * 70)

print("\nHairstyle table at 0x18A70:")
print(hexdump(data, 0x18A70, 96))

print("\nParsing the unlock entries:")
offset = 0x18A70
for i in range(24):
    id_val = read_uint16(data, offset)
    val = read_uint16(data, offset + 2)
    
    if id_val == 0xFFFF:
        # Separator - next entry is the actual hairstyle ID
        if i + 1 < 24:
            next_id = read_uint16(data, offset + 4)
            next_val = read_uint16(data, offset + 6)
            print(f"  Separator -> Hairstyle ID {next_id}: unlock_value = 0x{next_val:04X} ({next_val})")
    else:
        # Regular entry - might be class-specific data
        if id_val <= 12:  # Class IDs
            print(f"  Class ID {id_val}: value = 0x{val:04X} ({val})")
    
    offset += 4

print("\nKey findings:")
print("- Hairstyles 1-4 (Afro, Punk) have value 0x5A (90) in some contexts")
print("- Hairstyles 5-7, 9-10 have value 0x1E (30) - likely unlockable")
print("- Hairstyle 8 (Raiden F) has value 0x5A (90) - different from others")
print("- The value 0x1E (30) might represent 'needs to be unlocked'")
print("- The value 0x5A (90) might represent 'unlocked by default'")

# Create a summary document
with open(TABLE_SAMPLE_DIR + "/hairstyle_analysis.txt", 'w') as f:
    f.write("=" * 70 + "\n")
    f.write("HAIRSTYLE DATA ANALYSIS SUMMARY\n")
    f.write("=" * 70 + "\n\n")
    
    f.write("Hairstyles Found:\n")
    for h in hairstyles:
        f.write(f"  ID {h['id']}: {h['hair_name']} ({h['variant']}) at {h['offset']}\n")
    
    f.write("\nUnlock Table Analysis (0x18A70):\n")
    f.write("- Hairstyles 1-4: Value 0x5A (90) - default unlocked\n")
    f.write("- Hairstyles 5-7, 9-10: Value 0x1E (30) - unlockable\n")
    f.write("- Hairstyle 8: Value 0x5A (90) - default unlocked (special case)\n")
    
    f.write("\nHypothesis:\n")
    f.write("- To unlock all hairstyles, change 0x1E to 0x5A in the table\n")
    f.write("- Target offsets: 0x18AA4, 0x18AAC, 0x18AB4, 0x18AC4, 0x18ACC\n")
    f.write("- These correspond to hairstyle IDs 5, 6, 7, 9, 10\n")

print("\nCreated hairstyle_analysis.txt with summary")
