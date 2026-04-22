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
import tempfile
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
MODDED_EXE_FILE = os.path.join(BACKUP_DIR, "modded_exe.txt")

# Known CPK files and their backup locations
CPK_FILES = ["CommonData.cpk", "CommonData100.cpk", "CommonData2.cpk", "Data_eng.cpk"]
# DLLs to back up alongside the exe
DLL_FILES = ["SDL2.dll", "glew32.dll", "steam_api64.dll"]
# Manifest tracking loose file overrides placed in the game directory
OVERRIDES_MANIFEST = os.path.join(BACKUP_DIR, "overrides.txt")

# Proxy DLL deployment
# Source built by Mods/ProxyDLL-Test/build.bat; see that mod's README for
# runtime-patcher design. The installer deploys this DLL to the game folder
# as the mod delivery vector (replacing direct EXE hex/code patching).
PROXY_DLL_SRC      = os.path.join(MODS_DIR, "ProxyDLL-Test", "build", "dinput8.dll")
PROXY_DLL_NAME     = "dinput8.dll"       # name the game loads
PROXY_REAL_NAME    = "dinput8_real.dll"  # the renamed system DLL our proxy forwards to
SYSTEM_DINPUT8     = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                                  "System32", "dinput8.dll")

# Modded-EXE suffix. DKCModInstaller creates <stem>_modded.exe alongside the
# original on first-time game-dir setup, with ASLR + CFG disabled so heap
# scanning + VA-based RE notes stay stable across launches.
MODDED_EXE_SUFFIX  = "_modded"


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
    """Save the game exe path and trigger first-time setup.

    On first save (i.e. the path was not already persisted) we also create
    a `<stem>_modded.exe` sibling with ASLR + CFG disabled, so the proxy
    DLL's memory scanner sees a stable image base on every launch.
    """
    is_first_time = not os.path.exists(GAME_EXE_FILE)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(GAME_EXE_FILE, 'w') as f:
        f.write(path)
    print_ok(f"Game path saved: {path}")

    # First-time setup: create the modded exe alongside the original.
    # Safe to call on re-runs too (create_modded_exe is idempotent), but we
    # only advertise it the first time to keep the UX clean.
    if is_first_time:
        print_info("First-time setup: preparing modded executable.")
    create_modded_exe(path)


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
    
    # Backup CPK files (check both root and assets/ subdirectory)
    for cpk in CPK_FILES:
        dst = os.path.join(assets_dir, cpk)
        if os.path.exists(dst):
            print_ok(f"{cpk} backup exists")
            continue
        # Prefer the assets/ subdirectory copy as the source
        src_assets = os.path.join(game_dir, "assets", cpk)
        src_root = os.path.join(game_dir, cpk)
        src = src_assets if os.path.exists(src_assets) else src_root
        if os.path.exists(src):
            print_info(f"Backing up {cpk} ({os.path.getsize(src) // (1024*1024)}MB)...")
            shutil.copy2(src, dst)
            print_ok(f"{cpk} backed up")
        else:
            print_warn(f"{cpk} not found in game directory")


def check_files_writable(exe_path):
    """Check that game files aren't locked (e.g., game is running)."""
    game_dir = os.path.dirname(exe_path)
    files_to_check = [exe_path]
    for cpk in CPK_FILES:
        p = os.path.join(game_dir, cpk)
        if os.path.exists(p):
            files_to_check.append(p)
        p_assets = os.path.join(game_dir, "assets", cpk)
        if os.path.exists(p_assets):
            files_to_check.append(p_assets)
    
    for fpath in files_to_check:
        try:
            with open(fpath, 'r+b'):
                pass
        except PermissionError:
            return False, os.path.basename(fpath)
        except FileNotFoundError:
            pass
    return True, None


def clean_overrides(game_dir):
    """Remove loose file overrides placed by a previous install."""
    if not os.path.exists(OVERRIDES_MANIFEST):
        return
    with open(OVERRIDES_MANIFEST, 'r') as f:
        paths = [line.strip() for line in f if line.strip()]
    removed = 0
    for path in paths:
        if os.path.isfile(path):
            os.remove(path)
            removed += 1
    # Remove empty directories (deepest first)
    dirs = set(os.path.dirname(p) for p in paths)
    for d in sorted(dirs, key=len, reverse=True):
        try:
            if os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
        except OSError:
            pass
    os.remove(OVERRIDES_MANIFEST)
    if removed:
        print_ok(f"Removed {removed} loose file override(s)")


def restore_from_backup(exe_path):
    """Restore game files from backup to start fresh before applying mods."""
    print_step("Restoring from backup...")
    game_dir = os.path.dirname(exe_path)
    
    # Clean up loose file overrides from previous install
    clean_overrides(game_dir)
    
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
    
    # Restore CPKs to both root and assets/ subdirectory
    assets_dir = os.path.join(BACKUP_DIR, "assets")
    for cpk in CPK_FILES:
        src = os.path.join(assets_dir, cpk)
        if not os.path.exists(src):
            continue
        # Restore to root
        dst_root = os.path.join(game_dir, cpk)
        # Restore to assets/ subdirectory (if it exists)
        dst_assets = os.path.join(game_dir, "assets", cpk)
        destinations = [dst_root]
        if os.path.isdir(os.path.join(game_dir, "assets")):
            destinations.append(dst_assets)
        print_info(f"Restoring {cpk}...")
        for dst in destinations:
            try:
                shutil.copy2(src, dst)
            except PermissionError:
                print_err(f"Cannot write to {dst} - is the game running?")
                return False
        print_ok(f"{cpk} restored")
    return True


# ============================================================================
# Modded EXE creation  (ASLR / CFG disable)
# ============================================================================

def get_modded_exe_path(exe_path):
    """Compute the sibling "_modded" exe path. E.g.
    .../DkkStm.exe -> .../DkkStm_modded.exe"""
    game_dir = os.path.dirname(exe_path)
    stem, ext = os.path.splitext(os.path.basename(exe_path))
    return os.path.join(game_dir, f"{stem}{MODDED_EXE_SUFFIX}{ext}")


def _save_modded_path(path):
    """Persist the modded exe path alongside game_exe.txt for other tools."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(MODDED_EXE_FILE, 'w') as f:
        f.write(path)


def create_modded_exe(exe_path, force=False):
    """Create a `<stem>_modded.exe` copy of the original with ASLR and CFG
    disabled.

    Rationale: the heap/memory scanners in our proxy DLL and every VA in the
    RE notes assume the EXE loads at its preferred ImageBase (0x140000000).
    ASLR can relocate that in practice. Disabling `DYNAMIC_BASE` +
    `HIGH_ENTROPY_VA` in DllCharacteristics pins the image base, and clearing
    `GUARD_CF` removes Control Flow Guard runtime checks that can interfere
    with in-memory code patches.

    The original `DkkStm.exe` is left untouched; launch the `_modded` copy
    directly (or swap filenames) to get deterministic layout.

    Returns the modded-exe path on success, None on failure.
    """
    if not os.path.isfile(exe_path):
        print_err(f"Source exe not found: {exe_path}")
        return None

    modded_path = get_modded_exe_path(exe_path)
    already_exists = os.path.exists(modded_path)

    if already_exists and not force:
        # Check whether it's already fully patched; if yes, nothing to do.
        try:
            pe = PEPatcher(modded_path)
            flags = pe.get_dll_characteristics()
            if not (flags & (pe.DLL_CHAR_DYNAMIC_BASE | pe.DLL_CHAR_HIGH_ENTROPY_VA)):
                print_ok(f"Modded exe already present and ASLR-disabled: "
                         f"{os.path.basename(modded_path)}")
                _save_modded_path(modded_path)
                return modded_path
            print_info(f"Modded exe exists but still has ASLR flags "
                       f"(0x{flags:04X}); re-patching.")
        except Exception as e:
            print_warn(f"Could not inspect existing modded exe ({e}); overwriting.")

    print_step(f"Creating modded executable: {os.path.basename(modded_path)}")
    try:
        shutil.copy2(exe_path, modded_path)
    except PermissionError:
        print_err(f"Cannot write to {modded_path} -- is the game running?")
        return None
    except Exception as e:
        print_err(f"Copy failed: {e}")
        return None

    try:
        pe = PEPatcher(modded_path)
        result = pe.patch_for_modding(disable_cfg=True)
        pe.save()
    except Exception as e:
        print_err(f"PE patch failed: {e}")
        traceback.print_exc()
        # Leave the copy in place so the user can investigate.
        return None

    print_ok(f"DllCharacteristics: 0x{result['before']:04X} -> 0x{result['after']:04X}")
    if result['cleared']:
        print_info(f"Cleared flags: {', '.join(result['cleared'])}")
    else:
        print_info("No ASLR/CFG flags were set; modded exe is a plain copy.")
    print_info(f"Modded exe: {modded_path}")
    print_info("Launch this file directly (or swap filenames with the")
    print_info("original) to run with a deterministic memory layout.")

    _save_modded_path(modded_path)
    return modded_path


# ============================================================================
# Proxy DLL deployment  (replaces direct EXE hex/code patching)
# ============================================================================

def deploy_proxy_dll(exe_path):
    """Deploy the dinput8.dll proxy into the game folder.

    The proxy hooks process init, scans the private heap for the decompressed
    stageBase_EN.DAT (anchored on the "Thule" string), and applies runtime
    patches via an opt-in runtime_patcher. This replaces modifying DkkStm.exe
    directly with hex edits or PE section injection.

    File layout after deployment:
        <game_dir>/dinput8.dll          <- our proxy (loaded by the game)
        <game_dir>/dinput8_real.dll     <- renamed System32 dinput8.dll
                                           (our proxy forwards all exports here)
        <game_dir>/dinput8.dll.bak      <- any pre-existing dinput8.dll, preserved

    Returns True on success, False otherwise.
    """
    game_dir = os.path.dirname(exe_path)

    if not os.path.isfile(PROXY_DLL_SRC):
        print_err(f"Proxy DLL not built: {PROXY_DLL_SRC}")
        print_info("Build it first:")
        print_info(f"   cd {os.path.dirname(PROXY_DLL_SRC)}/..")
        print_info("   build.bat")
        return False

    if not os.path.isfile(SYSTEM_DINPUT8):
        print_err(f"System dinput8.dll not found: {SYSTEM_DINPUT8}")
        print_info("Cannot forward exports without the real DLL to chain to.")
        return False

    dst_proxy = os.path.join(game_dir, PROXY_DLL_NAME)
    dst_real  = os.path.join(game_dir, PROXY_REAL_NAME)

    # Preserve any pre-existing dinput8.dll (another mod's proxy, etc.)
    # as .bak on first install only — don't clobber our own backup on re-runs.
    if os.path.exists(dst_proxy):
        try:
            # If the file currently there is already our proxy (same size +
            # first few bytes), skip the .bak step.
            is_ours = False
            try:
                if os.path.getsize(dst_proxy) == os.path.getsize(PROXY_DLL_SRC):
                    with open(dst_proxy, 'rb') as a, open(PROXY_DLL_SRC, 'rb') as b:
                        is_ours = a.read(256) == b.read(256)
            except OSError:
                pass
            if not is_ours:
                bak = dst_proxy + ".bak"
                if not os.path.exists(bak):
                    print_info(f"Backing up existing dinput8.dll -> {os.path.basename(bak)}")
                    shutil.copy2(dst_proxy, bak)
        except PermissionError:
            print_err("Cannot back up existing dinput8.dll -- game may be running.")
            return False

    try:
        print_info(f"Copying system dinput8.dll -> {PROXY_REAL_NAME}")
        shutil.copy2(SYSTEM_DINPUT8, dst_real)
        print_info(f"Copying proxy {PROXY_DLL_NAME}")
        shutil.copy2(PROXY_DLL_SRC, dst_proxy)
    except PermissionError:
        print_err("Cannot write proxy DLL files -- game may be running.")
        return False
    except Exception as e:
        print_err(f"Proxy deploy failed: {e}")
        return False

    print_ok(f"Proxy DLL deployed to {game_dir}")
    return True


def remove_proxy_dll(exe_path):
    """Remove deployed proxy DLL files, restoring any pre-existing backup.
    Idempotent; silent if nothing was installed."""
    game_dir = os.path.dirname(exe_path)
    dst_proxy = os.path.join(game_dir, PROXY_DLL_NAME)
    dst_real  = os.path.join(game_dir, PROXY_REAL_NAME)
    bak_proxy = dst_proxy + ".bak"

    removed_any = False
    for f in (dst_proxy, dst_real):
        if os.path.isfile(f):
            try:
                os.remove(f)
                removed_any = True
            except OSError:
                pass
    if os.path.isfile(bak_proxy):
        try:
            shutil.move(bak_proxy, dst_proxy)
            print_info(f"Restored original dinput8.dll from .bak")
        except OSError:
            pass
    if removed_any:
        print_ok("Proxy DLL removed")


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


def extract_vanilla_asset(asset_name):
    """Extract the vanilla version of an asset from backup CPKs. Returns bytes or None."""
    assets_dir = os.path.join(BACKUP_DIR, "assets")
    for cpk_name in CPK_FILES:
        backup_cpk = os.path.join(assets_dir, cpk_name)
        if not os.path.exists(backup_cpk):
            continue
        try:
            cpk = CPKFile(backup_cpk)
            entry = cpk.find_file(asset_name)
            if entry:
                with open(backup_cpk, 'rb') as f:
                    f.seek(entry['abs_offset'])
                    return f.read(entry['file_size'])
        except Exception:
            continue
    return None


def merge_asset_files(vanilla_data, mod_versions):
    """Binary merge multiple mod versions of the same file against a vanilla base.
    
    Each mod is diffed against vanilla to find its changes.  All diffs are then
    combined.  If two mods change the same byte to different values, the last
    mod in the list wins and a warning is printed.
    
    Args:
        vanilla_data: bytes of the original unmodified file
        mod_versions: list of (mod_name, file_path) tuples
    
    Returns:
        (merged_bytes, change_count, conflict_count)
    """
    all_changes = {}  # offset -> (byte_value, mod_name)
    conflicts = 0
    
    for mod_name, mod_path in mod_versions:
        with open(mod_path, 'rb') as f:
            mod_data = f.read()
        
        # Diff this mod against vanilla
        common_len = min(len(vanilla_data), len(mod_data))
        for i in range(common_len):
            if vanilla_data[i] != mod_data[i]:
                if i in all_changes:
                    prev_val, prev_mod = all_changes[i]
                    if prev_val != mod_data[i]:
                        conflicts += 1
                        print_warn(
                            f"  Byte conflict at 0x{i:X}: "
                            f"[{prev_mod}] 0x{prev_val:02X} vs [{mod_name}] 0x{mod_data[i]:02X} "
                            f"(using {mod_name})"
                        )
                all_changes[i] = (mod_data[i], mod_name)
        
        # Handle mod being larger than vanilla
        for i in range(common_len, len(mod_data)):
            all_changes[i] = (mod_data[i], mod_name)
    
    # Apply all changes to a copy of the vanilla data
    merged = bytearray(vanilla_data)
    if all_changes:
        max_offset = max(all_changes.keys())
        if max_offset >= len(merged):
            merged.extend(b'\x00' * (max_offset - len(merged) + 1))
    for offset, (value, _) in all_changes.items():
        merged[offset] = value
    
    return bytes(merged), len(all_changes), conflicts


def apply_asset_mods(exe_path, asset_entries):
    """Replace asset files in the game's CPK archives and create loose file overrides.
    
    asset_entries is a list of (mod_name, asset_path) tuples.
    When multiple mods supply the same file, their changes are merged against
    the vanilla base via binary diff.
    """
    if not asset_entries:
        return 0
    
    game_dir = os.path.dirname(exe_path)
    
    # Group by filename — collect all mod versions of each asset
    assets_by_name = {}  # filename -> [(mod_name, path), ...]
    for mod_name, asset_path in asset_entries:
        fname = os.path.basename(asset_path)
        assets_by_name.setdefault(fname, []).append((mod_name, asset_path))
    
    # Resolve each asset to a single file path (merge if needed)
    assets_to_install = {}  # filename -> resolved_path
    temp_files = []  # track temp files for cleanup
    
    for fname, versions in assets_by_name.items():
        if len(versions) == 1:
            assets_to_install[fname] = versions[0][1]
        else:
            # Multiple mods touch the same file — merge against vanilla
            mod_names = ", ".join(v[0] for v in versions)
            print_info(f"Merging '{fname}' from {len(versions)} mods: {mod_names}")
            
            vanilla_data = extract_vanilla_asset(fname)
            if vanilla_data is None:
                print_err(f"Cannot merge '{fname}': vanilla version not found in backup CPKs")
                # Fall back to last mod
                assets_to_install[fname] = versions[-1][1]
                continue
            
            merged, changes, conflicts = merge_asset_files(vanilla_data, versions)
            
            if conflicts:
                print_warn(f"  {conflicts} byte conflict(s) — last mod's value used")
            print_ok(f"  Merged {changes} changed byte(s) from {len(versions)} mods")
            
            # Write merged result to temp file
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=f"_{fname}", dir=tempfile.gettempdir()
            )
            tmp.write(merged)
            tmp.close()
            assets_to_install[fname] = tmp.name
            temp_files.append(tmp.name)
    
    # Install resolved assets into CPK files + loose overrides
    installed = 0
    override_paths = []
    
    try:
        for cpk_name in CPK_FILES:
            cpk_paths = []
            cpk_root = os.path.join(game_dir, cpk_name)
            cpk_assets = os.path.join(game_dir, "assets", cpk_name)
            if os.path.exists(cpk_root):
                cpk_paths.append(cpk_root)
            if os.path.exists(cpk_assets):
                cpk_paths.append(cpk_assets)
            
            if not cpk_paths:
                continue
            
            try:
                cpk = CPKFile(cpk_paths[0])
            except Exception as e:
                print_err(f"Failed to open {cpk_name}: {e}")
                continue
            
            # Build lookup: lowercase name -> CPK entry (with dir info)
            cpk_filenames = {f['name'].lower(): f for f in cpk.files}
            
            for asset_name, asset_path in list(assets_to_install.items()):
                if asset_name.lower() in cpk_filenames:
                    try:
                        ok = True
                        for cpk_path in cpk_paths:
                            c = CPKFile(cpk_path)
                            result = c.replace_file(asset_name, asset_path)
                            if not result:
                                ok = False
                        if ok:
                            locations = " + ".join(
                                os.path.relpath(p, game_dir) for p in cpk_paths
                            )
                            print_ok(f"Asset '{asset_name}' -> {cpk_name} ({locations})")
                            installed += 1
                            
                            # Create loose file overrides so the CRI middleware
                            # picks up the modded file from disk
                            entry_info = cpk_filenames[asset_name.lower()]
                            dir_name = entry_info.get('dir', '')
                            if dir_name:
                                for base in [game_dir, os.path.join(game_dir, 'assets')]:
                                    if not os.path.isdir(base):
                                        continue
                                    override_dir = os.path.join(base, dir_name)
                                    os.makedirs(override_dir, exist_ok=True)
                                    override_file = os.path.join(override_dir, asset_name)
                                    shutil.copy2(asset_path, override_file)
                                    override_paths.append(override_file)
                                print_ok(f"Loose override: {dir_name}/{asset_name}")
                            
                            del assets_to_install[asset_name]
                        else:
                            print_err(f"Failed to replace '{asset_name}' in {cpk_name}")
                    except Exception as e:
                        print_err(f"Error replacing '{asset_name}' in {cpk_name}: {e}")
    finally:
        # Clean up temp files from merges
        for tmp in temp_files:
            try:
                os.remove(tmp)
            except OSError:
                pass
    
    # Save override manifest for cleanup on next install
    if override_paths:
        os.makedirs(os.path.dirname(OVERRIDES_MANIFEST), exist_ok=True)
        with open(OVERRIDES_MANIFEST, 'w') as f:
            for p in override_paths:
                f.write(p + '\n')
    
    # Report any assets that weren't found in any CPK
    for name in assets_to_install:
        print_warn(f"Asset '{name}' not found in any CPK archive")
    
    return installed


# ============================================================================
# Main Installer Flow
# ============================================================================

def run_installer(patch_exe_directly=False):
    """Main installation flow.

    Default pipeline (DLL-based, preferred):
      1. Locate game exe (triggers first-time modded-exe creation)
      2. Discover mods
      3. Back up original files
      4. Restore-from-backup to start clean
      5. Deploy dinput8.dll proxy into the game folder
      6. Install asset mods (CPK replacement + loose overrides)

    Hex edits and code mods that would modify `DkkStm.exe` are SKIPPED by
    default -- those belong in the proxy DLL's runtime_patcher now. Set
    `patch_exe_directly=True` to run the legacy EXE-patching flow for
    mods that still ship .hex or code_mods payloads.
    """
    print_header("DKCModTool Installer v2.0")
    print_info("Dokapon Kingdom: Connect Mod Installer")
    print_info(f"Root: {ROOT_DIR}")
    if patch_exe_directly:
        print_warn("Legacy mode: hex edits and code mods WILL modify DkkStm.exe")
    else:
        print_info("DLL-based pipeline: patches applied via dinput8.dll proxy")

    # 1. Find game exe  (also creates <stem>_modded.exe on first-time setup)
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
        # Deploying the proxy DLL alone still has value (runtime patches
        # baked into it). Continue rather than abort.

    total_assets = total_hex = total_codes = 0
    for mod in mods:
        na = len(mod['assets']); nh = len(mod['hex_edits']); nc = len(mod['code_mods'])
        total_assets += na; total_hex += nh; total_codes += nc
        print_info(f"  [{mod['name']}] {na} assets, {nh} hex edits, {nc} code mods")
    if mods:
        print_info(f"\n   Total: {total_assets} assets, {total_hex} hex edits, "
                   f"{total_codes} code mods")

    # Warn about skipped mod channels when running the DLL-first pipeline.
    if not patch_exe_directly and (total_hex or total_codes):
        print_warn(
            f"Skipping {total_hex} hex edit(s) and {total_codes} code mod(s): "
            f"these modify DkkStm.exe directly. Port them to the proxy DLL's "
            f"runtime_patcher, or re-run with --patch-exe to apply them."
        )

    # 3. Backup
    backup_game_files(exe_path)

    # 4. Check files are writable (includes exe when we're in legacy mode)
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

    # 6. Re-assert modded-exe (idempotent) — ensures it exists after restore.
    create_modded_exe(exe_path)

    # 7. Apply mods
    if patch_exe_directly:
        # --- Legacy path: modifies DkkStm.exe ---
        all_hex = [h for mod in mods for h in mod['hex_edits']]
        if all_hex:
            print_step(f"Applying {len(all_hex)} hex edit file(s)...")
            apply_hex_edits(exe_path, all_hex)
        all_codes = [c for mod in mods for c in mod['code_mods']]
        if all_codes:
            print_step(f"Injecting {len(all_codes)} code mod(s)...")
            apply_code_mods(exe_path, all_codes)
    else:
        # --- DLL-based path: deploys dinput8.dll proxy ---
        print_step("Deploying proxy DLL...")
        if not deploy_proxy_dll(exe_path):
            print_err("Proxy DLL deployment failed. CPK assets will still install.")

    # Asset mods — always applied (CPK data, not EXE)
    all_assets = [(mod['name'], p) for mod in mods for p in mod['assets']]
    if all_assets:
        print_step(f"Installing {len(all_assets)} asset file(s)...")
        apply_asset_mods(exe_path, all_assets)

    print_header("Installation Complete!")
    if not patch_exe_directly:
        print_info("Launch the game via DkkStm_modded.exe for a deterministic")
        print_info("memory layout, or use the normal Steam launcher if you")
        print_info("only need the proxy DLL's runtime patches + asset mods.")
    return True


def main():
    # Legacy EXE-patching mode: only active if the user passes --patch-exe
    # or sets DKCMOD_PATCH_EXE=1 in the environment. All other invocations
    # route through the DLL proxy.
    patch_exe_directly = (
        "--patch-exe" in sys.argv
        or os.environ.get("DKCMOD_PATCH_EXE", "").lower() in ("1", "true", "yes")
    )
    try:
        success = run_installer(patch_exe_directly=patch_exe_directly)
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
