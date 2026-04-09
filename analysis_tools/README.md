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

## When to Use These

- **After a game update:** Run `analyze_exe.py` to check if the PE layout changed.
- **Mapping new data:** Run `analyze_records.py` with adjusted offsets to hex-dump unknown regions.
- **Finding strings:** Run `analyze_data.py` to locate game text (item names, descriptions, etc.).
- **Verifying mod offsets:** Compare hex dumps against your changelog entries.
