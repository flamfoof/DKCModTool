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
| `patch-exe` | Add the .dkcedit section to the exe for code injection |
| `inject` | Inject a compiled mod.bin into a patched exe |
| `diff` | Generate a .hex patch file from the differences between two files |
| `read-hex` | Display the contents of a .hex patch file |
| `scan-strings` | Find all ASCII strings in a DAT file |
| `hexdump` | Show a hex dump of a file region |

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
├── pe_patcher.py          # PE file analysis and section injection
├── stagebase_parser.py    # stageBase_EN.DAT parser and editor
├── data_tables.py         # Known data structure definitions
├── hex_gen.py             # .hex patch file generation and reading
└── README.md              # This file
```

## Credits

- Original DKCedit by [Purrygamer](https://github.com/Purrygamer/DKCedit)
- Data offsets derived from JaJo's Balance Patch changelog
- ConnectModInstaller by the Dokapon Kingdom modding community
