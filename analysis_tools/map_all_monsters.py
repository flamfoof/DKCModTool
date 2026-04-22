"""
Monster Memory Mapper for Dokapon Kingdom: Connect
===================================================
Scans stageBase_EN.DAT for the contiguous monster record table and produces
a full machine-readable memory map suitable for the Monsters-Editor mod.

RECORD LAYOUT (discovered Apr 2026)
-----------------------------------
Each monster record is a variable-length, self-describing block:

  [8-byte header][name null-terminated, padded to 4-byte alignment][20-byte stats block]

Header (8 bytes):
  +0..+3  uint32 LE  marker       always 0x00000050 ('P')
  +4      uint8      prev_id      CSV-ID of previous monster in the chain
  +5      uint8      self_id      CSV-ID of this monster (1..N)
  +6      uint8      level        CSV "Lv." field (verified)
  +7      uint8      reserved     always 0

Name: ASCII, null-terminated, 4-byte aligned (so padding NULs follow)

Stats block (20 bytes, offset 0 = stats_off):
  +0..+1   uint16 LE  hp
  +2..+3   uint16 LE  attack
  +4..+5   uint16 LE  defense
  +6..+7   uint16 LE  speed       *** DAT stores SP before MG ***
  +8..+9   uint16 LE  magic
  +10..+11 uint16 LE  reserved    always 0 0 for all 137 monsters
  +12      uint8      off_magic   offensive-magic enum (see below, 0=N/A)
  +13      uint8      def_magic   defensive-magic enum (see below, 0=N/A)
  +14      uint8      battle_skill 7A-table battle-skill id (see skill_tables_memory_map.json)
  +15      uint8      reserved    always 0
  +16..+17 uint16 LE  exp
  +18..+19 uint16 LE  gold

TABLE BOUNDS
------------
First record: 0x19DE0 (Rogue, CSV id 1)
Last record:  ...     (Rico Jr., contiguous run of 137 records)

Records are packed tightly with no padding between them; the next header's
0x50 marker starts immediately after the previous record's stats block.

DROPS (drop1 / drop2 / special_drop) are NOT in these records - they live
in a separate sub-table that has not been located yet. This mapper does
NOT attempt to patch drops.
"""
from __future__ import annotations

import csv
import json
import os
import struct
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DAT_PATH = os.path.join(ROOT_DIR, "Backup", "assets", "stageBase_EN.DAT")
CSV_PATH = os.path.join(SCRIPT_DIR, "table_sample", "dokapon_monsters.csv")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "monsters_memory_map.json")
MOD_JSON = os.path.join(ROOT_DIR, "Mods", "Monsters-Editor", "monsters.json")

MONSTER_TABLE_START = 0x19DE0
MONSTER_HEADER_MARKER = b"\x50\x00\x00\x00"
MONSTER_STATS_BLOCK_SIZE = 20

# Enums derived experimentally by cross-referencing all 137 records against
# the CSV Offensive/Defensive-Magic columns. Preferred display names picked
# where the CSV had duplicates/typos (e.g. "Refresh+" vs "Refresh +").

OFFENSIVE_MAGIC_BY_ID = {
    0: "N/A",          1: "Scorch",        2: "Scorcher",     3: "Giga Blaze",
    4: "Zap",          5: "Zapper",        6: "Lectro Beam",  7: "Chill",
    8: "Chiller",      9: "Ice Barrage",   10: "Gust",        11: "Guster",
    12: "F5 Storm",    13: "Mirror Image", 14: "Teleport",    15: "Aurora",
    16: "Curse",       17: "Sleepy",       18: "Blind",       19: "Banish",
    20: "Drain",       21: "Swap",         22: "Pickpocket",  23: "Rust",
}

DEFENSIVE_MAGIC_BY_ID = {
    0: "N/A",         1: "M Guard",     2: "M Guard+",    3: "M Guard DX",
    4: "Refresh",     5: "Refresh+",    6: "Refresh DX",  7: "Super Cure",
    8: "Seal Magic",  9: "Seal Magic+", 10: "Shock",      11: "Mirror",
    12: "MG Charge",  13: "AT Charge",  14: "DF Charge",  15: "SP Charge",
    16: "Charge All", 17: "Charm",      18: "Bounce",
}

OFF_MAGIC_TO_ID = {v.lower(): k for k, v in OFFENSIVE_MAGIC_BY_ID.items()}
DEF_MAGIC_TO_ID = {v.lower(): k for k, v in DEFENSIVE_MAGIC_BY_ID.items()}
# CSV typo tolerance
DEF_MAGIC_TO_ID["refresh +"] = 5


def load_dat() -> bytes:
    with open(DAT_PATH, "rb") as f:
        return f.read()


def load_csv():
    if not os.path.exists(CSV_PATH):
        return {}
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return {r["Name"].strip(): r for r in rows if r.get("Name")}


def scan_monsters(data: bytes):
    """Walk the contiguous monster table starting at MONSTER_TABLE_START."""
    monsters = []
    pos = MONSTER_TABLE_START
    while pos < len(data) - 30:
        if data[pos:pos + 4] != MONSTER_HEADER_MARKER or data[pos + 7] != 0:
            break
        hdr = data[pos:pos + 8]
        prev_id = hdr[4]
        self_id = hdr[5]
        level = hdr[6]

        name_start = pos + 8
        nul = data.find(b"\x00", name_start, name_start + 40)
        if nul <= name_start:
            break
        name_bytes = data[name_start:nul]
        if not name_bytes or not all(32 <= c < 127 for c in name_bytes):
            break
        name = name_bytes.decode("ascii")
        name_len = nul - name_start + 1
        name_padded = (name_len + 3) & ~3
        stats_off = name_start + name_padded

        if stats_off + MONSTER_STATS_BLOCK_SIZE > len(data):
            break

        hp, at, df, sp, mg = struct.unpack_from("<5H", data, stats_off)
        reserved_10 = struct.unpack_from("<H", data, stats_off + 10)[0]
        off_mag = data[stats_off + 12]
        def_mag = data[stats_off + 13]
        skill = data[stats_off + 14]
        reserved_15 = data[stats_off + 15]
        exp, gold = struct.unpack_from("<2H", data, stats_off + 16)

        monsters.append({
            "name": name,
            "self_id": self_id,
            "prev_id": prev_id,
            "level": level,
            "header_offset": f"0x{pos:05X}",
            "name_offset": f"0x{name_start:05X}",
            "name_max_len": name_padded - 1,  # max chars before null
            "stats_offset": f"0x{stats_off:05X}",
            "record_size": 8 + name_padded + MONSTER_STATS_BLOCK_SIZE,
            "hp": hp, "attack": at, "defense": df,
            "magic": mg, "speed": sp,
            "exp": exp, "gold": gold,
            "battle_skill_id": skill,
            "offensive_magic_id": off_mag,
            "defensive_magic_id": def_mag,
            "offensive_magic": OFFENSIVE_MAGIC_BY_ID.get(off_mag, f"unknown_{off_mag}"),
            "defensive_magic": DEFENSIVE_MAGIC_BY_ID.get(def_mag, f"unknown_{def_mag}"),
            "_reserved_10": reserved_10,
            "_reserved_15": reserved_15,
        })

        pos = stats_off + MONSTER_STATS_BLOCK_SIZE

    return monsters


def load_skill_names():
    """Load battle-skill-id -> name from skill_tables_memory_map.json."""
    path = os.path.join(SCRIPT_DIR, "skill_tables_memory_map.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)
    return {e["id"]: e["skill_name"]
            for e in data["battle_skills_table"]["entries"]}


def verify_against_csv(monsters, csv_by_name, skill_names):
    """Verify each DAT monster against CSV reference, return stats."""
    def to_int(v):
        s = "".join(c for c in str(v) if c.isdigit() or c == "-")
        return int(s) if s and s != "-" else None

    stat_ok = stat_bad = skill_ok = skill_bad = 0
    off_ok = off_bad = def_ok = def_bad = 0
    missing_csv = []

    for m in monsters:
        row = csv_by_name.get(m["name"])
        sid = m["battle_skill_id"]
        if sid == 0:
            m["skill_name"] = "N/A"
        else:
            m["skill_name"] = skill_names.get(sid, f"unknown_skill_{sid}")
        if not row:
            missing_csv.append(m["name"])
            m["csv_status"] = "NOT_IN_CSV"
            continue

        def check(field, csv_field):
            expected = to_int(row.get(csv_field, ""))
            return (expected is not None and expected == m[field]), expected

        stat_fields = [("hp", "HP"), ("attack", "AT"), ("defense", "DF"),
                       ("magic", "MG"), ("speed", "SP"),
                       ("exp", "EXP"), ("gold", "Gold")]
        stat_matches = [check(f, c) for f, c in stat_fields]
        all_stats_match = all(ok for ok, _ in stat_matches) or any(v is None for _, v in stat_matches)

        expected_skill = row.get("Battle Skill", "").strip()
        skill_match = (expected_skill == m["skill_name"]) if expected_skill and expected_skill != "?" else True

        expected_off = row.get("Offensive Magic", "").strip()
        off_match = (expected_off.lower() == m["offensive_magic"].lower()) if expected_off else True

        expected_def = row.get("Defensive Magic", "").strip().replace(" +", "+")
        def_match = (expected_def.lower() == m["defensive_magic"].lower()) if expected_def else True

        m["csv_status"] = "OK" if (all_stats_match and skill_match and off_match and def_match) else "MISMATCH"
        m["csv_level"] = to_int(row.get("Lv."))

        if all_stats_match: stat_ok += 1
        else: stat_bad += 1
        if skill_match: skill_ok += 1
        else: skill_bad += 1
        if off_match: off_ok += 1
        else: off_bad += 1
        if def_match: def_ok += 1
        else: def_bad += 1

    return {
        "stats_ok": stat_ok, "stats_bad": stat_bad,
        "skill_ok": skill_ok, "skill_bad": skill_bad,
        "off_magic_ok": off_ok, "off_magic_bad": off_bad,
        "def_magic_ok": def_ok, "def_magic_bad": def_bad,
        "dat_only_no_csv": missing_csv,
    }


def emit_memory_map(monsters, verify_stats):
    return {
        "table": {
            "start_offset": f"0x{MONSTER_TABLE_START:05X}",
            "count": len(monsters),
            "record_layout": (
                "[8-byte header: 0x50 marker + prev_id + self_id + level + 0]"
                " [name null-term, 4-byte padded]"
                " [20-byte stats: HP AT DF SP MG, 2 reserved, off_mag_id,"
                " def_mag_id, skill_id, 0, EXP, Gold]"
            ),
            "note_sp_mg": "DAT stores SPEED before MAGIC (swapped vs CSV order).",
            "note_drops": "drop1 / drop2 / special_drop are NOT in these records; sub-table not yet located.",
        },
        "offensive_magic_enum": OFFENSIVE_MAGIC_BY_ID,
        "defensive_magic_enum": DEFENSIVE_MAGIC_BY_ID,
        "verification": verify_stats,
        "entries": monsters,
    }


def emit_mod_json(monsters):
    """Compact format consumed by Mods/Monsters-Editor/build_mod.py."""
    entries = {}
    for m in monsters:
        entries[m["name"]] = {
            "_offsets": {
                "header": m["header_offset"],
                "name":   m["name_offset"],
                "stats":  m["stats_offset"],
                "name_max_len": m["name_max_len"],
            },
            "self_id": m["self_id"],
            "level": m["level"],
            "hp": m["hp"],
            "attack": m["attack"],
            "defense": m["defense"],
            "magic": m["magic"],
            "speed": m["speed"],
            "exp": m["exp"],
            "gold": m["gold"],
            "battle_skill": m["skill_name"],
            "offensive_magic": m["offensive_magic"],
            "defensive_magic": m["defensive_magic"],
            "new_name": None,  # set to a string (<= name_max_len) to rename
        }
    return {
        "_comment": (
            "Monsters-Editor config. Edit any field to patch stageBase_EN.DAT."
            " Set `new_name` to a string (length <= _offsets.name_max_len) to"
            " rename a monster; leave null to keep current name."
            " battle_skill / offensive_magic / defensive_magic must match an"
            " entry in the enums documented in monsters_memory_map.json."
        ),
        "_offensive_magic_options": list(OFFENSIVE_MAGIC_BY_ID.values()),
        "_defensive_magic_options": list(DEFENSIVE_MAGIC_BY_ID.values()),
        "monsters": entries,
    }


def main():
    print("=" * 72)
    print("  Dokapon Kingdom: Connect - Monster Memory Mapper")
    print("=" * 72)

    data = load_dat()
    print(f"Loaded {DAT_PATH} ({len(data)} bytes)")

    csv_by_name = load_csv()
    print(f"Loaded CSV reference ({len(csv_by_name)} named monsters)")

    skill_names = load_skill_names()
    print(f"Loaded skill enum ({len(skill_names)} battle skills)")
    print()

    monsters = scan_monsters(data)
    print(f"Found {len(monsters)} monsters in contiguous table "
          f"starting at 0x{MONSTER_TABLE_START:X}")
    print()

    stats = verify_against_csv(monsters, csv_by_name, skill_names)
    print(f"Verification against CSV:")
    print(f"  stats (HP/AT/DF/MG/SP/EXP/Gold): {stats['stats_ok']} OK, {stats['stats_bad']} mismatch")
    print(f"  battle_skill:                    {stats['skill_ok']} OK, {stats['skill_bad']} mismatch")
    print(f"  offensive_magic:                 {stats['off_magic_ok']} OK, {stats['off_magic_bad']} mismatch")
    print(f"  defensive_magic:                 {stats['def_magic_ok']} OK, {stats['def_magic_bad']} mismatch")
    print(f"  {len(stats['dat_only_no_csv'])} monsters in DAT but not CSV "
          f"(bosses / variants): {stats['dat_only_no_csv'][:8]}...")
    print()

    mm = emit_memory_map(monsters, stats)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(mm, f, indent=2)
    print(f"Wrote {OUTPUT_JSON}")

    os.makedirs(os.path.dirname(MOD_JSON), exist_ok=True)
    with open(MOD_JSON, "w") as f:
        json.dump(emit_mod_json(monsters), f, indent=2)
    print(f"Wrote {MOD_JSON}")


if __name__ == "__main__":
    main()
