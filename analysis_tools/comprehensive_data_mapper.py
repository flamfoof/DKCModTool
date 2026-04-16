"""Comprehensive data mapper to expand table_sample with full stats and discover missing items."""
import struct
import csv
import os

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"
TABLE_SAMPLE_DIR = r"table_sample"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def read_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

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
print("COMPREHENSIVE DATA MAPPING")
print("=" * 70)

data = read_stagebase()

# =============================================================================
# EXPAND HAIRSTYLE DATA
# =============================================================================
print("\n" + "=" * 70)
print("EXPANDING HAIRSTYLE DATA")
print("=" * 70)

# From analysis, hairstyle names are at 0xBCD0 area
# Pattern: 96 00 00 00 ID 04 68 00 NAME
# Let's extract all hairstyles systematically

hairstyles = []
offset = 0xBCD0
while offset < 0xBE00:
    # Find the pattern marker
    pattern_pos = data.find(b'\x96\x00\x00\x00', offset)
    if pattern_pos < 0 or pattern_pos >= 0xBE00:
        break
    
    # Check for name after 68 00 (4 bytes after pattern)
    name_pos = pattern_pos + 8
    if name_pos + 4 < len(data) and data[name_pos:name_pos+2] == b'\x68\x00':
        id_byte = data[pattern_pos + 4]
        variant_byte = data[pattern_pos + 5]
        name = read_string(data, name_pos + 2, 32)
        
        # Map variant byte to M/F
        variant = "M" if variant_byte == 0x04 else "F" if variant_byte == 0x05 else "?"
        
        hairstyles.append({
            "id": len(hairstyles) + 1,
            "hair_name": name,
            "variant": variant,
            "id_byte": id_byte,
            "offset": f"0x{pattern_pos:X}"
        })
        
        offset = name_pos + len(name) + 1
    else:
        offset = pattern_pos + 1

print(f"\nFound {len(hairstyles)} hairstyles:")
for h in hairstyles:
    print(f"  ID {h['id']}: {h['hair_name']} ({h['variant']}) - byte 0x{h['id_byte']:02X} at {h['offset']}")

# Update hair.csv
with open(os.path.join(TABLE_SAMPLE_DIR, "hair.csv"), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["id", "hair_name", "variant"])
    for h in hairstyles:
        writer.writerow([h['id'], h['hair_name'], h['variant']])

print(f"\nUpdated hair.csv with {len(hairstyles)} entries")

# =============================================================================
# ANALYZE HAIRSTYLE TABLE AT 0x18A70 FOR UNLOCK DATA
# =============================================================================
print("\n" + "=" * 70)
print("HAIRSTYLE TABLE ANALYSIS (0x18A70)")
print("=" * 70)

# The table has [id, value] pairs
# IDs 5-10 have value 0x1E (30) except ID 8 which has 0x5A (90)
# This might be unlock flags or availability codes

print("\nHairstyle table entries:")
hairstyle_table = []
offset = 0x18A70
for i in range(24):
    id_val = read_uint16(data, offset)
    val = read_uint16(data, offset + 2)
    hairstyle_table.append({"id": id_val, "value": val, "offset": offset})
    print(f"  0x{offset:X}: ID={id_val}, Value=0x{val:04X} ({val})")
    offset += 4

# Look for the pattern: FF FF 00 00 XX YY where XX is hairstyle ID
print("\nHairstyle availability/unlock entries:")
unlock_entries = []
for i, entry in enumerate(hairstyle_table):
    if entry['id'] == 0xFFFF:  # Separator
        if i + 1 < len(hairstyle_table):
            next_entry = hairstyle_table[i + 1]
            if 1 <= next_entry['id'] <= 15:
                print(f"  Hairstyle ID {next_entry['id']}: value = 0x{next_entry['value']:04X} ({next_entry['value']})")
                unlock_entries.append(next_entry)

# =============================================================================
# EXPAND WEAPON DATA WITH ALL STATS
# =============================================================================
print("\n" + "=" * 70)
print("SEARCHING FOR WEAPON STAT STRUCTURES")
print("=" * 70)

# Weapons are in region 0x7000-0x9800
# Stats pattern: [att, def, mag, spd, hp] as uint16 LE (10 bytes)
# Need to find names nearby

weapons = []
# Search for known weapon names first
weapon_names = ["Knife", "Dagger", "Longsword", "Hand Axe", "Rapier", "Spear",
               "Longbow", "Crossbow", "Battle Axe", "Mace", "Flail", "Halberd",
               "Katana", "Nunchaku", "Kusarigama", "Shuriken", "Kunai"]

for name in weapon_names:
    name_bytes = name.encode('ascii')
    offset = 0x7000
    while offset < 0x9800:
        offset = data.find(name_bytes, offset)
        if offset < 0 or offset >= 0x9800:
            break
        
        # Search for stat pattern nearby (within 64 bytes)
        found_stats = False
        for stat_offset in range(offset - 64, offset + 32, 2):
            if stat_offset + 10 <= len(data):
                att = read_uint16(data, stat_offset)
                def_ = read_uint16(data, stat_offset + 2)
                mag = read_uint16(data, stat_offset + 4)
                spd = read_uint16(data, stat_offset + 6)
                hp = read_uint16(data, stat_offset + 8)
                
                # Filter for reasonable weapon stats
                if 1 <= att <= 50 and 0 <= def_ <= 15 and 0 <= mag <= 15 and 0 <= spd <= 15 and 0 <= hp <= 15:
                    # Check if this is a new weapon (not already found)
                    if not any(w['weapon_name'] == name for w in weapons):
                        weapons.append({
                            "id": len(weapons) + 1,
                            "weapon_name": name,
                            "attack": att,
                            "defense": def_,
                            "magic": mag,
                            "speed": spd,
                            "hp": hp,
                            "name_offset": offset,
                            "stats_offset": stat_offset
                        })
                        found_stats = True
                        print(f"  Found '{name}' at 0x{offset:X} (stats at 0x{stat_offset:X}): ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp}")
                        break
        
        if found_stats:
            break
        offset += len(name_bytes)

# Also try to find weapons by stat patterns directly
print("\nSearching for additional weapons by stat patterns...")
for offset in range(0x7000, 0x9800, 2):
    if offset + 10 > len(data):
        break
    att = read_uint16(data, offset)
    def_ = read_uint16(data, offset + 2)
    mag = read_uint16(data, offset + 4)
    spd = read_uint16(data, offset + 6)
    hp = read_uint16(data, offset + 8)
    
    # Weapon stat pattern: high ATK, low others
    if 5 <= att <= 50 and 0 <= def_ <= 15 and 0 <= mag <= 15 and 0 <= spd <= 15:
        # Check if there's a name nearby
        for name_offset in range(offset - 64, offset + 16):
            if 0x7000 <= name_offset < 0x9800:
                s = read_string(data, name_offset, 32)
                if len(s) >= 3 and s.isalpha() and s[0].isupper():
                    # Check if we already have this weapon
                    if not any(w['weapon_name'] == s for w in weapons):
                        weapons.append({
                            "id": len(weapons) + 1,
                            "weapon_name": s,
                            "attack": att,
                            "defense": def_,
                            "magic": mag,
                            "speed": spd,
                            "hp": hp,
                            "name_offset": name_offset,
                            "stats_offset": offset
                        })
                        print(f"  Found '{s}' at 0x{name_offset:X} (stats at 0x{offset:X}): ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp}")
                    break

# Update weapon.csv with all stats
with open(os.path.join(TABLE_SAMPLE_DIR, "weapon.csv"), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["id", "weapon_name", "attack", "defense", "magic", "speed", "hp"])
    for w in sorted(weapons, key=lambda x: x['id']):
        writer.writerow([w['id'], w['weapon_name'], w['attack'], w['defense'], 
                       w['magic'], w['speed'], w['hp']])

print(f"\nUpdated weapon.csv with {len(weapons)} entries")

# =============================================================================
# EXPAND SHIELD DATA WITH ALL STATS
# =============================================================================
print("\n" + "=" * 70)
print("SEARCHING FOR SHIELD STAT STRUCTURES")
print("=" * 70)

shields = []
shield_names = ["Wooden Shield", "Leather Shield", "Buckler", "Bronze Shield", "Lead Shield",
                "Wabbit Shield", "Iron Shield", "Steel Shield", "Mirror Shield", "Aegis"]

for name in shield_names:
    name_bytes = name.encode('ascii')
    offset = 0xA000
    while offset < 0xB000:
        offset = data.find(name_bytes, offset)
        if offset < 0 or offset >= 0xB000:
            break
        
        # Search for stat pattern nearby
        for stat_offset in range(offset - 64, offset + 32, 2):
            if stat_offset + 10 <= len(data):
                att = read_uint16(data, stat_offset)
                def_ = read_uint16(data, stat_offset + 2)
                mag = read_uint16(data, stat_offset + 4)
                spd = read_uint16(data, stat_offset + 6)
                hp = read_uint16(data, stat_offset + 8)
                
                # Shield stat pattern: high DEF, low ATK
                if 0 <= att <= 10 and 5 <= def_ <= 50 and 0 <= mag <= 20 and 0 <= spd <= 15 and 0 <= hp <= 15:
                    if not any(s['shield_name'] == name for s in shields):
                        shields.append({
                            "id": len(shields) + 1,
                            "shield_name": name,
                            "attack": att,
                            "defense": def_,
                            "magic": mag,
                            "speed": spd,
                            "hp": hp,
                            "name_offset": offset,
                            "stats_offset": stat_offset
                        })
                        print(f"  Found '{name}': ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp}")
                    break
        offset += len(name_bytes)

# Also search by stat patterns
print("\nSearching for additional shields by stat patterns...")
for offset in range(0xA000, 0xB000, 2):
    if offset + 10 > len(data):
        break
    att = read_uint16(data, offset)
    def_ = read_uint16(data, offset + 2)
    mag = read_uint16(data, offset + 4)
    spd = read_uint16(data, offset + 6)
    hp = read_uint16(data, offset + 8)
    
    # Shield stat pattern
    if 0 <= att <= 15 and 3 <= def_ <= 50 and 0 <= mag <= 20:
        for name_offset in range(offset - 64, offset + 16):
            if 0xA000 <= name_offset < 0xB000:
                s = read_string(data, name_offset, 32)
                if len(s) >= 3 and s.isalpha() and s[0].isupper():
                    if not any(sh['shield_name'] == s for sh in shields):
                        shields.append({
                            "id": len(shields) + 1,
                            "shield_name": s,
                            "attack": att,
                            "defense": def_,
                            "magic": mag,
                            "speed": spd,
                            "hp": hp,
                            "name_offset": name_offset,
                            "stats_offset": offset
                        })
                        print(f"  Found '{s}': ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp}")
                    break

# Update shield.csv with all stats
with open(os.path.join(TABLE_SAMPLE_DIR, "shield.csv"), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["id", "shield_name", "attack", "defense", "magic", "speed", "hp"])
    for s in sorted(shields, key=lambda x: x['id']):
        writer.writerow([s['id'], s['shield_name'], s['attack'], s['defense'],
                       s['magic'], s['speed'], s['hp']])

print(f"\nUpdated shield.csv with {len(shields)} entries")

# =============================================================================
# EXPAND ACCESSORY DATA
# =============================================================================
print("\n" + "=" * 70)
print("SEARCHING FOR ACCESSORY DATA")
print("=" * 70)

accessories = []
accessory_names = ["Power Gloves", "Spirit Gloves", "Speed Gloves", "Warm Gloves",
                   "Power Ring", "Spirit Ring", "Speed Ring", "Warm Ring",
                   "Angel Wings", "Demon Wings", "Hero Badge", "Dark Badge"]

# Search across entire file for accessories
for name in accessory_names:
    name_bytes = name.encode('ascii')
    offset = data.find(name_bytes)
    if offset >= 0:
        # Search for stat pattern nearby
        for stat_offset in range(offset - 64, offset + 32, 2):
            if stat_offset + 10 <= len(data):
                att = read_uint16(data, stat_offset)
                def_ = read_uint16(data, stat_offset + 2)
                mag = read_uint16(data, stat_offset + 4)
                spd = read_uint16(data, stat_offset + 6)
                hp = read_uint16(data, stat_offset + 8)
                
                # Accessory stat pattern: moderate stats
                if 0 < att <= 30 and 0 <= def_ <= 30 and 0 <= mag <= 30 and 0 <= spd <= 30 and 0 <= hp <= 30:
                    if not any(a['accessory_name'] == name for a in accessories):
                        accessories.append({
                            "id": len(accessories) + 1,
                            "accessory_name": name,
                            "attack": att,
                            "defense": def_,
                            "magic": mag,
                            "speed": spd,
                            "hp": hp,
                            "offset": offset,
                            "stats_offset": stat_offset
                        })
                        print(f"  Found '{name}': ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp}")
                    break

# Update accessory.csv
with open(os.path.join(TABLE_SAMPLE_DIR, "accessory.csv"), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["id", "accessory_name", "attack", "defense", "magic", "speed", "hp"])
    for a in sorted(accessories, key=lambda x: x['id']):
        writer.writerow([a['id'], a['accessory_name'], a['attack'], a['defense'],
                       a['magic'], a['speed'], a['hp']])

print(f"\nUpdated accessory.csv with {len(accessories)} entries")

# =============================================================================
# CREATE DATA STRUCTURE DOCUMENTATION
# =============================================================================
print("\n" + "=" * 70)
print("DATA STRUCTURE DOCUMENTATION")
print("=" * 70)

with open(os.path.join(TABLE_SAMPLE_DIR, "data_structures.txt"), 'w') as f:
    f.write("=" * 70 + "\n")
    f.write("DATA STRUCTURE DOCUMENTATION\n")
    f.write("=" * 70 + "\n\n")
    
    f.write("HAIRSTYLE DATA STRUCTURE\n")
    f.write("-" * 70 + "\n")
    f.write("Name Table: 0xBCD0\n")
    f.write("Pattern: 96 00 00 00 ID 04 68 00 NAME\n")
    f.write("ID byte values: 0x18=24 (Afro M), 0x19=25 (Afro F), 0x1A=26 (Punk M), etc.\n")
    f.write("Variant: 0x04=M, 0x05=F\n\n")
    
    f.write("Hairstyle Table: 0x18A70\n")
    f.write("Pattern: [ID, value] pairs (4 bytes each)\n")
    f.write("FF FF 00 00 = separator\n")
    f.write("IDs 5-10 have value 0x1E (30) except ID 8 has 0x5A (90)\n")
    f.write("This likely represents unlock/availability status\n\n")
    
    f.write("WEAPON DATA STRUCTURE\n")
    f.write("-" * 70 + "\n")
    f.write("Region: 0x7000-0x9800\n")
    f.write("Stats: [att, def, mag, spd, hp] as uint16 LE (10 bytes)\n")
    f.write(f"Found {len(weapons)} weapons\n\n")
    
    f.write("SHIELD DATA STRUCTURE\n")
    f.write("-" * 70 + "\n")
    f.write("Region: 0xA000-0xB000\n")
    f.write("Stats: [att, def, mag, spd, hp] as uint16 LE (10 bytes)\n")
    f.write(f"Found {len(shields)} shields\n\n")
    
    f.write("ACCESSORY DATA STRUCTURE\n")
    f.write("-" * 70 + "\n")
    f.write("Scattered throughout file\n")
    f.write("Stats: [att, def, mag, spd, hp] as uint16 LE (10 bytes)\n")
    f.write(f"Found {len(accessories)} accessories\n")

print("\n" + "=" * 70)
print("MAPPING COMPLETE")
print("=" * 70)
print(f"\nUpdated files:")
print(f"  - hair.csv: {len(hairstyles)} entries")
print(f"  - weapon.csv: {len(weapons)} entries")
print(f"  - shield.csv: {len(shields)} entries")
print(f"  - accessory.csv: {len(accessories)} entries")
print(f"  - data_structures.txt: Documentation")
