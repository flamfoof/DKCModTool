# DKCModTool v2.0

A Python-based modding toolkit for **Dokapon Kingdom: Connect** (Steam/PC).  
Replaces the outdated DKCedit with a dynamic, version-independent tool that works with the Chinese language update and beyond.

## Why This Exists

The original DKCedit had all PE offsets **hardcoded** for a specific version of `DkkStm.exe`. After the Chinese language update, the exe gained 2 new PE sections and grew by ~500KB, breaking every hardcoded offset. This tool reads PE headers **dynamically** and requires no hardcoded addresses for the exe.

## Requirements

- **Python 3.8+** (no external packages needed — stdlib only)

## Quick Start

```bash
# Analyze the current exe structure
python dkc_mod_tool.py analyze-exe path/to/DkkStm.exe

# Extract game data from a stageBase_EN.DAT to editable JSON
python dkc_mod_tool.py extract path/to/stageBase_EN.DAT output.json

# View the extracted data in the terminal
python dkc_mod_tool.py analyze-dat path/to/stageBase_EN.DAT

# Apply edited JSON back to create a modded DAT file
python dkc_mod_tool.py apply path/to/stageBase_EN.DAT output.json modded_stageBase_EN.DAT

# --- DLL-based mod pipeline (preferred) --------------------------------
# Create a DkkStm_modded.exe sibling with ASLR + CFG disabled
python dkc_mod_tool.py make-modded-exe path/to/DkkStm.exe

# Deploy the dinput8.dll proxy into the game folder
python dkc_mod_tool.py deploy-dll path/to/DkkStm.exe

# Uninstall the proxy DLL and restore any prior dinput8.dll
python dkc_mod_tool.py remove-dll path/to/DkkStm.exe

# --- Legacy EXE-patching (kept for backwards compatibility) ------------
# Read an existing .hex patch file
python dkc_mod_tool.py read-hex path/to/patch.hex

# Add the .dkcedit section to the exe for code mods
python dkc_mod_tool.py patch-exe path/to/DkkStm.exe

# Inject a compiled code mod
python dkc_mod_tool.py inject path/to/DkkStm.exe path/to/mod_folder/

# Generate a .hex patch from two files
python dkc_mod_tool.py diff original_file modified_file output.hex

# Scan a DAT file for text strings
python dkc_mod_tool.py scan-strings path/to/stageBase_EN.DAT

# Hex dump a region of any file
python dkc_mod_tool.py hexdump path/to/file 0x1884E 64
```

## Commands

| Command | Description |
|---------|-------------|
| `analyze-exe` | Display full PE structure analysis of DkkStm.exe |
| `analyze-dat` | Display all known game data from a stageBase DAT file |
| `extract` | Export game data to an editable JSON file |
| `apply` | Apply edits from a JSON file back to a DAT file |
| `make-modded-exe` | Copy `DkkStm.exe` to `DkkStm_modded.exe` with ASLR + CFG disabled |
| `deploy-dll` | Deploy `dinput8.dll` proxy into the game folder for runtime patches |
| `remove-dll` | Remove the deployed proxy DLL and restore any pre-existing `.bak` |
| `patch-exe` *(legacy)* | Add the `.dkcedit` section to the exe for code injection |
| `inject` *(legacy)* | Inject a compiled `mod.bin` into a patched exe |
| `diff` | Generate a `.hex` patch file from the differences between two files |
| `read-hex` | Display the contents of a `.hex` patch file |
| `scan-strings` | Find all ASCII strings in a DAT file |
| `hexdump` | Show a hex dump of a file region |

## DLL-based Mod Pipeline (v2.1+)

As of April 2026 the default `DKCModInstaller` workflow no longer writes
to `DkkStm.exe`. Instead:

1. **First-time game-dir setup** creates `<stem>_modded.exe` alongside the
   original with `DYNAMIC_BASE` + `HIGH_ENTROPY_VA` + `GUARD_CF` cleared in
   the PE `DllCharacteristics` field. The image then always loads at its
   preferred `ImageBase` (`0x140000000`), making heap-scan anchors and
   VA-based RE notes stable across launches.
2. **Install-time** deploys `Mods/ProxyDLL-Test/build/dinput8.dll` into the
   game folder along with a renamed system `dinput8_real.dll`. The proxy
   hooks process init, scans the private heap for decompressed DAT data
   (anchored on the `"Thule"` string), and applies runtime patches via its
   `runtime_patcher` module.
3. **Asset mods** (CPK replacement + loose-file overrides) run unchanged --
   those modify game data, not the executable.

Legacy `.hex` and code-mod payloads are skipped by default. Re-run the
installer with `--patch-exe` (or set `DKCMOD_PATCH_EXE=1`) to apply them
the old way. Porting those payloads to the proxy DLL is the preferred
long-term path.

Launch the game via `DkkStm_modded.exe` for a deterministic memory layout
(recommended for any debugger / RE work), or just use the normal Steam
launcher if you only need the proxy DLL's runtime patches plus asset mods.

## Editable Game Data (stageBase_EN.DAT)

The `extract` command exports these known data tables to JSON:

- **Bag Slots** — Item/magic slot counts per class (male & female variants)
- **Level-Up Bonuses** — ATT/DEF/MAG/SPD/HP per class per level
- **Status Effects** — Duration ranges (Squeeze, Petrify, Sealed, Invisible)
- **Damage Formulas** — Display text for battle damage calculations
- **Enemy Data** — Defense magic, attack magic, skills for ~30 enemies
- **Shop Data** — Item IDs sold in each shop
- **Items** — Names, prices, flags, descriptions for known items
- **Equipment** — Percentage values, stat bonuses, class requirements
- **AI Assignments** — Monster AI table references
- **AI Weight Tables** — Attack/Defend/Magic weight distributions

### Class Order (Internal)

| Index | Class | Index | Class |
|-------|-------|-------|-------|
| 0 | Warrior | 6 | Ninja |
| 1 | Magician | 7 | Monk |
| 2 | Thief | 8 | Acrobat |
| 3 | Cleric | 9 | Robo Knight |
| 4 | Spellsword | 10 | Hero |
| 5 | Alchemist | 11 | Darkling |

## PE Patching (Code Mods)

The `patch-exe` command dynamically:
1. Reads the current PE headers to find correct offsets
2. Adds a `.dkcedit` section at the end of the file
3. Updates the section count, image size, and section headers
4. Works with **any** version of DkkStm.exe — no hardcoded offsets

The `inject` command loads a `mod.bin` + `variables.txt` + `functions.txt` (same format as original DKCedit) into the patched section.

## .hex File Format

The ConnectModInstaller uses a custom .hex format:
```
8 bytes (big-endian): File offset
8 bytes (big-endian): Size of data
N bytes: Data to write at offset
... repeat ...
```
Use `read-hex` to inspect existing patches, or `diff` to generate new ones.

## Workflow: Creating a Balance Mod

1. **Extract** the original stageBase_EN.DAT from the game's CPK archives
2. **Export** to JSON: `python dkc_mod_tool.py extract stageBase_EN.DAT mymod.json`
3. **Edit** `mymod.json` — change bag sizes, level-up stats, enemy magic, etc.
4. **Apply** changes: `python dkc_mod_tool.py apply stageBase_EN.DAT mymod.json modded_stageBase_EN.DAT`
5. **Place** `modded_stageBase_EN.DAT` in your mod's Assets folder (named `stageBase_EN.DAT`)
6. Use the ConnectModInstaller to install your mod

## Workflow: Creating an EXE Patch

1. **Analyze** the exe: `python dkc_mod_tool.py analyze-exe DkkStm.exe`
2. **Patch** the exe: `python dkc_mod_tool.py patch-exe DkkStm.exe`
3. **Inject** your code mod: `python dkc_mod_tool.py inject DkkStm.exe ./my_mod/`

## File Structure

```
DKCModTool/
├── dkc_mod_tool.py        # Main CLI entry point
├── mod_installer.py       # Install pipeline (DLL-first, CPK assets, legacy EXE flags)
├── pe_patcher.py          # PE file analysis, section injection, DllCharacteristics patching
├── stagebase_parser.py    # stageBase_EN.DAT parser and editor
├── data_tables.py         # Known data structure definitions
├── hex_gen.py             # .hex patch file generation and reading
├── cpk_tools.py           # CPK archive read/replace for asset mods
├── analysis_tools/        # RE mappers (equipment, monsters, class stats, skills)
│                          # See analysis_tools/README.md for details
└── README.md              # This file
```

## Credits

- Original DKCedit by [Purrygamer](https://github.com/Purrygamer/DKCedit)
- Data offsets derived from JaJo's Balance Patch changelog
- ConnectModInstaller by the Dokapon Kingdom modding community
