"""
analyze_skill_tables.py
=======================
Dumps and parses the two tag-prefixed skill tables found in
`stageBase_EN.DAT` in the 0x14000 region:

  1. Battle skills table  (tag `7A 00 00 00`)
     - SP-consuming combat commands (Heal, Thunder, Prayer, Pierce, ...)
     - Entry layout: [7A 00 00 00 id accuracy effectiveness flag][name padded]

  2. Class field skills table (tag `7B 00 00 00`, starts at 0x14638)
     - 12 class-signature field skills (War Cry, Holy Aura, Item Combo, ...)
     - Entry layout: [7B 00 00 00 id chance 00 00][name padded]

IMPORTANT CAVEAT (discovered Apr 2026):
  The chance byte (header+5) in the 7B field-skill table is UI/description-only.
  Patching it changes the % displayed in the status screen but does NOT change
  the actual trigger rate at runtime. Real trigger logic is hardcoded in
  `DkkStm.exe` (the vanilla chance sequence does not appear anywhere in the
  EXE, so immediates are likely baked directly into each skill's handler).

  The 7A battle-skills table byte layout is decoded (accuracy/effectiveness
  match wiki values for verified skills like Muscle=100/50) but runtime
  effect has NOT been confirmed — the same UI-only caveat may apply.

USAGE
-----
    cd "Connect Mod Installer v2.0.0"
    python DKCModTool/analysis_tools/analyze_skill_tables.py

Edit STAGEBASE / EXE_PATH at the top to point at a different file.
"""
from __future__ import annotations

import os
import re
import sys

# ---------------------------------------------------------------- config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
STAGEBASE = os.path.join(ROOT, "Backup", "assets", "stageBase_EN.DAT")
EXE_PATH = os.path.join(ROOT, "Backup", "DkkStm.exe")

# ---------------------------------------------------------------- helpers
def load(path: str) -> bytes:
    if not os.path.exists(path):
        print(f"[ERROR] file not found: {path}")
        sys.exit(1)
    with open(path, "rb") as f:
        return f.read()


def parse_tagged_records(data: bytes, tag: bytes, start: int, end: int):
    """Walk [tag + 4 header bytes + null-term name padded to 4].

    Yields tuples of (header_offset, id_byte, byte5, byte6, byte7, name).
    Stops when tag no longer matches at the expected offset.
    """
    off = start
    while off < end:
        if data[off:off + 4] != tag:
            break
        sid = data[off + 4]
        b5 = data[off + 5]
        b6 = data[off + 6]
        b7 = data[off + 7]
        name_start = off + 8
        nul = data.find(b"\x00", name_start)
        if nul < 0 or nul > name_start + 64:
            break
        name = data[name_start:nul].decode("ascii", errors="replace")
        name_len = nul - name_start + 1  # include null
        padded = (name_len + 3) & ~3
        yield (off, sid, b5, b6, b7, name)
        off = name_start + padded


# ---------------------------------------------------------------- field skills (7B)
FIELD_SKILL_TABLE_OFFSET = 0x14638
FIELD_SKILL_TAG = b"\x7B\x00\x00\x00"

CLASS_ORDER_12 = [
    "warrior", "magician", "thief", "cleric", "spellsword", "alchemist",
    "ninja", "monk", "acrobat", "robo_knight", "hero", "darkling",
]


def dump_field_skill_table(data: bytes):
    print("=" * 72)
    print("FIELD SKILLS TABLE (tag 7B) - class signature passives / triggers")
    print("=" * 72)
    print(f"Start offset: 0x{FIELD_SKILL_TABLE_OFFSET:05X}")
    print()
    print(f"{'Hdr':>8}  {'ID':>3}  {'Chance':>7}  {'Class':<12}  Skill")
    print("-" * 72)
    records = list(parse_tagged_records(
        data, FIELD_SKILL_TAG,
        FIELD_SKILL_TABLE_OFFSET, FIELD_SKILL_TABLE_OFFSET + 0x200,
    ))
    for i, (off, sid, chance, _b6, _b7, name) in enumerate(records):
        cls = CLASS_ORDER_12[i] if i < len(CLASS_ORDER_12) else "?"
        print(f"0x{off:05X}  {sid:>3}  {chance:>5}%   {cls:<12}  {name}")
    print()
    print(f"Total entries: {len(records)}")
    print()
    print("NOTE: chance byte is UI-DISPLAY ONLY - real trigger logic is in EXE.")
    print()


# ---------------------------------------------------------------- battle skills (7A)
BATTLE_SKILL_TAG = b"\x7A\x00\x00\x00"
# All 46 battle skills live in a single contiguous 7A-tagged region
# from 0x14724 to 0x14A3C (first record "Charge" starts at 0x14724).
# The earlier-documented "scattered" offsets in ModsTest/Battle_Skills-Editor
# were pointing at stray string references in other parts of the DAT and
# are NOT the actual skill records.
BATTLE_REGION_START = 0x14724
BATTLE_REGION_END = 0x14A40


def dump_battle_skill_table(data: bytes):
    print("=" * 72)
    print("BATTLE SKILLS TABLE (tag 7A) - SP combat commands")
    print("=" * 72)
    print(f"Region: 0x{BATTLE_REGION_START:05X} - 0x14A3C (46 contiguous records)")
    print()
    print("Layout per record: [7A 00 00 00 id accuracy effectiveness flag]")
    print("                   [name null-terminated, padded to 4-byte alignment]")
    print()
    print(f"{'Hdr':>8}  {'ID':>3}  {'Acc':>4}  {'Eff':>4}  {'Flag':>4}  Skill")
    print("-" * 72)
    records = list(parse_tagged_records(
        data, BATTLE_SKILL_TAG, BATTLE_REGION_START, BATTLE_REGION_END,
    ))
    for off, sid, acc, eff, flag, name in records:
        print(f"0x{off:05X}  {sid:>3}  {acc:>4}  {eff:>4}  0x{flag:02X}   {name}")
    print()
    print(f"Total entries: {len(records)}")
    print()
    print("Accuracy/effectiveness interpretation (verified against wiki):")
    print("  accuracy      = trigger % 0-100 (e.g. Muscle=100, Virus=75)")
    print("  effectiveness = skill-specific (damage %, stat-boost %, ...)")
    print("  flag          = skill category (0x01=buff, 0x02=attack, 0x04=heal)")
    print()
    print("CAVEAT: runtime effect of patching these bytes has NOT been verified.")
    print("The 7B field-skill table turned out to be UI-only; the 7A table")
    print("MIGHT have the same caveat. Test before shipping a mod.")
    print()


# ---------------------------------------------------------------- xrefs
def search_name_xrefs(exe: bytes, names):
    print("=" * 72)
    print("EXE NAME XREFS (anchors for locating real trigger-handler code)")
    print("=" * 72)
    for name in names:
        nb = name.encode("ascii")
        locs = [m.start() for m in re.finditer(re.escape(nb), exe)]
        hits = ", ".join(f"0x{l:06X}" for l in locs[:5]) or "(none)"
        print(f"  {name:14}: {hits}")
    print()


def search_alt_chance_tables(data: bytes, exe: bytes):
    """Look for a hidden secondary chance table that might drive real triggers.

    The 7B table has variable-length names between chance bytes, so the 12
    chance values are NOT contiguous in the DAT. If a real trigger table
    existed elsewhere, it would likely store the 12 chances contiguously
    (or interleaved with a small fixed stride). Check all reasonable strides.
    """
    print("=" * 72)
    print("ALTERNATE CHANCE-TABLE SCAN")
    print("=" * 72)
    vanilla = [20, 100, 100, 20, 33, 25, 100, 100, 50, 20, 100, 100]
    found_any = False
    for stride in (1, 2, 4, 8, 12, 16):
        for buf, label in ((data, "DAT"), (exe, "EXE")):
            # Build needle as vanilla[i] at every `stride` bytes, require
            # exact match at stride 1 only (others need scan with mask).
            if stride == 1:
                needle = bytes(vanilla)
                hits = [m.start() for m in re.finditer(re.escape(needle), buf)]
            else:
                hits = []
                step = stride
                limit = len(buf) - (len(vanilla) - 1) * step
                for i in range(0, limit):
                    ok = True
                    for k, v in enumerate(vanilla):
                        if buf[i + k * step] != v:
                            ok = False
                            break
                    if ok:
                        hits.append(i)
                        if len(hits) > 5:
                            break
            if hits:
                found_any = True
                print(f"  stride={stride:<2} in {label}: {[hex(h) for h in hits[:5]]}")
    if not found_any:
        print("  No contiguous or strided copy of the vanilla chance sequence")
        print("  found anywhere in DAT or EXE.")
        print("  Conclusion: real trigger values are NOT held in a parallel")
        print("  data table - they must be hardcoded immediates in EXE code.")
    print()


# ---------------------------------------------------------------- main
def main():
    data = load(STAGEBASE)
    exe = load(EXE_PATH)

    dump_field_skill_table(data)
    dump_battle_skill_table(data)

    # Anchors for future EXE disassembly work:
    field_skill_names = [
        "War Cry", "Mage Combo", "Pickpocket", "Holy Aura", "Barrier",
        "Duplicate", "Item Combo", "Fire Up", "Play Dead", "GOTO",
        "Full Combo", "Dark Arts",
    ]
    search_name_xrefs(exe, field_skill_names)
    search_alt_chance_tables(data, exe)


if __name__ == "__main__":
    main()
