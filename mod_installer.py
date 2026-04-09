#!/usr/bin/env python3
"""
DKCModTool Installer - Dokapon Kingdom: Connect Mod Installer
Applies mods from the Mods/ folder to the game installation.

Handles:
  - Asset replacement (files injected into CPK archives)
  - Hex edits (raw binary patches to the exe)
  - Code mods (PE section injection via .dkcedit)
"""
import os
import sys
import shutil
import struct
import glob
import time
import traceback

# Ensure we can import sibling modules when running as .exe
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# When packaged, the tool lives alongside Mods/ and Backup/
# Navigate up one level if we're inside DKCModTool/
if os.path.basename(SCRIPT_DIR).lower() == 'dkcmodtool':
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
else:
    ROOT_DIR = SCRIPT_DIR

sys.path.insert(0, SCRIPT_DIR)

from pe_patcher import PEPatcher
from hex_gen import HexGenerator
from cpk_tools import CPKFile

BACKUP_DIR = os.path.join(ROOT_DIR, "Backup")
MODS_DIR = os.path.join(ROOT_DIR, "Mods")
GAME_EXE_FILE = os.path.join(BACKUP_DIR, "game_exe.txt")

# Known CPK files and their backup locations
CPK_FILES = ["CommonData.cpk", "CommonData100.cpk", "CommonData2.cpk", "Data_eng.cpk"]
# DLLs to back up alongside the exe
DLL_FILES = ["SDL2.dll", "glew32.dll", "steam_api64.dll"]


# ============================================================================
# Console Helpers
# ============================================================================

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_step(text):
    print(f"\n>> {text}")


def print_ok(text):
    print(f"   [OK] {text}")


def print_warn(text):
    print(f"   [!!] {text}")


def print_err(text):
    print(f"   [ERROR] {text}")


def print_info(text):
    print(f"   {text}")


# ============================================================================
# Game Path Detection
# ============================================================================

def find_game_exe():
    """
    Find the game executable path.
    1. Check Backup/game_exe.txt
    2. If not found or invalid, open a Windows file dialog
    3. If dialog cancelled, prompt for manual path entry
    """
    # 1. Try existing path
    if os.path.exists(GAME_EXE_FILE):
        with open(GAME_EXE_FILE, 'r') as f:
            path = f.read().strip()
        if path and os.path.isfile(path):
            print_ok(f"Found game exe: {path}")
            return path
        else:
            print_warn(f"Saved path not found: {path}")
    
    # 2. Try Windows file dialog
    print_step("Game executable not found. Opening file browser...")
    path = _open_file_dialog()
    
    if path and os.path.isfile(path):
        _save_game_path(path)
        return path
    
    # 3. Manual entry fallback
    print_info("File browser cancelled or unavailable.")
    print_info("Please enter the full path to DkkStm.exe:")
    print_info("(Usually: C:\\...\\steamapps\\common\\Dokapon Kingdom Connect\\DkkStm.exe)")
    
    while True:
        path = input("\n   Path: ").strip().strip('"').strip("'")
        if not path:
            return None
        if os.path.isfile(path):
            _save_game_path(path)
            return path
        print_warn(f"File not found: {path}")
        print_info("Try again, or press Enter to cancel.")


def _open_file_dialog():
    """Open a Windows file dialog to select DkkStm.exe."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Try common Steam paths as initial directory
        initial_dirs = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Dokapon Kingdom Connect",
            r"C:\Program Files\Steam\steamapps\common\Dokapon Kingdom Connect",
            r"D:\SteamLibrary\steamapps\common\Dokapon Kingdom Connect",
            r"E:\SteamLibrary\steamapps\common\Dokapon Kingdom Connect",
            r"H:\SteamLibrary\steamapps\common\Dokapon Kingdom Connect",
        ]
        initial = None
        for d in initial_dirs:
            if os.path.isdir(d):
                initial = d
                break
        
        path = filedialog.askopenfilename(
            title="Select DkkStm.exe (Dokapon Kingdom Connect)",
            filetypes=[("Game Executable", "DkkStm.exe"), ("All Executables", "*.exe"), ("All files", "*.*")],
            initialdir=initial,
        )
        root.destroy()
        return path if path else None
    except Exception as e:
        print_warn(f"Could not open file dialog: {e}")
        return None


def _save_game_path(path):
    """Save the game exe path for future use."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(GAME_EXE_FILE, 'w') as f:
        f.write(path)
    print_ok(f"Game path saved: {path}")


# ============================================================================
# Backup & Restore
# ============================================================================

def backup_game_files(exe_path):
    """Back up original game files before modding."""
    print_step("Checking backups...")
    game_dir = os.path.dirname(exe_path)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    assets_dir = os.path.join(BACKUP_DIR, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # Backup exe
    backup_exe = os.path.join(BACKUP_DIR, os.path.basename(exe_path))
    if not os.path.exists(backup_exe):
        print_info(f"Backing up {os.path.basename(exe_path)}...")
        shutil.copy2(exe_path, backup_exe)
        print_ok("Executable backed up")
    else:
        print_ok("Executable backup exists")
    
    # Backup DLLs
    for dll in DLL_FILES:
        src = os.path.join(game_dir, dll)
        dst = os.path.join(BACKUP_DIR, dll)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
    
    # Backup CPK files
    for cpk in CPK_FILES:
        src = os.path.join(game_dir, cpk)
        dst = os.path.join(assets_dir, cpk)
        if os.path.exists(src) and not os.path.exists(dst):
            print_info(f"Backing up {cpk} ({os.path.getsize(src) // (1024*1024)}MB)...")
            shutil.copy2(src, dst)
            print_ok(f"{cpk} backed up")
        elif os.path.exists(dst):
            print_ok(f"{cpk} backup exists")


def check_files_writable(exe_path):
    """Check that game files aren't locked (e.g., game is running)."""
    game_dir = os.path.dirname(exe_path)
    files_to_check = [exe_path]
    for cpk in CPK_FILES:
        p = os.path.join(game_dir, cpk)
        if os.path.exists(p):
            files_to_check.append(p)
    
    for fpath in files_to_check:
        try:
            with open(fpath, 'r+b'):
                pass
        except PermissionError:
            return False, os.path.basename(fpath)
        except FileNotFoundError:
            pass
    return True, None


def restore_from_backup(exe_path):
    """Restore game files from backup to start fresh before applying mods."""
    print_step("Restoring from backup...")
    game_dir = os.path.dirname(exe_path)
    
    # Restore exe
    backup_exe = os.path.join(BACKUP_DIR, os.path.basename(exe_path))
    if os.path.exists(backup_exe):
        try:
            shutil.copy2(backup_exe, exe_path)
            print_ok("Executable restored")
        except PermissionError:
            print_err(f"Cannot write to {exe_path} - is the game running?")
            print_info("Close the game and try again.")
            return False
    else:
        print_warn("No exe backup found - working with current exe")
    
    # Restore CPKs
    assets_dir = os.path.join(BACKUP_DIR, "assets")
    for cpk in CPK_FILES:
        src = os.path.join(assets_dir, cpk)
        dst = os.path.join(game_dir, cpk)
        if os.path.exists(src):
            print_info(f"Restoring {cpk}...")
            try:
                shutil.copy2(src, dst)
                print_ok(f"{cpk} restored")
            except PermissionError:
                print_err(f"Cannot write to {cpk} - is the game running?")
                return False
    return True


# ============================================================================
# Mod Discovery
# ============================================================================

def discover_mods():
    """Scan the Mods/ directory for installable mods."""
    if not os.path.isdir(MODS_DIR):
        print_warn(f"Mods directory not found: {MODS_DIR}")
        return []
    
    mods = []
    for entry in os.listdir(MODS_DIR):
        mod_path = os.path.join(MODS_DIR, entry)
        if os.path.isdir(mod_path):
            mod = {
                'name': entry,
                'path': mod_path,
                'assets': [],
                'hex_edits': [],
                'code_mods': [],
            }
            
            # Find asset files
            assets_dir = os.path.join(mod_path, "Assets")
            if os.path.isdir(assets_dir):
                for root, dirs, files in os.walk(assets_dir):
                    for fname in files:
                        mod['assets'].append(os.path.join(root, fname))
            
            # Find hex edit files
            hex_dir = os.path.join(mod_path, "Hex")
            if os.path.isdir(hex_dir):
                for root, dirs, files in os.walk(hex_dir):
                    for fname in files:
                        if fname.lower().endswith('.hex'):
                            mod['hex_edits'].append(os.path.join(root, fname))
            
            # Find code mods
            codes_dir = os.path.join(mod_path, "Codes")
            if os.path.isdir(codes_dir):
                for code_entry in os.listdir(codes_dir):
                    code_path = os.path.join(codes_dir, code_entry)
                    if os.path.isdir(code_path):
                        mod_bin = os.path.join(code_path, "mod.bin")
                        if os.path.exists(mod_bin):
                            mod['code_mods'].append({
                                'name': code_entry,
                                'path': code_path,
                                'mod_bin': mod_bin,
                                'variables': os.path.join(code_path, "variables.txt"),
                                'functions': os.path.join(code_path, "functions.txt"),
                            })
            
            if mod['assets'] or mod['hex_edits'] or mod['code_mods']:
                mods.append(mod)
    
    return mods


# ============================================================================
# Mod Application
# ============================================================================

def apply_hex_edits(exe_path, hex_files):
    """Apply all .hex patches to the game executable."""
    if not hex_files:
        return 0
    
    total_patches = 0
    with open(exe_path, 'r+b') as f:
        exe_size = f.seek(0, 2)
        for hex_file in hex_files:
            patches = HexGenerator.read_hex_file(hex_file)
            hex_name = os.path.basename(hex_file)
            for patch in patches:
                if patch.offset + len(patch.data) > exe_size:
                    print_warn(f"{hex_name}: Offset 0x{patch.offset:X} exceeds exe size, skipped")
                    continue
                f.seek(patch.offset)
                f.write(patch.data)
                total_patches += 1
            print_ok(f"{hex_name}: {len(patches)} patches applied")
    
    return total_patches


def apply_code_mods(exe_path, code_mods):
    """Inject code mods into the game executable via PE section injection."""
    if not code_mods:
        return 0
    
    pe = PEPatcher(exe_path)
    
    # Add .dkcedit section if not present
    if not pe.is_modded():
        pe.add_mod_section(section_size=0x4000)
        pe.save(exe_path)
        pe = PEPatcher(exe_path)  # Reload
    
    count = 0
    for mod in code_mods:
        try:
            pe.inject_mod(mod['mod_bin'], mod['variables'], mod['functions'])
            print_ok(f"Code mod '{mod['name']}' injected")
            count += 1
        except Exception as e:
            print_err(f"Code mod '{mod['name']}' failed: {e}")
    
    pe.save(exe_path)
    return count


def apply_asset_mods(exe_path, asset_files):
    """Replace asset files in the game's CPK archives."""
    if not asset_files:
        return 0
    
    game_dir = os.path.dirname(exe_path)
    
    # Build a map of filename -> asset path
    assets_to_install = {}
    for asset_path in asset_files:
        fname = os.path.basename(asset_path)
        if fname in assets_to_install:
            print_warn(f"Duplicate asset: {fname} (using first found)")
            continue
        assets_to_install[fname] = asset_path
    
    # Try to install each asset into the CPK files
    installed = 0
    not_found = []
    
    for cpk_name in CPK_FILES:
        cpk_path = os.path.join(game_dir, cpk_name)
        if not os.path.exists(cpk_path):
            continue
        
        # Check if any of our assets are in this CPK
        try:
            cpk = CPKFile(cpk_path)
        except Exception as e:
            print_err(f"Failed to open {cpk_name}: {e}")
            continue
        
        cpk_filenames = {f['name'].lower(): f['name'] for f in cpk.files}
        
        for asset_name, asset_path in list(assets_to_install.items()):
            if asset_name.lower() in cpk_filenames:
                try:
                    result = cpk.replace_file(asset_name, asset_path)
                    if result:
                        print_ok(f"Asset '{asset_name}' -> {cpk_name}")
                        installed += 1
                        del assets_to_install[asset_name]
                    else:
                        print_err(f"Failed to replace '{asset_name}' in {cpk_name}")
                except Exception as e:
                    print_err(f"Error replacing '{asset_name}' in {cpk_name}: {e}")
    
    # Report any assets that weren't found in any CPK
    for name in assets_to_install:
        print_warn(f"Asset '{name}' not found in any CPK archive")
    
    return installed


# ============================================================================
# Main Installer Flow
# ============================================================================

def run_installer():
    """Main installation flow."""
    print_header("DKCModTool Installer v2.0")
    print_info("Dokapon Kingdom: Connect Mod Installer")
    print_info(f"Root: {ROOT_DIR}")
    
    # 1. Find game exe
    print_step("Locating game executable...")
    exe_path = find_game_exe()
    if not exe_path:
        print_err("No game executable selected. Aborting.")
        return False
    
    # 2. Discover mods
    print_step("Scanning for mods...")
    mods = discover_mods()
    if not mods:
        print_warn("No mods found in Mods/ directory.")
        return False
    
    print_info(f"Found {len(mods)} mod(s):")
    total_assets = 0
    total_hex = 0
    total_codes = 0
    for mod in mods:
        na = len(mod['assets'])
        nh = len(mod['hex_edits'])
        nc = len(mod['code_mods'])
        total_assets += na
        total_hex += nh
        total_codes += nc
        print_info(f"  [{mod['name']}] {na} assets, {nh} hex edits, {nc} code mods")
    
    print_info(f"\n   Total: {total_assets} assets, {total_hex} hex edits, {total_codes} code mods")
    
    # 3. Backup
    backup_game_files(exe_path)
    
    # 4. Check files are writable
    print_step("Checking file access...")
    writable, locked_file = check_files_writable(exe_path)
    if not writable:
        print_err(f"Cannot write to {locked_file} - is the game running?")
        print_info("Close the game and any programs using it, then try again.")
        return False
    print_ok("All game files are writable")
    
    # 5. Restore from backup (fresh start)
    if not restore_from_backup(exe_path):
        return False
    
    # 5. Apply mods in order: hex edits -> code mods -> assets
    # (Hex edits first, as they patch the raw exe before code injection)
    
    # Hex edits
    all_hex = []
    for mod in mods:
        all_hex.extend(mod['hex_edits'])
    if all_hex:
        print_step(f"Applying {len(all_hex)} hex edit file(s)...")
        apply_hex_edits(exe_path, all_hex)
    
    # Code mods
    all_codes = []
    for mod in mods:
        all_codes.extend(mod['code_mods'])
    if all_codes:
        print_step(f"Injecting {len(all_codes)} code mod(s)...")
        apply_code_mods(exe_path, all_codes)
    
    # Asset mods
    all_assets = []
    for mod in mods:
        all_assets.extend(mod['assets'])
    if all_assets:
        print_step(f"Installing {len(all_assets)} asset file(s)...")
        apply_asset_mods(exe_path, all_assets)
    
    print_header("Installation Complete!")
    return True


def main():
    try:
        success = run_installer()
    except Exception as e:
        print_err(f"Unexpected error: {e}")
        traceback.print_exc()
        success = False
    
    print("\n")
    if success:
        print("   Done! You can now launch the game.")
    else:
        print("   Installation did not complete successfully.")
    
    print("\n   Press Enter to exit...")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
