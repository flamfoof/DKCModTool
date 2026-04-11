"""Search for data patterns more robustly to extract all entries."""
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

print("=" * 70)
print("PATTERN SEARCH FOR HAIRSTYLE NAMES")
print("=" * 70)

data = read_stagebase()

# Search for pattern: 96 00 00 00 XX YY 68 00 [name]
# where XX is the ID byte and YY is the variant byte
hairstyles = []
offset = 0xBC00
while offset < 0xBE00:
    # Find the pattern marker
    pattern_pos = data.find(b'\x96\x00\x00\x00', offset)
    if pattern_pos < 0 or pattern_pos >= 0xBE00:
        break
    
    # Check if pattern is followed by 68 00
    if pattern_pos + 8 < len(data) and data[pattern_pos+6:pattern_pos+8] == b'\x68\x00':
        id_byte = data[pattern_pos + 4]
        variant_byte = data[pattern_pos + 5]
        name = read_string(data, pattern_pos + 8, 32)
        
        # Only include if name is alphabetic and reasonable length
        # Filter out job names (Monk, Acrobat, Hero, etc.)
        job_names = ["Monk", "Acrobat", "Hero", "Warrior", "Magician", "Thief", "Cleric", "Alchemist", "Ninja", "Spellsword", "Robo Knight", "Darkling"]
        if len(name) >= 3 and name.isalpha() and name not in job_names:
            variant = "M" if variant_byte % 2 == 0 else "F"
            hairstyles.append({
                "id": len(hairstyles) + 1,
                "hair_name": name,
                "variant": variant,
                "id_byte": id_byte,
                "variant_byte": variant_byte,
                "offset": f"0x{pattern_pos:X}"
            })
            print(f"Found: {name} ({variant}) - ID byte 0x{id_byte:02X}, variant 0x{variant_byte:02X} at 0x{pattern_pos:X}")
            offset = pattern_pos + len(name) + 8
        else:
            offset = pattern_pos + 1
    else:
        offset = pattern_pos + 1

print(f"\nTotal hairstyles found: {len(hairstyles)}")

# Update hair.csv
with open(TABLE_SAMPLE_DIR + "/hair.csv", 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["id", "hair_name", "variant"])
    for h in hairstyles:
        writer.writerow([h['id'], h['hair_name'], h['variant']])

print(f"Updated hair.csv with {len(hairstyles)} entries")

# Now clean up the weapon/shield data by removing entries with unreasonable HP values
print("\n" + "=" * 70)
print("CLEANING UP EQUIPMENT DATA")
print("=" * 70)

# Read current weapon.csv
weapons = []
with open(TABLE_SAMPLE_DIR + "/weapon.csv", 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        hp = int(row['hp'])
        # Remove entries with HP > 100 (false positives)
        if hp <= 100:
            weapons.append(row)
        else:
            print(f"Removing false positive: {row['weapon_name']} (HP={hp})")

# Write cleaned weapon.csv
with open(TABLE_SAMPLE_DIR + "/weapon.csv", 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["id", "weapon_name", "attack", "defense", "magic", "speed", "hp"])
    writer.writeheader()
    for w in weapons:
        writer.writerow(w)

print(f"Cleaned weapon.csv: {len(weapons)} entries (removed false positives)")

# Clean shield.csv
shields = []
with open(TABLE_SAMPLE_DIR + "/shield.csv", 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        hp = int(row['hp'])
        spd = int(row['speed'])
        # Remove entries with HP > 100 or SPD > 100 (false positives)
        if hp <= 100 and spd <= 100:
            shields.append(row)
        else:
            print(f"Removing false positive: {row['shield_name']} (HP={hp}, SPD={spd})")

# Write cleaned shield.csv
with open(TABLE_SAMPLE_DIR + "/shield.csv", 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["id", "shield_name", "attack", "defense", "magic", "speed", "hp"])
    writer.writeheader()
    for s in shields:
        writer.writerow(s)

print(f"Cleaned shield.csv: {len(shields)} entries (removed false positives)")

# Create comprehensive summary
print("\n" + "=" * 70)
print("DATA MAPPING SUMMARY")
print("=" * 70)

with open(TABLE_SAMPLE_DIR + "/mapping_summary.txt", 'w') as f:
    f.write("=" * 70 + "\n")
    f.write("COMPREHENSIVE DATA MAPPING SUMMARY\n")
    f.write("=" * 70 + "\n\n")
    
    f.write("HAIRSTYLE DATA\n")
    f.write("-" * 70 + "\n")
    f.write(f"Total hairstyles: {len(hairstyles)}\n")
    for h in hairstyles:
        f.write(f"  ID {h['id']}: {h['hair_name']} ({h['variant']})\n")
        f.write(f"    Offset: {h['offset']}, ID byte: 0x{h['id_byte']:02X}\n")
    
    f.write("\nHAIRSTYLE UNLOCK TABLE (0x18A70)\n")
    f.write("-" * 70 + "\n")
    f.write("Hairstyle IDs 5-7, 9-10: Value 0x1E (30) - UNLOCKABLE\n")
    f.write("Hairstyle ID 8: Value 0x5A (90) - UNLOCKED BY DEFAULT\n")
    f.write("\nTo unlock all hairstyles, patch these offsets in stageBase_EN.DAT:\n")
    f.write("  0x18AA4: Change 1E 00 to 5A 00 (Hairstyle 5)\n")
    f.write("  0x18AAC: Change 1E 00 to 5A 00 (Hairstyle 6)\n")
    f.write("  0x18AB4: Change 1E 00 to 5A 00 (Hairstyle 7)\n")
    f.write("  0x18AC4: Change 1E 00 to 5A 00 (Hairstyle 9)\n")
    f.write("  0x18ACC: Change 1E 00 to 5A 00 (Hairstyle 10)\n")
    
    f.write("\nWEAPON DATA\n")
    f.write("-" * 70 + "\n")
    f.write(f"Total weapons: {len(weapons)}\n")
    for w in weapons:
        f.write(f"  ID {w['id']}: {w['weapon_name']} - ATK={w['attack']}, DEF={w['defense']}, MAG={w['magic']}, SPD={w['speed']}, HP={w['hp']}\n")
    
    f.write("\nSHIELD DATA\n")
    f.write("-" * 70 + "\n")
    f.write(f"Total shields: {len(shields)}\n")
    for s in shields:
        f.write(f"  ID {s['id']}: {s['shield_name']} - ATK={s['attack']}, DEF={s['defense']}, MAG={s['magic']}, SPD={s['speed']}, HP={s['hp']}\n")

print("\nCreated mapping_summary.txt with comprehensive data")
print("\nData mapping complete!")
