#!/usr/bin/env python3
"""
DKCModTool - Dokapon Kingdom: Connect Modding Toolkit v2.0
A replacement for DKCedit that dynamically handles any version of DkkStm.exe
and provides full game data extraction and editing.

Usage:
    python dkc_mod_tool.py <command> [options]

Commands:
    analyze-exe <exe_path>              Analyze PE structure of DkkStm.exe
    analyze-dat <dat_path>              Analyze a stageBase .DAT file
    extract <dat_path> [output.json]    Extract game data to JSON
    apply <dat_path> <input.json> [out] Apply JSON edits to a DAT file
    patch-exe <exe_path>                Add .dkcedit section to exe
    inject <exe_path> <mod_dir>         Inject a code mod into patched exe
    diff <original> <modified> [out]    Generate .hex patch from two files
    read-hex <hex_file>                 Describe a .hex patch file
    scan-strings <dat_path> [min_len]   Scan a DAT file for text strings
    hexdump <file> <offset> <length>    Hex dump a region of a file
"""
import sys
import os
import struct
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stagebase_parser import StageBaseParser
from pe_patcher import PEPatcher
from hex_gen import HexGenerator, diff_to_hex


def cmd_analyze_exe(args):
    if len(args) < 1:
        print("Usage: analyze-exe <exe_path>")
        return
    pe = PEPatcher(args[0])
    info = pe.get_info()
    
    print(f"\n{'='*60}")
    print(f" DkkStm.exe PE Analysis")
    print(f"{'='*60}")
    print(f"File:              {info['file_path']}")
    print(f"File size:         {info['file_size']} bytes (0x{info['file_size']:X})")
    print(f"PE type:           {info['pe_type']}")
    print(f"Image base:        {info['image_base']}")
    print(f"Section alignment: {info['section_alignment']}")
    print(f"File alignment:    {info['file_alignment']}")
    print(f"Image size:        {info['image_size']}")
    print(f"Sections:          {info['num_sections']}")
    print(f"Already modded:    {'YES' if info['has_dkcedit_section'] else 'No'}")
    print(f"Can add section:   {'YES' if info['can_add_section'] else 'NO (not enough header space!)'}")
    
    print(f"\n{'Name':<12} {'VirtAddr':>10} {'VirtSize':>10} {'RawAddr':>10} {'RawSize':>10}")
    print("-" * 58)
    for s in info['sections']:
        print(f"{s['name']:<12} {s['virtual_address']:>10} {s['virtual_size']:>10} {s['raw_address']:>10} {s['raw_size']:>10}")
    
    print(f"\nNext virtual address: {info['next_virtual_address']}")
    print(f"Next raw address:     {info['next_raw_address']}")
    print(f"Header space left:    {info['header_space_available']} bytes")
    
    if info['has_dkcedit_section']:
        mod_info = pe.get_mod_section_info()
        if mod_info:
            print(f"\n--- .dkcedit Section Info ---")
            print(f"Space used:      {mod_info['space_used']} bytes")
            print(f"Space available: {mod_info['available_space']} bytes")
            print(f"Code start (raw):  0x{mod_info['code_start_raw']:X}")
            print(f"Code start (virt): 0x{mod_info['code_start_virt']:X}")
    
    # Save full info to JSON
    json_path = args[0] + ".analysis.json"
    pe.export_info_json(json_path)
    print(f"\nFull analysis saved to: {json_path}")


def cmd_analyze_dat(args):
    if len(args) < 1:
        print("Usage: analyze-dat <dat_path>")
        return
    parser = StageBaseParser(args[0])
    data = parser.export_all()
    
    print(f"\n{'='*60}")
    print(f" stageBase Data Analysis")
    print(f"{'='*60}")
    print(f"File: {data['file_info']['path']}")
    print(f"Size: {data['file_info']['size']} bytes")
    
    print(f"\n--- Bag Slots (Item/Magic) ---")
    for bag in data['bags']:
        print(f"  {bag['class']:<14} ({bag['variant']:<6}): {bag['item_slots']}/{bag['magic_slots']} (cap {bag['total_cap']})")
    
    print(f"\n--- Level-Up Bonuses ---")
    for entry in data['level_ups']:
        s = entry['stats']
        print(f"  {entry['class']:<14} ({entry['variant']:<6}): "
              f"ATT+{s['attack']} DEF+{s['defense']} MAG+{s['magic']} SPD+{s['speed']} HP+{s['hp']}")
    
    print(f"\n--- Status Effects ---")
    for name, effect in data['status_effects'].items():
        dur = f"{effect.get('min_duration','?')}-{effect.get('max_duration','?')}"
        print(f"  {name:<12}: {dur} turns")
    
    print(f"\n--- Damage Formulas ---")
    for name, formula in data['damage_formulas'].items():
        print(f"  {name:<14}: '{formula['text']}'")
    
    print(f"\n--- Enemy Defense Magic ---")
    for name, enemy in data['enemies'].items():
        parts = []
        if 'def_magic' in enemy:
            parts.append(f"DefMagic={enemy['def_magic']}")
        if 'atk_magic' in enemy:
            parts.append(f"AtkMagic={enemy['atk_magic']}")
        if 'skill' in enemy:
            parts.append(f"Skill={enemy['skill']}")
        if parts:
            print(f"  {name:<22}: {', '.join(parts)}")
    
    print(f"\n--- Known Items ---")
    for name, item in data['items'].items():
        parts = []
        if 'display_name' in item:
            parts.append(f"Name='{item['display_name']}'")
        if 'price' in item:
            parts.append(f"Price={item['price']:,}")
        if 'flags_desc' in item:
            parts.append(f"Flags={item['flags_desc']}")
        print(f"  {name}: {', '.join(parts)}")
    
    print(f"\n--- Equipment ---")
    for name, equip in data['equipment'].items():
        parts = []
        if 'percentage' in equip:
            parts.append(f"{equip['percentage']}%")
        if 'class_req' in equip:
            parts.append(f"Req={equip['class_req']}")
        if 'stats' in equip:
            s = equip['stats']
            parts.append(f"Stats: ATT+{s['attack']} DEF+{s['defense']} MAG+{s['magic']} SPD+{s['speed']} HP+{s['hp']}")
        print(f"  {name}: {', '.join(parts)}")


def cmd_extract(args):
    if len(args) < 1:
        print("Usage: extract <dat_path> [output.json]")
        return
    dat_path = args[0]
    json_path = args[1] if len(args) > 1 else os.path.splitext(dat_path)[0] + "_data.json"
    
    parser = StageBaseParser(dat_path)
    parser.export_json(json_path)
    print(f"[+] Extracted game data to: {json_path}")
    print(f"    Edit the JSON file, then use 'apply' to write changes back.")


def cmd_apply(args):
    if len(args) < 2:
        print("Usage: apply <dat_path> <input.json> [output_dat]")
        return
    dat_path = args[0]
    json_path = args[1]
    out_path = args[2] if len(args) > 2 else dat_path
    
    if out_path == dat_path:
        confirm = input(f"This will overwrite {dat_path}. Continue? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return
    
    parser = StageBaseParser(dat_path)
    changes = parser.import_json(json_path)
    parser.save(out_path)
    
    print(f"[+] Applied {len(changes)} changes to: {out_path}")
    for change in changes:
        print(f"    {change}")


def cmd_patch_exe(args):
    if len(args) < 1:
        print("Usage: patch-exe <exe_path> [output_path]")
        return
    exe_path = args[0]
    out_path = args[1] if len(args) > 1 else exe_path
    
    if out_path == exe_path:
        confirm = input(f"This will modify {exe_path} in-place. Continue? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return
    
    pe = PEPatcher(exe_path)
    result = pe.add_mod_section(section_size=0x4000)  # 16KB for mods
    pe.save(out_path)
    
    # Save section info for reference
    info_path = out_path + ".modinfo.json"
    with open(info_path, 'w') as f:
        json.dump({k: (f"0x{v:X}" if isinstance(v, int) else v) for k, v in result.items()}, f, indent=2)
    print(f"[+] Mod section info saved to: {info_path}")


def cmd_inject(args):
    if len(args) < 2:
        print("Usage: inject <exe_path> <mod_dir>")
        return
    exe_path = args[0]
    mod_dir = args[1]
    
    mod_bin = os.path.join(mod_dir, "mod.bin")
    variables = os.path.join(mod_dir, "variables.txt")
    functions = os.path.join(mod_dir, "functions.txt")
    
    if not os.path.exists(mod_bin):
        print(f"[!] mod.bin not found in {mod_dir}")
        return
    
    pe = PEPatcher(exe_path)
    pe.inject_mod(mod_bin, variables, functions)
    pe.save(exe_path)


def cmd_diff(args):
    if len(args) < 2:
        print("Usage: diff <original_file> <modified_file> [output.hex]")
        return
    original = args[0]
    modified = args[1]
    output = args[2] if len(args) > 2 else "patch.hex"
    
    gen = diff_to_hex(original, modified, output)
    changelog = gen.generate_changelog()
    print(f"\nChangelog:\n{changelog}")


def cmd_read_hex(args):
    if len(args) < 1:
        print("Usage: read-hex <hex_file>")
        return
    print(HexGenerator.describe_hex_file(args[0]))


def cmd_scan_strings(args):
    if len(args) < 1:
        print("Usage: scan-strings <dat_path> [min_length]")
        return
    dat_path = args[0]
    min_len = int(args[1]) if len(args) > 1 else 4
    
    parser = StageBaseParser(dat_path)
    strings = parser.scan_strings(min_length=min_len)
    
    print(f"Found {len(strings)} strings (min length {min_len}):")
    for s in strings:
        text = s['text'][:80]
        if len(s['text']) > 80:
            text += "..."
        print(f"  {s['offset']}: {text}")


def cmd_hexdump(args):
    if len(args) < 3:
        print("Usage: hexdump <file> <offset> <length>")
        print("  offset and length can be hex (0x...) or decimal")
        return
    filepath = args[0]
    offset = int(args[1], 0)
    length = int(args[2], 0)
    
    with open(filepath, 'rb') as f:
        f.seek(offset)
        data = f.read(length)
    
    for i in range(0, len(data), 16):
        addr = offset + i
        chunk = data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"  0x{addr:06X}: {hex_str:<48} {ascii_str}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    commands = {
        "analyze-exe": cmd_analyze_exe,
        "analyze-dat": cmd_analyze_dat,
        "extract": cmd_extract,
        "apply": cmd_apply,
        "patch-exe": cmd_patch_exe,
        "inject": cmd_inject,
        "diff": cmd_diff,
        "read-hex": cmd_read_hex,
        "scan-strings": cmd_scan_strings,
        "hexdump": cmd_hexdump,
    }
    
    if command in commands:
        try:
            commands[command](args)
        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(commands.keys())}")


if __name__ == "__main__":
    main()
