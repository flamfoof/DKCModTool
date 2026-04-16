#!/usr/bin/env python3
"""
Class Stats Memory Mapper for Dokapon Kingdom: Connect
=======================================================
Scans stageBase_EN.DAT and DkkStm.exe to map ALL class-related data:
  - Level-up stat gains per class (M/F variants)
  - Battle requirements per level
  - Bag/inventory capacity
  - Assignable points EXE patch location

Outputs:
  - class_stats_memory_map.json  (machine-readable full mapping)
  - Console report

Data Structures in stageBase_EN.DAT:
=====================================

Level-Up Entries (offset 0x1733E, 28 bytes each, 24 entries = 12 classes x 2 variants):
  bytes 0-1:  int16 LE  attack gain per level
  bytes 2-3:  int16 LE  defense gain per level
  bytes 4-5:  int16 LE  magic gain per level
  bytes 6-7:  int16 LE  speed gain per level
  bytes 8-9:  int16 LE  hp gain per level
  bytes 10-27: 18 bytes of additional data (unknown flags, marker 0x3B at byte 22, class/variant IDs)

Bag Capacity Entries (offset 0x175D8, 8 bytes each, 22 entries = 11 classes x 2 variants):
  bytes 0-3:  uint32 LE marker (0x44 = 68)
  byte  4:    uint8     class_id (0-based)
  byte  5:    uint8     variant (0=male, 1=female)
  byte  6:    uint8     item_slots
  byte  7:    uint8     magic_slots
  Note: Classes 0-10 (warrior through hero). Darkling (11) has no bag entry.

Battle Requirement Entries (offset 0x1768C, 8 bytes each):
  byte  0:    uint8     class_id
  byte  1:    uint8     variant (0=male, 1=female)
  byte  2:    uint8     battles_per_level
  byte  3:    uint8     padding (0)
  bytes 4-7:  uint32 LE marker (0x3E = 62)
  Note: Includes classes 0-11 (warrior through darkling), M/F variants.

Assignable Points in DkkStm.exe:
=================================
  File offset: 0x18CABF (15 bytes)
  Original code: sub r14d,edx; add r9d,r14d; mov eax,edi; cmp r9d,edi; cmovl eax,r9d
  
  The game computes assignable points via: min(edi, r9d)
  - [rbx+0xC4] = levels_gained (L) before the function runs
  - edi = L * 2 after doubling at 0x18C782
  - Result stored to [rbx+0xC4] at 0x18CACE
  
  To override with N points per level:
    mov eax, edi (8B C7)        2 bytes
    shr eax, 1  (C1 E8 01)     3 bytes   -> eax = levels_gained
    imul eax, eax, N            3 bytes (6B C0 NN for N<=127) or 6 bytes (69 C0 NN NN NN NN)
    nop padding                 7 or 4 bytes
  Total: 15 bytes
  
  Vanilla value: 2 points per level.
  
  DO NOT PATCH:
    [rbx+0xC8] at 0x18CADA  — UI layout value (cursor offset)
    [rbx+0xA8] at 0x18CAE5  — UI layout value
    [rbx+0x98] at 0x18CB04  — state machine value (changing freezes game)
"""

import struct
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DAT_PATH = os.path.join(ROOT_DIR, "Backup", "assets", "stageBase_EN.DAT")
EXE_PATH = os.path.join(ROOT_DIR, "Backup", "DkkStm.exe")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "class_stats_memory_map.json")

# Table offsets in stageBase_EN.DAT
LEVELUP_OFFSET = 0x1733E
LEVELUP_ENTRY_SIZE = 28
LEVELUP_ENTRY_COUNT = 24  # 12 classes x 2 variants (M/F)

BAG_OFFSET = 0x175D8
BAG_ENTRY_SIZE = 8
BAG_ENTRY_COUNT = 22  # 11 classes x 2 variants (no Darkling)

BATTLE_REQ_OFFSET = 0x1768C
BATTLE_REQ_ENTRY_SIZE = 8

# EXE patch locations
EXE_COMP_OFFSET = 0x18CABF
EXE_COMP_SIZE = 15
EXE_STORE_OFFSET = 0x18CACE  # mov [rbx+0xC4], eax (store result)
VANILLA_ASSIGNABLE = 2

CLASS_ORDER = [
    "warrior", "magician", "thief", "cleric", "spellsword", "alchemist",
    "ninja", "monk", "acrobat", "robo_knight", "hero", "darkling"
]

CLASS_DISPLAY = {
    "warrior": "Warrior", "magician": "Magician", "thief": "Thief",
    "cleric": "Cleric", "spellsword": "Spellsword", "alchemist": "Alchemist",
    "ninja": "Ninja", "monk": "Monk", "acrobat": "Acrobat",
    "robo_knight": "Robo Knight", "hero": "Hero", "darkling": "Darkling"
}


def load_file(path):
    with open(path, "rb") as f:
        return bytearray(f.read())


def scan_levelup_entries(data):
    """Scan all level-up stat entries."""
    entries = []
    for i in range(LEVELUP_ENTRY_COUNT):
        offset = LEVELUP_OFFSET + i * LEVELUP_ENTRY_SIZE
        raw = data[offset:offset + LEVELUP_ENTRY_SIZE]

        stats = struct.unpack_from("<5h", raw, 0)
        rest = raw[10:]

        class_idx = i // 2
        variant = i % 2  # 0=male, 1=female
        class_name = CLASS_ORDER[class_idx] if class_idx < len(CLASS_ORDER) else f"class_{class_idx}"

        entry = {
            "class": class_name,
            "class_index": class_idx,
            "variant": "male" if variant == 0 else "female",
            "variant_index": variant,
            "entry_index": i,
            "offset": f"0x{offset:05X}",
            "offset_int": offset,
            "attack": stats[0],
            "defense": stats[1],
            "magic": stats[2],
            "speed": stats[3],
            "hp": stats[4],
            "total_fixed": sum(stats),
            "rest_bytes": " ".join(f"{b:02X}" for b in rest),
        }
        entries.append(entry)
    return entries


def scan_bag_entries(data):
    """Scan all bag/inventory capacity entries."""
    entries = []
    for i in range(BAG_ENTRY_COUNT):
        offset = BAG_OFFSET + i * BAG_ENTRY_SIZE
        raw = data[offset:offset + BAG_ENTRY_SIZE]

        marker = struct.unpack_from("<I", raw, 0)[0]
        class_id = raw[4]
        variant = raw[5]
        item_slots = raw[6]
        magic_slots = raw[7]

        class_name = CLASS_ORDER[class_id] if class_id < len(CLASS_ORDER) else f"class_{class_id}"

        entry = {
            "class": class_name,
            "class_index": class_id,
            "variant": "male" if variant == 0 else "female",
            "variant_index": variant,
            "entry_index": i,
            "offset": f"0x{offset:05X}",
            "offset_int": offset,
            "marker": f"0x{marker:02X}",
            "item_slots": item_slots,
            "magic_slots": magic_slots,
        }
        entries.append(entry)
    return entries


def scan_battle_req_entries(data):
    """Scan all battle requirement entries."""
    entries = []
    # Scan until we hit a different marker or run out
    for i in range(30):  # scan up to 30 entries
        offset = BATTLE_REQ_OFFSET + i * BATTLE_REQ_ENTRY_SIZE
        if offset + BATTLE_REQ_ENTRY_SIZE > len(data):
            break

        raw = data[offset:offset + BATTLE_REQ_ENTRY_SIZE]
        class_id = raw[0]
        variant = raw[1]
        battles = raw[2]
        padding = raw[3]
        marker = struct.unpack_from("<I", raw, 4)[0]

        # Stop if marker is not 0x3E
        if marker != 0x3E:
            break

        class_name = CLASS_ORDER[class_id] if class_id < len(CLASS_ORDER) else f"class_{class_id}"

        entry = {
            "class": class_name,
            "class_index": class_id,
            "variant": "male" if variant == 0 else "female",
            "variant_index": variant,
            "entry_index": i,
            "offset": f"0x{offset:05X}",
            "offset_int": offset,
            "battles_per_level": battles,
        }
        entries.append(entry)
    return entries


def scan_exe_patch_site(exe_data):
    """Scan the EXE for the assignable points patch site."""
    if len(exe_data) <= EXE_COMP_OFFSET + EXE_COMP_SIZE:
        return None

    original_bytes = exe_data[EXE_COMP_OFFSET:EXE_COMP_OFFSET + EXE_COMP_SIZE]
    store_bytes = exe_data[EXE_STORE_OFFSET:EXE_STORE_OFFSET + 6]

    # Check if it's vanilla (unpatched)
    vanilla_sig = bytes([0x44, 0x2B, 0xF2])  # sub r14d, edx
    is_vanilla = original_bytes[:3] == vanilla_sig

    return {
        "patch_offset": f"0x{EXE_COMP_OFFSET:05X}",
        "patch_size": EXE_COMP_SIZE,
        "store_offset": f"0x{EXE_STORE_OFFSET:05X}",
        "is_vanilla": is_vanilla,
        "current_bytes": " ".join(f"{b:02X}" for b in original_bytes),
        "store_bytes": " ".join(f"{b:02X}" for b in store_bytes),
        "vanilla_assignable": VANILLA_ASSIGNABLE,
        "description": (
            "Replace 15-byte computation with: "
            "mov eax,edi (8B C7) + shr eax,1 (C1 E8 01) + imul eax,eax,N (6B C0 NN) + NOPs. "
            "This gives levels_gained * N assignable points."
        ),
        "forbidden_patches": [
            {"offset": "0x18CADA", "register": "[rbx+0xC8]", "reason": "UI cursor offset"},
            {"offset": "0x18CAE5", "register": "[rbx+0xA8]", "reason": "UI layout value"},
            {"offset": "0x18CB04", "register": "[rbx+0x98]", "reason": "State machine (freezes game)"},
        ]
    }


def main():
    print("=" * 70)
    print("  Dokapon Kingdom: Connect — Class Stats Memory Mapper")
    print("=" * 70)

    data = load_file(DAT_PATH)
    print(f"Loaded {DAT_PATH} ({len(data)} bytes)")

    exe_data = None
    if os.path.exists(EXE_PATH):
        exe_data = load_file(EXE_PATH)
        print(f"Loaded {EXE_PATH} ({len(exe_data)} bytes)")
    else:
        print(f"[WARN] EXE not found at {EXE_PATH}")

    full_map = {}

    # Level-up entries
    print("\n=== LEVEL-UP STATS ===")
    print(f"  Table offset: 0x{LEVELUP_OFFSET:05X}")
    print(f"  Entry size: {LEVELUP_ENTRY_SIZE} bytes, Count: {LEVELUP_ENTRY_COUNT}")
    print()
    print(f"  {'Class':14} {'Var':4} {'AT':>4} {'DF':>4} {'MG':>4} {'SP':>4} {'HP':>4} {'Sum':>4} {'Offset'}")
    print(f"  {'-'*60}")

    levelup_entries = scan_levelup_entries(data)
    for e in levelup_entries:
        display = CLASS_DISPLAY.get(e["class"], e["class"])
        v = "M" if e["variant"] == "male" else "F"
        print(f"  {display:14} {v:4} {e['attack']:4} {e['defense']:4} {e['magic']:4} "
              f"{e['speed']:4} {e['hp']:4} {e['total_fixed']:4} {e['offset']}")

    full_map["levelup_table"] = {
        "offset": f"0x{LEVELUP_OFFSET:05X}",
        "entry_size": LEVELUP_ENTRY_SIZE,
        "entry_count": LEVELUP_ENTRY_COUNT,
        "stat_fields": {
            "attack": {"offset_in_entry": 0, "type": "int16_le"},
            "defense": {"offset_in_entry": 2, "type": "int16_le"},
            "magic": {"offset_in_entry": 4, "type": "int16_le"},
            "speed": {"offset_in_entry": 6, "type": "int16_le"},
            "hp": {"offset_in_entry": 8, "type": "int16_le"},
        },
        "entries": levelup_entries,
    }

    # Bag capacity
    print(f"\n=== BAG / INVENTORY CAPACITY ===")
    print(f"  Table offset: 0x{BAG_OFFSET:05X}")
    print(f"  Entry size: {BAG_ENTRY_SIZE} bytes, Count: {BAG_ENTRY_COUNT}")
    print()
    print(f"  {'Class':14} {'Var':4} {'Items':>5} {'Magic':>5} {'Offset'}")
    print(f"  {'-'*45}")

    bag_entries = scan_bag_entries(data)
    for e in bag_entries:
        display = CLASS_DISPLAY.get(e["class"], e["class"])
        v = "M" if e["variant"] == "male" else "F"
        print(f"  {display:14} {v:4} {e['item_slots']:5} {e['magic_slots']:5} {e['offset']}")

    full_map["bag_table"] = {
        "offset": f"0x{BAG_OFFSET:05X}",
        "entry_size": BAG_ENTRY_SIZE,
        "entry_count": BAG_ENTRY_COUNT,
        "fields": {
            "marker": {"offset_in_entry": 0, "type": "uint32_le", "expected": "0x44"},
            "class_id": {"offset_in_entry": 4, "type": "uint8"},
            "variant": {"offset_in_entry": 5, "type": "uint8", "values": "0=male, 1=female"},
            "item_slots": {"offset_in_entry": 6, "type": "uint8"},
            "magic_slots": {"offset_in_entry": 7, "type": "uint8"},
        },
        "entries": bag_entries,
    }

    # Battle requirements
    print(f"\n=== BATTLE REQUIREMENTS ===")
    print(f"  Table offset: 0x{BATTLE_REQ_OFFSET:05X}")
    print(f"  Entry size: {BATTLE_REQ_ENTRY_SIZE} bytes")
    print()
    print(f"  {'Class':14} {'Var':4} {'Battles':>7} {'Offset'}")
    print(f"  {'-'*40}")

    battle_entries = scan_battle_req_entries(data)
    for e in battle_entries:
        display = CLASS_DISPLAY.get(e["class"], e["class"])
        v = "M" if e["variant"] == "male" else "F"
        print(f"  {display:14} {v:4} {e['battles_per_level']:7} {e['offset']}")

    full_map["battle_req_table"] = {
        "offset": f"0x{BATTLE_REQ_OFFSET:05X}",
        "entry_size": BATTLE_REQ_ENTRY_SIZE,
        "entry_count": len(battle_entries),
        "fields": {
            "class_id": {"offset_in_entry": 0, "type": "uint8"},
            "variant": {"offset_in_entry": 1, "type": "uint8"},
            "battles_per_level": {"offset_in_entry": 2, "type": "uint8"},
            "marker": {"offset_in_entry": 4, "type": "uint32_le", "expected": "0x3E"},
        },
        "entries": battle_entries,
    }

    # EXE assignable points
    if exe_data:
        print(f"\n=== ASSIGNABLE POINTS (DkkStm.exe) ===")
        exe_info = scan_exe_patch_site(exe_data)
        if exe_info:
            print(f"  Patch offset:   {exe_info['patch_offset']}")
            print(f"  Patch size:     {exe_info['patch_size']} bytes")
            print(f"  Store offset:   {exe_info['store_offset']}")
            print(f"  Is vanilla:     {exe_info['is_vanilla']}")
            print(f"  Current bytes:  {exe_info['current_bytes']}")
            print(f"  Vanilla value:  {exe_info['vanilla_assignable']} points/level")
            print(f"\n  Forbidden patches:")
            for fp in exe_info["forbidden_patches"]:
                print(f"    {fp['offset']}: {fp['register']} — {fp['reason']}")

            full_map["assignable_points_exe"] = exe_info

    # Save
    print(f"\n--- Saving to {OUTPUT_JSON} ---")
    with open(OUTPUT_JSON, "w") as f:
        json.dump(full_map, f, indent=2)
    print("[OK] Saved class stats memory map")

    # Summary
    print(f"\n{'='*70}")
    print(f"  Level-up entries:     {len(levelup_entries)}")
    print(f"  Bag capacity entries: {len(bag_entries)}")
    print(f"  Battle req entries:   {len(battle_entries)}")
    print(f"  EXE patch site:       {'found' if exe_data else 'not scanned'}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
