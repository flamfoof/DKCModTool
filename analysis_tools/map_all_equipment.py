#!/usr/bin/env python3
"""
Comprehensive Equipment Memory Mapper for Dokapon Kingdom: Connect
==================================================================
Scans stageBase_EN.DAT and maps ALL weapons, shields, and accessories
with their exact memory offsets, stats, prices, effects, and metadata.

Outputs:
  - equipment_memory_map.json  (machine-readable full mapping)
  - Console report with verification against CSV reference data

Entry Structure (all equipment types):
  [8-byte header] [name string, null-terminated, padded to 4-byte alignment] [20-byte data block]

  Header (8 bytes):
    uint32 LE  marker        (0x58=weapon, 0x5E=shield, 0x64=accessory)
    uint8      item_id       (1-based sequential within type)
    uint8      reserved      (always 0)
    uint8      sub_type      (weapon class / shield=0x51 / accessory sub-type)
    uint8      reserved      (always 0)

  Data block (20 bytes):
    --- Weapons ---
    uint8      sub_rank          byte 0: internal ranking/tier
    uint8      preferred_job     byte 1: 0=None,1=Warrior,2=Magician,3=Thief,4=Cleric,5=Acrobat,6=Monk,7=Ninja,8=RoboKnight
    uint8      effect_chance     byte 2: activation % (0=none, 0x0C=12%, 0x19=25%, 0x32=50%, 0x64=100%)
    uint8      rarity_tier       byte 3: acquisition tier (0=common store, 1=uncommon store,
                                   2=rare store, 3=special/locked box, 4=rare drop, 5=ultimate)
    NOTE: The specific effect (Zapper, Sleep, etc.) is hardcoded per item ID in the game engine.
    --- Shields & Accessories ---
    uint8      effect_chance     byte 0: activation %
    uint8      rarity_tier       byte 1: acquisition tier (same scale as weapons)
    uint8      reserved          byte 2: always 0
    uint8      reserved          byte 3: always 0
    --- Common (bytes 4-19) ---
    uint32 LE  price             bytes 4-7
    int16  LE  stat0             bytes 8-9   (AT for weapons/accessories, DF for shields)
    int16  LE  stat1             bytes 10-11 (DF for weapons/accessories, AT for shields)
    int16  LE  magic             bytes 12-13
    int16  LE  speed             bytes 14-15
    int16  LE  hp                bytes 16-17 (stored as HP/10, so multiply by 10 for real value)
    uint8[2]   trail             bytes 18-19 (next-item / sort indices)

Weapon sub_type codes:
  0x4A=Sword/Blade, 0x4B=Axe, 0x4C=Wand/Staff, 0x4D=Hammer/Mace,
  0x4E=Spear/Lance, 0x4F=Fist/Knuckle, 0x50=Bow/Ranged

Shield sub_type: always 0x51

Accessory sub_type codes:
  0x52=Gloves, 0x53=Ring, 0x54=Bracelet, 0x55=Necklace/Choker,
  0x56=Footwear, 0x57=Bandana, 0x58=Badge, 0x59=Studs, 0x5A=Crown
"""

import struct
import json
import csv
import io
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DAT_PATH = os.path.join(ROOT_DIR, "Backup", "assets", "stageBase_EN.DAT")
CSV_DIR = os.path.join(SCRIPT_DIR, "table_sample")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "equipment_memory_map.json")

# Also generate a mod-ready JSON for the Equipment-Editor
MOD_JSON = os.path.join(ROOT_DIR, "Mods", "Equipment-Editor", "equipment.json")

MARKERS = {"weapon": 0x58, "shield": 0x5E, "accessory": 0x64}

JOB_NAMES = {
    0: "none", 1: "warrior", 2: "magician", 3: "thief", 4: "cleric",
    5: "acrobat", 6: "monk", 7: "ninja", 8: "robo_knight"
}

WEAPON_TYPES = {
    0x4A: "sword", 0x4B: "axe", 0x4C: "wand", 0x4D: "hammer",
    0x4E: "spear", 0x4F: "fist", 0x50: "bow"
}

ACCESSORY_TYPES = {
    0x52: "gloves", 0x53: "ring", 0x54: "bracelet", 0x55: "necklace",
    0x56: "footwear", 0x57: "bandana", 0x58: "badge", 0x59: "studs", 0x5A: "crown"
}


def load_dat():
    with open(DAT_PATH, "rb") as f:
        return bytearray(f.read())


def load_csv_reference(filename):
    """Load CSV reference data for verification.
    
    Handles broken multiline CSV rows where Price and Effect fields
    end up on a continuation line (e.g., shields and accessories CSVs).
    A continuation line is detected when its first comma-field is NOT
    a valid integer ID.
    """
    path = os.path.join(CSV_DIR, filename)
    if not os.path.exists(path):
        return {}

    # Pre-merge continuation lines
    with open(path, "r", encoding="utf-8-sig") as f:
        raw_lines = f.readlines()

    merged = [raw_lines[0]]  # header
    for line in raw_lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        first_field = stripped.split(",")[0].strip().strip('"')
        if first_field.isdigit():
            merged.append(line)
        else:
            # Continuation line — append to previous (comma-join)
            if merged:
                prev = merged[-1].rstrip("\n\r")
                merged[-1] = prev + "," + line
            else:
                merged.append(line)

    items = {}
    reader = csv.DictReader(io.StringIO("".join(merged)))
    for row in reader:
        name = (row.get("Name") or "").strip()
        if name:
            items[name] = row
    return items


def parse_price(price_str):
    """Parse price string like '2,000G' or '2G' to int."""
    if not price_str:
        return 0
    # Strip whitespace, unicode chars, extract digits before 'G'
    s = price_str.strip().rstrip('\u200b')
    # Find the price portion (digits and commas before 'G')
    import re
    m = re.search(r'([\d,]+)\s*G', s)
    if m:
        return int(m.group(1).replace(',', ''))
    # Fallback: try plain int
    try:
        return int(s.replace(',', '').replace('G', ''))
    except ValueError:
        return 0


def parse_stat(val):
    """Parse a stat string, handling empty and '*' values."""
    if not val or val.strip() == "":
        return 0, False
    val = val.strip()
    dynamic = "*" in val
    num_str = val.replace("*", "").strip()
    return (int(num_str) if num_str else 0), dynamic


def find_all_entries(data, marker, start_region, end_region):
    """Find all equipment entries with given marker in a region."""
    entries = []
    pos = start_region
    marker_bytes = struct.pack("<I", marker)

    while pos < end_region:
        idx = data.find(marker_bytes, pos, end_region)
        if idx < 0:
            break

        # Verify header structure: marker(4) + id(1) + 0(1) + type(1) + 0(1)
        if idx + 8 > len(data):
            pos = idx + 1
            continue

        item_id = data[idx + 4]
        reserved1 = data[idx + 5]
        sub_type = data[idx + 6]
        reserved2 = data[idx + 7]

        if reserved1 != 0 or reserved2 != 0:
            pos = idx + 1
            continue

        # Read name string after header
        name_start = idx + 8
        name_end = data.find(b"\x00", name_start, name_start + 64)
        if name_end < 0:
            pos = idx + 1
            continue

        name = data[name_start:name_end].decode("ascii", errors="replace")

        # Skip if name doesn't look valid (must have printable chars)
        if not name or not all(32 <= c < 127 for c in data[name_start:name_end]):
            pos = idx + 1
            continue

        # Calculate padded name length (aligned to 4 bytes)
        name_raw_len = name_end - name_start + 1  # include null
        name_padded = (name_raw_len + 3) & ~3

        # Data block offset
        data_off = name_start + name_padded

        if data_off + 20 > len(data):
            pos = idx + 1
            continue

        # Read 20-byte data block
        block = data[data_off:data_off + 20]
        meta = block[0:4]
        price = struct.unpack_from("<I", block, 4)[0]
        stats = struct.unpack_from("<5h", block, 8)
        trail = block[18:20]

        entry = {
            "name": name,
            "item_id": item_id,
            "sub_type": sub_type,
            "header_offset": idx,
            "name_offset": name_start,
            "data_offset": data_off,
            "name_max_len": name_padded - 1,  # max chars before null
            "meta": list(meta),
            "price": price,
            "raw_stats": list(stats),
            "trail": list(trail),
        }

        entries.append(entry)
        pos = idx + 4  # move past this marker

    # Sort by item_id
    entries.sort(key=lambda e: e["item_id"])
    return entries


def decode_weapon_entry(entry):
    """Decode weapon-specific fields."""
    meta = entry["meta"]
    s = entry["raw_stats"]
    return {
        "sub_rank": meta[0],
        "preferred_job": JOB_NAMES.get(meta[1], f"unknown_{meta[1]}"),
        "preferred_job_id": meta[1],
        "effect_chance": meta[2],
        "rarity_tier": meta[3],
        "attack": s[0],
        "defense": s[1],
        "magic": s[2],
        "speed": s[3],
        "hp": s[4] * 10,
        "hp_raw": s[4],
    }


def decode_shield_entry(entry):
    """Decode shield-specific fields (stats 0-1 are DF,AT swapped)."""
    meta = entry["meta"]
    s = entry["raw_stats"]
    return {
        "effect_chance": meta[0],
        "rarity_tier": meta[1],
        "attack": s[1],   # AT is in position 1 for shields
        "defense": s[0],  # DF is in position 0 for shields
        "magic": s[2],
        "speed": s[3],
        "hp": s[4] * 10,
        "hp_raw": s[4],
    }


def decode_accessory_entry(entry):
    """Decode accessory-specific fields."""
    meta = entry["meta"]
    s = entry["raw_stats"]
    return {
        "effect_chance": meta[0],
        "rarity_tier": meta[1],
        "attack": s[0],
        "defense": s[1],
        "magic": s[2],
        "speed": s[3],
        "hp": s[4] * 10,
        "hp_raw": s[4],
    }


def verify_against_csv(decoded, csv_ref, equip_type):
    """Verify decoded values against CSV reference data."""
    issues = []
    name = decoded.get("_name", "")
    if name not in csv_ref:
        return ["not in CSV"]

    ref = csv_ref[name]

    # Parse expected stats from CSV
    if equip_type == "weapon":
        exp_at, _ = parse_stat(ref.get("AT", ""))
        exp_df, _ = parse_stat(ref.get("DF", ""))
        exp_mg, _ = parse_stat(ref.get("MG", ""))
        exp_sp, _ = parse_stat(ref.get("SP", ""))
        exp_hp, _ = parse_stat(ref.get("HP", ""))
        exp_price = parse_price(ref.get("Price", "0"))
    else:
        exp_at, _ = parse_stat(ref.get("AT", ""))
        exp_df, _ = parse_stat(ref.get("DF", ""))
        exp_mg, _ = parse_stat(ref.get("MG", ""))
        exp_sp, _ = parse_stat(ref.get("SP", ""))
        exp_hp, _ = parse_stat(ref.get("HP", ""))
        exp_price = parse_price(ref.get("Price", "0"))

    # Check stats
    if decoded["attack"] != exp_at:
        issues.append(f"AT: {decoded['attack']} != CSV {exp_at}")
    if decoded["defense"] != exp_df:
        issues.append(f"DF: {decoded['defense']} != CSV {exp_df}")
    if decoded["magic"] != exp_mg:
        issues.append(f"MG: {decoded['magic']} != CSV {exp_mg}")
    if decoded["speed"] != exp_sp:
        issues.append(f"SP: {decoded['speed']} != CSV {exp_sp}")
    if decoded["hp"] != exp_hp:
        issues.append(f"HP: {decoded['hp']} != CSV {exp_hp}")
    if decoded.get("_price", 0) != exp_price:
        issues.append(f"Price: {decoded.get('_price', 0)} != CSV {exp_price}")

    return issues


def check_dynamic_stats(name, csv_ref):
    """Check if item has dynamic (asterisk) stats in CSV."""
    if name not in csv_ref:
        return False
    ref = csv_ref[name]
    for field in ["AT", "DF", "MG", "SP", "HP"]:
        val = ref.get(field, "")
        if "*" in str(val):
            return True
    return False


def get_csv_effect(name, csv_ref):
    """Get effect description from CSV."""
    if name not in csv_ref:
        return ""
    val = csv_ref[name].get("Effect", "") or ""
    return val.strip().rstrip("\u200b")


def get_csv_locations(name, csv_ref):
    """Get locations from CSV."""
    if name not in csv_ref:
        return ""
    val = csv_ref[name].get("Locations", "") or ""
    return val.strip()


def main():
    print("=" * 70)
    print("  Dokapon Kingdom: Connect — Equipment Memory Mapper")
    print("=" * 70)

    data = load_dat()
    print(f"Loaded {DAT_PATH} ({len(data)} bytes)")

    # Load CSV reference data
    weapons_csv = load_csv_reference("dokapon_weapons.csv")
    shields_csv = load_csv_reference("dokapon_shields.csv")
    accessories_csv = load_csv_reference("dokapon_accessories.csv")
    print(f"CSV refs: {len(weapons_csv)} weapons, {len(shields_csv)} shields, {len(accessories_csv)} accessories")

    # Scan regions
    print("\n--- Scanning Weapons (marker=0x58, region 0x07000-0x07C00) ---")
    weapon_entries = find_all_entries(data, 0x58, 0x07000, 0x07C00)
    print(f"Found {len(weapon_entries)} weapon entries")

    print("\n--- Scanning Shields (marker=0x5E, region 0x09800-0x09F80) ---")
    shield_entries = find_all_entries(data, 0x5E, 0x09800, 0x09F80)
    print(f"Found {len(shield_entries)} shield entries")

    print("\n--- Scanning Accessories (marker=0x64, region 0x0AA00-0x0B200) ---")
    acc_entries = find_all_entries(data, 0x64, 0x0AA00, 0x0B200)
    print(f"Found {len(acc_entries)} accessory entries")

    # Decode and verify
    full_map = {"weapons": [], "shields": [], "accessories": []}
    mod_config = {
        "_comment": "Equipment Editor — comprehensive configuration for stageBase_EN.DAT",
        "_notes": {
            "hp_storage": "HP values in DAT are stored as HP/10. Build script handles conversion.",
            "shield_stat_order": "Shields store DF in stat position 0 and AT in position 1 (swapped vs weapons).",
            "dynamic_stats": "Items with dynamic_stats=true have computed stats. DO NOT overwrite their stat values.",
            "effect_chance": "Activation percentage: 0=none, 12=12%, 25=25%, 33=33%, 50=50%, 100=always.",
            "rarity_tier": "Acquisition tier: 0=common store, 1=uncommon store, 2=rare store, 3=special (locked box/casino), 4=rare drop, 5=ultimate (darkling/hero).",
            "effects_note": "The specific effect each item triggers (Zapper, Sleep, etc.) is hardcoded per item ID in the game engine. Only effect_chance (activation %) is patchable.",
            "name_max_len": "Maximum name length (chars) before data block is corrupted. Shorter names are OK.",
            "offsets": "All offsets are hex addresses in stageBase_EN.DAT file."
        },
        "weapons": {},
        "shields": {},
        "accessories": {}
    }

    # Process weapons
    print("\n=== WEAPONS ===")
    print(f"{'ID':>3} {'Name':20} {'AT':>5} {'DF':>5} {'MG':>5} {'SP':>5} {'HP':>5} {'Price':>10} {'Eff%':>4} {'Job':12} {'Status'}")
    print("-" * 100)

    for entry in weapon_entries:
        decoded = decode_weapon_entry(entry)
        decoded["_name"] = entry["name"]
        decoded["_price"] = entry["price"]
        is_dynamic = check_dynamic_stats(entry["name"], weapons_csv)
        issues = verify_against_csv(decoded, weapons_csv, "weapon")
        effect_desc = get_csv_effect(entry["name"], weapons_csv)
        locations = get_csv_locations(entry["name"], weapons_csv)

        status = "DYNAMIC" if is_dynamic else ("OK" if not issues else f"WARN: {'; '.join(issues)}")
        print(f"{entry['item_id']:3} {entry['name']:20} {decoded['attack']:5} {decoded['defense']:5} "
              f"{decoded['magic']:5} {decoded['speed']:5} {decoded['hp']:5} {entry['price']:10} "
              f"{decoded['effect_chance']:4} {decoded['preferred_job']:12} {status}")

        # Build memory map entry
        map_entry = {
            "name": entry["name"],
            "item_id": entry["item_id"],
            "weapon_type": WEAPON_TYPES.get(entry["sub_type"], f"0x{entry['sub_type']:02X}"),
            "preferred_job": decoded["preferred_job"],
            "header_offset": f"0x{entry['header_offset']:05X}",
            "name_offset": f"0x{entry['name_offset']:05X}",
            "data_offset": f"0x{entry['data_offset']:05X}",
            "name_max_len": entry["name_max_len"],
            "price": entry["price"],
            "attack": decoded["attack"],
            "defense": decoded["defense"],
            "magic": decoded["magic"],
            "speed": decoded["speed"],
            "hp": decoded["hp"],
            "effect_chance": decoded["effect_chance"],
            "rarity_tier": decoded["rarity_tier"],
            "sub_rank": decoded["sub_rank"],
            "dynamic_stats": is_dynamic,
            "effect_description": effect_desc,
            "locations": locations,
        }
        full_map["weapons"].append(map_entry)

        # Build mod config entry
        mod_entry = {
            "attack": decoded["attack"],
            "defense": decoded["defense"],
            "magic": decoded["magic"],
            "speed": decoded["speed"],
            "hp": decoded["hp"],
            "price": entry["price"],
            "effect_chance": decoded["effect_chance"],
            "rarity_tier": decoded["rarity_tier"],
            "preferred_job": decoded["preferred_job"],
            "name_offset": f"0x{entry['name_offset']:05X}",
            "data_offset": f"0x{entry['data_offset']:05X}",
            "name_max_len": entry["name_max_len"],
            "effect_description": effect_desc,
            "locations": locations,
        }
        if is_dynamic:
            mod_entry["dynamic_stats"] = True
        mod_config["weapons"][entry["name"]] = mod_entry

    # Process shields
    print(f"\n=== SHIELDS ===")
    print(f"{'ID':>3} {'Name':20} {'AT':>5} {'DF':>5} {'MG':>5} {'SP':>5} {'HP':>5} {'Price':>10} {'Eff%':>4} {'Status'}")
    print("-" * 90)

    for entry in shield_entries:
        decoded = decode_shield_entry(entry)
        decoded["_name"] = entry["name"]
        decoded["_price"] = entry["price"]
        is_dynamic = check_dynamic_stats(entry["name"], shields_csv)
        issues = verify_against_csv(decoded, shields_csv, "shield")
        effect_desc = get_csv_effect(entry["name"], shields_csv)
        locations = get_csv_locations(entry["name"], shields_csv)

        status = "DYNAMIC" if is_dynamic else ("OK" if not issues else f"WARN: {'; '.join(issues)}")
        print(f"{entry['item_id']:3} {entry['name']:20} {decoded['attack']:5} {decoded['defense']:5} "
              f"{decoded['magic']:5} {decoded['speed']:5} {decoded['hp']:5} {entry['price']:10} "
              f"{decoded['effect_chance']:4} {status}")

        map_entry = {
            "name": entry["name"],
            "item_id": entry["item_id"],
            "header_offset": f"0x{entry['header_offset']:05X}",
            "name_offset": f"0x{entry['name_offset']:05X}",
            "data_offset": f"0x{entry['data_offset']:05X}",
            "name_max_len": entry["name_max_len"],
            "price": entry["price"],
            "attack": decoded["attack"],
            "defense": decoded["defense"],
            "magic": decoded["magic"],
            "speed": decoded["speed"],
            "hp": decoded["hp"],
            "effect_chance": decoded["effect_chance"],
            "rarity_tier": decoded["rarity_tier"],
            "dynamic_stats": is_dynamic,
            "effect_description": effect_desc,
            "locations": locations,
        }
        full_map["shields"].append(map_entry)

        mod_entry = {
            "attack": decoded["attack"],
            "defense": decoded["defense"],
            "magic": decoded["magic"],
            "speed": decoded["speed"],
            "hp": decoded["hp"],
            "price": entry["price"],
            "effect_chance": decoded["effect_chance"],
            "rarity_tier": decoded["rarity_tier"],
            "name_offset": f"0x{entry['name_offset']:05X}",
            "data_offset": f"0x{entry['data_offset']:05X}",
            "name_max_len": entry["name_max_len"],
            "effect_description": effect_desc,
            "locations": locations,
        }
        if is_dynamic:
            mod_entry["dynamic_stats"] = True
        mod_config["shields"][entry["name"]] = mod_entry

    # Process accessories
    print(f"\n=== ACCESSORIES ===")
    print(f"{'ID':>3} {'Name':20} {'AT':>5} {'DF':>5} {'MG':>5} {'SP':>5} {'HP':>5} {'Price':>10} {'Eff%':>4} {'Status'}")
    print("-" * 90)

    for entry in acc_entries:
        decoded = decode_accessory_entry(entry)
        decoded["_name"] = entry["name"]
        decoded["_price"] = entry["price"]
        is_dynamic = check_dynamic_stats(entry["name"], accessories_csv)
        issues = verify_against_csv(decoded, accessories_csv, "accessory")
        effect_desc = get_csv_effect(entry["name"], accessories_csv)
        locations = get_csv_locations(entry["name"], accessories_csv)

        status = "DYNAMIC" if is_dynamic else ("OK" if not issues else f"WARN: {'; '.join(issues)}")
        acc_type = ACCESSORY_TYPES.get(entry["sub_type"], f"0x{entry['sub_type']:02X}")
        print(f"{entry['item_id']:3} {entry['name']:20} {decoded['attack']:5} {decoded['defense']:5} "
              f"{decoded['magic']:5} {decoded['speed']:5} {decoded['hp']:5} {entry['price']:10} "
              f"{decoded['effect_chance']:4} {status}")

        map_entry = {
            "name": entry["name"],
            "item_id": entry["item_id"],
            "accessory_type": acc_type,
            "header_offset": f"0x{entry['header_offset']:05X}",
            "name_offset": f"0x{entry['name_offset']:05X}",
            "data_offset": f"0x{entry['data_offset']:05X}",
            "name_max_len": entry["name_max_len"],
            "price": entry["price"],
            "attack": decoded["attack"],
            "defense": decoded["defense"],
            "magic": decoded["magic"],
            "speed": decoded["speed"],
            "hp": decoded["hp"],
            "effect_chance": decoded["effect_chance"],
            "rarity_tier": decoded["rarity_tier"],
            "dynamic_stats": is_dynamic,
            "effect_description": effect_desc,
            "locations": locations,
        }
        full_map["accessories"].append(map_entry)

        mod_entry = {
            "attack": decoded["attack"],
            "defense": decoded["defense"],
            "magic": decoded["magic"],
            "speed": decoded["speed"],
            "hp": decoded["hp"],
            "price": entry["price"],
            "effect_chance": decoded["effect_chance"],
            "rarity_tier": decoded["rarity_tier"],
            "accessory_type": acc_type,
            "name_offset": f"0x{entry['name_offset']:05X}",
            "data_offset": f"0x{entry['data_offset']:05X}",
            "name_max_len": entry["name_max_len"],
            "effect_description": effect_desc,
            "locations": locations,
        }
        if is_dynamic:
            mod_entry["dynamic_stats"] = True
        mod_config["accessories"][entry["name"]] = mod_entry

    # Save outputs
    print(f"\n--- Saving memory map to {OUTPUT_JSON} ---")
    with open(OUTPUT_JSON, "w") as f:
        json.dump(full_map, f, indent=2)
    print(f"[OK] Saved {len(full_map['weapons'])} weapons, {len(full_map['shields'])} shields, "
          f"{len(full_map['accessories'])} accessories")

    print(f"\n--- Saving mod config to {MOD_JSON} ---")
    os.makedirs(os.path.dirname(MOD_JSON), exist_ok=True)
    with open(MOD_JSON, "w") as f:
        json.dump(mod_config, f, indent=2)
    print(f"[OK] Saved equipment.json for Equipment-Editor mod")

    # Summary
    total = len(full_map["weapons"]) + len(full_map["shields"]) + len(full_map["accessories"])
    print(f"\n{'='*70}")
    print(f"  Total: {total} equipment items mapped")
    print(f"  Weapons:     {len(full_map['weapons'])}")
    print(f"  Shields:     {len(full_map['shields'])}")
    print(f"  Accessories: {len(full_map['accessories'])}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
