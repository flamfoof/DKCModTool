"""Map out weapon, shield, and accessory data with full stats."""
import struct
import csv
import os

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"
OUTPUT_DIR = r"table_sample"

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

# =============================================================================
# WEAPON DATA ANALYSIS
# =============================================================================

def analyze_weapons(data):
    print("=" * 70)
    print("WEAPON DATA ANALYSIS")
    print("=" * 70)
    
    # From data_tables.py: WEAPON_TABLE_REGION_START = 0x7000, WEAPON_TABLE_REGION_END = 0x9800
    # Let's search for weapon name patterns and stat structures
    
    # Known weapon names to search for
    weapon_names = [
        "Knife", "Dagger", "Longsword", "Hand Axe", "Rapier", "Spear",
        "Longbow", "Crossbow", "Battle Axe", "Mace", "Flail", "Halberd",
        "Katana", "Nunchaku", "Kusarigama", "Shuriken", "Kunai",
        "Dragon Guandao", "Ichimonji Katana", "Nihilist Sword"
    ]
    
    weapon_entries = []
    
    # Search for weapon names in the weapon region
    for name in weapon_names:
        name_bytes = name.encode('ascii')
        offset = 0x7000
        while offset < 0x9800:
            offset = data.find(name_bytes, offset)
            if offset < 0 or offset >= 0x9800:
                break
            print(f"\nFound '{name}' at 0x{offset:X}:")
            print(hexdump(data, max(0, offset-16), 64))
            
            # Look for stats pattern around the name
            # Stats likely: [att, def, mag, spd, hp] as uint16 LE (10 bytes)
            for stat_offset in range(offset - 32, offset + 32):
                if stat_offset + 10 <= len(data):
                    att = read_uint16(data, stat_offset)
                    def_ = read_uint16(data, stat_offset + 2)
                    mag = read_uint16(data, stat_offset + 4)
                    spd = read_uint16(data, stat_offset + 6)
                    hp = read_uint16(data, stat_offset + 8)
                    # Filter for reasonable stat values
                    if 0 < att < 100 and 0 <= def_ < 50 and 0 <= mag < 50:
                        print(f"  Possible stats at 0x{stat_offset:X}: ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp}")
                        weapon_entries.append({
                            "name": name,
                            "name_offset": offset,
                            "stats_offset": stat_offset,
                            "attack": att,
                            "defense": def_,
                            "magic": mag,
                            "speed": spd,
                            "hp": hp
                        })
            offset += len(name_bytes)
    
    # Also search for stat patterns directly
    print("\n" + "=" * 70)
    print("SEARCHING FOR STAT PATTERNS IN WEAPON REGION")
    print("=" * 70)
    
    for offset in range(0x7000, 0x9800, 2):
        if offset + 10 > len(data):
            break
        att = read_uint16(data, offset)
        def_ = read_uint16(data, offset + 2)
        mag = read_uint16(data, offset + 4)
        spd = read_uint16(data, offset + 6)
        hp = read_uint16(data, offset + 8)
        # Look for reasonable weapon stat patterns
        if 1 <= att <= 50 and 0 <= def_ <= 20 and 0 <= mag <= 20 and 0 <= spd <= 20 and 0 <= hp <= 20:
            # Check if there's a name nearby
            for name_offset in range(offset - 64, offset + 16):
                if 0x7000 <= name_offset < 0x9800:
                    s = read_string(data, name_offset, 32)
                    if len(s) >= 3 and s.isalpha():
                        print(f"  0x{offset:X}: ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp} (name: '{s}' at 0x{name_offset:X})")
                        break
    
    return weapon_entries

# =============================================================================
# SHIELD DATA ANALYSIS
# =============================================================================

def analyze_shields(data):
    print("\n" + "=" * 70)
    print("SHIELD DATA ANALYSIS")
    print("=" * 70)
    
    # From data_tables.py: SHIELD_TABLE_REGION_START = 0xA000, SHIELD_TABLE_REGION_END = 0xB000
    # Known: Wabbit Shield stats at 0xAC10
    
    shield_names = [
        "Wooden Shield", "Leather Shield", "Buckler", "Bronze Shield", "Lead Shield",
        "Wabbit Shield", "Iron Shield", "Steel Shield", "Mirror Shield", "Aegis"
    ]
    
    shield_entries = []
    
    # Check known location first
    print("\nKnown Wabbit Shield location (0xAC10):")
    print(hexdump(data, 0xAC00, 64))
    
    for offset in range(0xAC00, 0xAC10):
        att = read_uint16(data, offset)
        def_ = read_uint16(data, offset + 2)
        mag = read_uint16(data, offset + 4)
        spd = read_uint16(data, offset + 6)
        hp = read_uint16(data, offset + 8)
        print(f"  0x{offset:X}: ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp}")
    
    # Search for shield names
    for name in shield_names:
        name_bytes = name.encode('ascii')
        offset = 0xA000
        while offset < 0xB000:
            offset = data.find(name_bytes, offset)
            if offset < 0 or offset >= 0xB000:
                break
            print(f"\nFound '{name}' at 0x{offset:X}:")
            print(hexdump(data, max(0, offset-16), 64))
            offset += len(name_bytes)
    
    # Search for stat patterns
    print("\n" + "=" * 70)
    print("SEARCHING FOR STAT PATTERNS IN SHIELD REGION")
    print("=" * 70)
    
    for offset in range(0xA000, 0xB000, 2):
        if offset + 10 > len(data):
            break
        att = read_uint16(data, offset)
        def_ = read_uint16(data, offset + 2)
        mag = read_uint16(data, offset + 4)
        spd = read_uint16(data, offset + 6)
        hp = read_uint16(data, offset + 8)
        # Shields typically have high DEF, low ATK
        if 0 <= att <= 10 and 1 <= def_ <= 30 and 0 <= mag <= 10 and 0 <= spd <= 10 and 0 <= hp <= 10:
            for name_offset in range(offset - 64, offset + 16):
                if 0xA000 <= name_offset < 0xB000:
                    s = read_string(data, name_offset, 32)
                    if len(s) >= 3 and s.isalpha():
                        print(f"  0x{offset:X}: ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp} (name: '{s}' at 0x{name_offset:X})")
                        break
    
    return shield_entries

# =============================================================================
# ACCESSORY DATA ANALYSIS
# =============================================================================

def analyze_accessories(data):
    print("\n" + "=" * 70)
    print("ACCESSORY DATA ANALYSIS")
    print("=" * 70)
    
    # Accessories might be in a different region
    # Let's search for known accessory names
    accessory_names = [
        "Power Gloves", "Spirit Gloves", "Speed Gloves", "Warm Gloves",
        "Power Ring", "Spirit Ring", "Speed Ring", "Warm Ring",
        "Angel Wings", "Demon Wings", "Hero Badge", "Dark Badge"
    ]
    
    # Search across the whole file for these names
    for name in accessory_names:
        name_bytes = name.encode('ascii')
        offset = data.find(name_bytes)
        if offset >= 0:
            print(f"\nFound '{name}' at 0x{offset:X}:")
            print(hexdump(data, max(0, offset-32), 96))
            
            # Look for nearby stats
            for stat_offset in range(offset - 32, offset + 32):
                if stat_offset + 10 <= len(data):
                    att = read_uint16(data, stat_offset)
                    def_ = read_uint16(data, stat_offset + 2)
                    mag = read_uint16(data, stat_offset + 4)
                    spd = read_uint16(data, stat_offset + 6)
                    hp = read_uint16(data, stat_offset + 8)
                    if 0 < att < 50 or 0 < def_ < 50 or 0 < mag < 50:
                        print(f"  Possible stats at 0x{stat_offset:X}: ATK={att}, DEF={def_}, MAG={mag}, SPD={spd}, HP={hp}")

# =============================================================================
# HAIRSTYLE DATA ANALYSIS
# =============================================================================

def analyze_hairstyles(data):
    print("\n" + "=" * 70)
    print("HAIRSTYLE DATA ANALYSIS")
    print("=" * 70)
    
    # Search for hairstyle-related strings
    hair_keywords = [
        "Afro", "Punk", "Horror", "Hair", "hairstyle", "Hairstyle"
    ]
    
    for keyword in hair_keywords:
        name_bytes = keyword.encode('ascii')
        offset = 0
        count = 0
        while offset < len(data):
            offset = data.find(name_bytes, offset)
            if offset < 0:
                break
            if count < 5:
                print(f"\nFound '{keyword}' at 0x{offset:X}:")
                print(hexdump(data, max(0, offset-16), 64))
            count += 1
            offset += len(name_bytes)
        
        print(f"Total '{keyword}' occurrences: {count}")
    
    # Look for the hair data region from table_sample
    # IDs 1-8, with names and variants
    print("\n" + "=" * 70)
    print("SEARCHING FOR HAIRSTYLE TABLE STRUCTURE")
    print("=" * 70)
    
    # Look for patterns that might represent hairstyle data
    # Could be: [id, name_ptr, variant, unlock_flag, ...]
    
    # Search for sequences of small integers (IDs) followed by name pointers
    for offset in range(0, min(0x20000, len(data) - 100)):
        # Look for ID sequence: 1, 2, 3, 4, 5, 6, 7, 8
        if (data[offset] == 1 and data[offset+4] == 2 and 
            data[offset+8] == 3 and data[offset+12] == 4):
            print(f"\nPossible ID sequence at 0x{offset:X}:")
            print(hexdump(data, offset, 80))

if __name__ == "__main__":
    data = read_stagebase()
    
    weapons = analyze_weapons(data)
    shields = analyze_shields(data)
    analyze_accessories(data)
    analyze_hairstyles(data)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
