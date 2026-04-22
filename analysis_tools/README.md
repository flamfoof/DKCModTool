# Analysis Tools

Standalone Python scripts used to reverse-engineer the `DkkStm.exe` PE structure and the `stageBase_EN.DAT` game data format. These were used to build the DKCModTool data definitions and are kept for future use when mapping new data structures or investigating game updates.

All scripts should be run from the **root project directory** (`Connect Mod Installer v2.0.0/`), not from this folder.

---

## analyze_exe.py

**Purpose:** Analyzes the PE (Portable Executable) structure of `DkkStm.exe`.

**What it shows:**
- DOS/PE header fields (magic, offsets, signatures)
- COFF header (machine type, section count, timestamp)
- Optional header (image base, alignments, image size)
- All PE sections with virtual/raw addresses and sizes
- Comparison with old DKCedit hardcoded values
- Space available for adding new sections
- Scans for known strings (class names, game text, `.dkcedit` marker)

**Usage:**
```bash
cd "Connect Mod Installer v2.0.0"
python DKCModTool/analysis_tools/analyze_exe.py
```

**Notes:**
- Reads from `Backup\DkkStm.exe` by default — edit the `EXE_PATH` variable at the top to change this.
- Useful after a game update to see if sections were added/moved.

---

## analyze_data.py

**Purpose:** Analyzes the `stageBase_EN.DAT` file and the exe for game data locations.

**What it shows:**
- stageBase header and first 64 bytes
- All ASCII strings found in the file (5000+)
- Data at known changelog offsets (bags, level-ups, skills, shops, enemies, etc.)
- Damage formula text patterns
- Class/job name locations
- CJK character region scan in the exe
- Resource section analysis

**Usage:**
```bash
cd "Connect Mod Installer v2.0.0"
python DKCModTool/analysis_tools/analyze_data.py
```

**Notes:**
- Reads stageBase from `Mods\JaJo's Balance Patch v1.0.1\Assets\stageBase_EN.DAT` by default.
- Reads the exe from `Backup\DkkStm.exe` by default.
- Edit the `STAGEBASE` and `EXE_PATH` variables at the top to point to different files.

---

## analyze_records.py

**Purpose:** Deep-dives into specific data record structures within `stageBase_EN.DAT`.

**What it shows:**
- Hex dumps of specific regions: bags, level-ups, skills, items, equipment, shops, enemies, status effects, damage formulas, loot tables, AI tables, job unlocks, class names, item flags
- File header structure (`@BAS` format fields)
- Pointer table scanning

**Usage:**
```bash
cd "Connect Mod Installer v2.0.0"
python DKCModTool/analysis_tools/analyze_records.py
```

**Notes:**
- Reads from `Mods\JaJo's Balance Patch v1.0.1\Assets\stageBase_EN.DAT` by default.
- Edit the `STAGEBASE` variable at the top to analyze a different file.
- Output is large — pipe to a file or `less` for easier reading:
  ```bash
  python DKCModTool/analysis_tools/analyze_records.py > records_dump.txt
  ```

---

## map_all_equipment.py

**Purpose:** Comprehensive scanner for every weapon, shield, and accessory in `stageBase_EN.DAT`. Produces the ground-truth memory map consumed by `@[Mods/Equipment-Editor]`.

**What it maps:**
- All 67 weapons (marker `0x58`) with per-item `sub_rank`, `preferred_job`, `effect_chance`, `rarity_tier`, price, and 5 stats
- All 40 shields (marker `0x5E`, sub-type `0x51`) — note DF/AT stat positions are swapped vs. weapons
- All 33 accessories (marker `0x64`) across 9 sub-types (gloves, rings, bracelets, necklaces, footwear, bandanas, badges, studs, crowns)
- Each entry's exact `header_offset`, `name_offset`, `data_offset`, and `name_max_len` (needed to respect 4-byte padding when renaming)
- Cross-verification against `table_sample/*.csv` reference tables (wiki-sourced)

**Usage:**
```bash
cd "Connect Mod Installer v2.0.0"
python DKCModTool/analysis_tools/map_all_equipment.py
```

**Machine-readable outputs:**
- `equipment_memory_map.json` (67 + 40 + 33 = 140 entries with full metadata)
- **Side effect:** also rewrites `@[Mods/Equipment-Editor]/equipment.json` as ground-truth-from-DAT. Back up any hand-edited mod config before running.

**Key findings from this analysis (Apr 2026):**
- The DAT contains **140 equipment items** (67 weapons + 40 shields + 33 accessories), matching the wiki's totals. The outdated line in `@[Mods/Equipment-Editor/README.md]` claiming "only 27 items exist in the DAT file" is pre-mapper legacy text and no longer accurate.
- Entry layout universally: `[8-byte header][name null-term, padded to 4-byte][20-byte data block]`. The 20-byte block splits into a 4-byte metadata quad + `uint32 price` + five `int16` stats + 2-byte trail. Weapon metadata is `(sub_rank, preferred_job, effect_chance, rarity_tier)`; shields and accessories use `(effect_chance, rarity_tier, 0, 0)`.
- **Shields swap byte positions 0-1** (DF at offset 8-9, AT at 10-11) — every other equipment type keeps AT first. The decoder in `decode_shield_entry` flips them so JSON output is type-uniform.
- **HP is stored divided by 10** across all equipment. The mapper multiplies back to real HP but keeps the raw byte in `hp_raw` for round-trip safety.
- **Effects are hardcoded per item ID in the EXE** — only `effect_chance` (activation %) is patchable via DAT. Changing which effect fires (Zapper vs Sleep etc.) requires EXE patching, not DAT.
- The CSV verifier marks items with asterisked stats as `DYNAMIC` (game-computed, e.g. Criminal Studs). Build scripts must skip stat patching for these.
- `preferred_job` byte (weapons, meta byte 1) uses its own 0-8 enum that **skips** Spellsword / Alchemist / Hero / Darkling, unlike the 12-class order in DKC-Class-Stats-Editor. Do not cross-reference the two indices.
- **`equipment_offsets_map.json` (older file) is superseded** by `equipment_memory_map.json`. The old file contains false matches like `"Knife (0x77F7)"` with `speed: -12287` — those are naive string-search hits into unrelated regions. Prefer the new map in all new code.

---

## map_all_monsters.py

**Purpose:** Reverse-engineer and map the contiguous monster record table in `stageBase_EN.DAT` for `@[Mods/Monsters-Editor]`. Produces a machine-readable memory map plus a ground-truth mod config.

**What it maps:**
- All 137 monsters in the contiguous table starting at `0x19DE0` (Rogue) and running through Rico Jr.
- Per-monster header offset, name offset + max length, stats offset, record size
- Stats: HP, AT, DF, SP, MG, EXP, Gold
- Battle skill byte (cross-referenced against the 7A table in `skill_tables_memory_map.json`)
- Offensive-magic and defensive-magic bytes — mapped to human names via two enums derived by scanning all 137 records against `table_sample/dokapon_monsters.csv`
- CSV verification stats (stats match / skill match / magic match counts)

**Usage:**
```bash
cd "Connect Mod Installer v2.0.0"
python DKCModTool/analysis_tools/map_all_monsters.py
```

**Machine-readable outputs:**
- `monsters_memory_map.json` — full map + enums + verification stats
- **Side effect:** rewrites `@[Mods/Monsters-Editor]/monsters.json` as ground-truth-from-DAT. Back up any hand-edited mod config before running.

**Key findings from this analysis (Apr 2026):**
- Monster records form a single contiguous table, not 21 scattered entries as the previous README claimed. Layout: `[8-byte header][name null-term, padded to 4][20-byte stats]`, packed with no gaps.
- **Header format:** `0x50 0x00 0x00 0x00` constant marker + `prev_id(u8)` + `self_id(u8)` + `level(u8)` + `0`. The level byte matches the CSV "Lv." column exactly.
- **Stats block: SP is stored BEFORE MG** (swapped vs. the CSV column order). Every mod that wrote MG/SP in the CSV order corrupted those two stats.
- **Offensive-magic enum (24 entries):** `0=N/A, 1=Scorch, 2=Scorcher, 3=Giga Blaze, 4=Zap, 5=Zapper, 6=Lectro Beam, 7=Chill, 8=Chiller, 9=Ice Barrage, 10=Gust, 11=Guster, 12=F5 Storm, 13=Mirror Image, 14=Teleport, 15=Aurora, 16=Curse, 17=Sleepy, 18=Blind, 19=Banish, 20=Drain, 21=Swap, 22=Pickpocket, 23=Rust`. 100% match rate across all 133 CSV-linked monsters.
- **Defensive-magic enum (19 entries):** `0=N/A, 1=M Guard, 2=M Guard+, 3=M Guard DX, 4=Refresh, 5=Refresh+, 6=Refresh DX, 7=Super Cure, 8=Seal Magic, 9=Seal Magic+, 10=Shock, 11=Mirror, 12=MG Charge, 13=AT Charge, 14=DF Charge, 15=SP Charge, 16=Charge All, 17=Charm, 18=Bounce`. 132/133 match; the one outlier is a CSV "Bounce"/"Mirror" labeling inconsistency.
- **Battle skill byte = 7A-table `id`** (verified against `skill_tables_memory_map.json`): 124/133 match. Remaining 9 use `id=0` (no skill) or high ids reserved for boss variants (`Clonus` has `id=128`).
- **Drops (drop1 / drop2 / special_drop) are NOT in these records.** A scan of the 20-byte stats block found no CSV-drop-related bytes. The drop sub-table lives elsewhere and has not been located. The build script intentionally omits drop patching rather than guessing.
- Pre-existing `extract_all_monsters.py` / `extract_monster_table.py` scripts were stat-only probes that missed the `offensive_magic` / `defensive_magic` / `battle_skill` bytes entirely and used the wrong offsets for EXP/Gold (+10/+12 instead of +16/+18). The new `map_all_monsters.py` supersedes them.

---

## map_class_stats.py

**Purpose:** Scans `stageBase_EN.DAT` + `DkkStm.exe` and produces a full machine-readable memory map of every class-related data structure used by `@[Mods/DKC-Class-Stats-Editor]`.

**What it maps:**
- Level-up stat gains table (`0x1733E`, 24 entries x 28 bytes)
- Bag / inventory capacity table (`0x175D8`, 22 entries x 8 bytes — Darkling has no bag slot)
- Battle requirements per level table (`0x1768C`, 24 logical slots x 8 bytes)
- Assignable-points EXE patch site (`0x18CABF` in `DkkStm.exe`) with vanilla signature check and forbidden-patch list

**Usage:**
```bash
cd "Connect Mod Installer v2.0.0"
python DKCModTool/analysis_tools/map_class_stats.py
```

**Machine-readable output:** `class_stats_memory_map.json` (regenerated each run).

**Key findings from this analysis (Apr 2026):**
- The battle-req table only has 21 "clean" entries with marker `0x3E`. The last 3 slots (Hero F, Darkling M, Darkling F at offsets `0x17734`, `0x1773C`, `0x17744`) have irregular markers but byte 2 still holds `battles_per_level` in the same position, and the build script writes them successfully.
- **Darkling F has a vanilla `battles_per_level` of `44`** — a clear outlier against every other class (`7/8/10`). Darkling is not player-selectable, so this value is likely a sentinel. The `class_stats_backup.json` uses `10` (matching Darkling M) as the intended vanilla representation.
- True vanilla level-up stats / bag slots / battle counts were extracted directly from the DAT via this mapper and used to rebuild `@[Mods/DKC-Class-Stats-Editor/class_stats_backup.json]` as a round-trip-safe reference (running the build script against it patches zero bytes except the Darkling-F sentinel correction).
- The assignable-points EXE patch site is confirmed stable; the three forbidden neighbors (`[rbx+0xC8]`, `[rbx+0xA8]`, `[rbx+0x98]`) were found empirically during earlier work and are preserved in the memory map as anti-regression documentation.

---

## analyze_skill_tables.py

**Purpose:** Parses the two tag-prefixed skill tables in `stageBase_EN.DAT` and reports their layout and per-entry values.

**What it shows:**
- Full class-field-skill table (tag `7B`, 12 entries at `0x14638`) with each class's signature skill + vanilla trigger %
- Full battle-skill table (tag `7A`, 46 contiguous entries at `0x14724-0x14A3C`) with accuracy / effectiveness / flag bytes
- EXE name xrefs for field-skill handler code (anchors for future disassembly)
- Scan for hidden parallel chance tables (confirms none exist)

**Usage:**
```bash
cd "Connect Mod Installer v2.0.0"
python DKCModTool/analysis_tools/analyze_skill_tables.py
```

**Machine-readable output:** `skill_tables_memory_map.json` (committed alongside this script) contains the parsed tables with offsets, IDs, and vanilla values for tooling consumption.

**Key findings from this analysis (Apr 2026):**
- The `7B` field-skill table chance byte at `header+5` is **UI-display-only**. Patching it changes the % shown on the status screen but does NOT change the runtime trigger rate. Confirmed experimentally (Warrior/Cleric/Spellsword set to 100% still triggered at vanilla rates after reinstall).
- The vanilla chance sequence `[20,100,100,20,33,25,100,100,50,20,100,100]` appears zero times in both the DAT (outside this table) and the EXE, at any stride. Real trigger values must be hardcoded immediates baked into each skill's handler in `DkkStm.exe`.
- Useful EXE string anchors for locating those handlers: `Duplicate` @ `0x4ABA39`, `0x4ABE09`; `Play Dead` @ `0x5A8588`; `Dark Arts` @ `0x5A8B80`. Most other field-skill names are NOT in the EXE as literal strings.
- The `7A` battle-skill table byte layout was fully decoded and matches wiki-documented values (e.g. Muscle = 100 accuracy / 50 effectiveness / 0x01 buff-flag). Runtime effect of patching these bytes has **not** been verified; it may share the UI-only caveat of the `7B` table.
- The `SKILL_OFFSETS` dict in `ModsTest/Battle_Skills-Editor/build_mod.py` (previously documented as "46 skills across 8 scattered regions") is incorrect: all 46 records live contiguously at `0x14724-0x14A3C`. The scattered offsets were stray name references elsewhere in the DAT.

---

## When to Use These

- **After a game update:** Run `analyze_exe.py` to check if the PE layout changed.
- **Mapping new data:** Run `analyze_records.py` with adjusted offsets to hex-dump unknown regions.
- **Finding strings:** Run `analyze_data.py` to locate game text (item names, descriptions, etc.).
- **Verifying mod offsets:** Compare hex dumps against your changelog entries.
- **Working on skill data:** Run `analyze_skill_tables.py` to get current offsets and per-skill values, then consult `skill_tables_memory_map.json` for the machine-readable version. Note the UI-only caveat before designing a skill mod.
- **Working on class stats / bags / battle reqs / assignable points:** Run `map_class_stats.py` to regenerate `class_stats_memory_map.json`. Use the `regular_format` / `anomaly` fields on battle-req entries when validating a new class mod (especially the Darkling-F sentinel).
- **Working on weapons / shields / accessories:** Run `map_all_equipment.py` to regenerate `equipment_memory_map.json` and the mod-side `Mods/Equipment-Editor/equipment.json`. Remember the shield AT/DF swap, the HP/10 encoding, and that only `effect_chance` is patchable (not the effect itself).
- **Working on monster names / stats / skills / magic:** Run `map_all_monsters.py` to regenerate `monsters_memory_map.json` and the mod-side `Mods/Monsters-Editor/monsters.json`. Remember the SP-before-MG stats swap, and that drops are not yet patchable.
