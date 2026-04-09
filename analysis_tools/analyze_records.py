"""Deep analysis of stageBase record structures."""
import struct

STAGEBASE = r"Mods\JaJo's Balance Patch v1.0.1\Assets\stageBase_EN.DAT"

with open(STAGEBASE, 'rb') as f:
    data = f.read()

def hexdump(data, offset, length, label=""):
    if label:
        print(f"\n--- {label} ---")
    for i in range(0, length, 16):
        addr = offset + i
        chunk = data[addr:addr+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"  0x{addr:06X}: {hex_str:<48} {ascii_str}")

# ============= JOB/CLASS DATA =============
print("=" * 70)
print("JOB/CLASS TABLE ANALYSIS")
print("=" * 70)

# Bag data region - dump a wide area around it
hexdump(data, 0x18840, 0xB0, "Bag Data Region (0x18840)")

# Level-up data region
hexdump(data, 0x18590, 0x100, "Level-up Data Region (0x18590)")

# Skill data region
hexdump(data, 0x18340, 0x80, "Skill Data Region (0x18340)")

# ============= ITEM DATA =============
print("\n" + "=" * 70)
print("ITEM/EQUIPMENT DATA ANALYSIS")
print("=" * 70)

# Item names region around 0xE498
hexdump(data, 0xE480, 0x60, "Item Name Region - Hero License area (0xE480)")

# Equipment - M Guard DX
hexdump(data, 0x14EF0, 0x40, "Equipment Region - M Guard DX (0x14EF0)")

# Shield stats
hexdump(data, 0xAC00, 0x30, "Shield Stats - Wabbit Shield (0xAC00)")

# Weapon class requirements
hexdump(data, 0x8510, 0x20, "Weapon - Dragon Guandao (0x8510)")

# ============= SHOP DATA =============
print("\n" + "=" * 70)
print("SHOP DATA ANALYSIS")
print("=" * 70)

hexdump(data, 0x5080, 0x30, "Shop Data - Afrike (0x5080)")
hexdump(data, 0x51C0, 0x40, "Shop Data - Clovis (0x51C0)")

# ============= ENEMY DATA =============
print("\n" + "=" * 70)
print("ENEMY DATA ANALYSIS")
print("=" * 70)

hexdump(data, 0x1B030, 0x60, "Enemy Data - Rogue area (0x1B030)")
hexdump(data, 0x1B080, 0x40, "Enemy Data - Barbarian area (0x1B080)")

# Try to find enemy record size by looking at repeated patterns
# Rogue def magic at 0x1B041
# Barbarian skill at 0x1B092
# Halfling def magic at 0x1B0DD
# Diff: 0x1B092 - 0x1B041 = 0x51 = 81 bytes... odd
# Diff: 0x1B0DD - 0x1B092 = 0x4B = 75 bytes... also odd
# These are different fields within different enemy records

# Let's look for a repeating structure
hexdump(data, 0x1B000, 0x180, "Enemy Data Full Region (0x1B000)")

# ============= STATUS EFFECTS =============
print("\n" + "=" * 70)
print("STATUS EFFECT DATA ANALYSIS")
print("=" * 70)

hexdump(data, 0x1A660, 0x30, "Status - Squeeze (0x1A660)")
hexdump(data, 0x1A6A0, 0x30, "Status - Petrify (0x1A6A0)")
hexdump(data, 0x1AA80, 0x30, "Status - Sealed (0x1AA80)")
hexdump(data, 0x1AAF0, 0x30, "Status - Invisible (0x1AAF0)")

# ============= DAMAGE FORMULA =============
print("\n" + "=" * 70)
print("DAMAGE FORMULA DATA ANALYSIS")
print("=" * 70)

hexdump(data, 0xB0DC0, 0x200, "Damage Formula Region (0xB0DC0)")

# ============= LOOT TABLES =============
print("\n" + "=" * 70)
print("LOOT TABLE DATA ANALYSIS")
print("=" * 70)

hexdump(data, 0x4C60, 0x40, "Loot Table 58 (0x4C60)")
hexdump(data, 0x40A0, 0x30, "Loot Table 15 (0x40A0)")

# ============= AI TABLES =============
print("\n" + "=" * 70)
print("AI TABLE DATA ANALYSIS")
print("=" * 70)

hexdump(data, 0x1E1C0, 0x40, "AI Data - Demon's Guard area (0x1E1C0)")
hexdump(data, 0x1E3E0, 0x30, "AI Table 24-25 (0x1E3E0)")

# ============= JOB UNLOCK DATA =============
print("\n" + "=" * 70)
print("JOB UNLOCK DATA ANALYSIS")  
print("=" * 70)

hexdump(data, 0x18B60, 0x40, "Job Unlock Data (0x18B60)")

# ============= @BAS HEADER =============
print("\n" + "=" * 70)
print("@BAS FILE HEADER ANALYSIS")
print("=" * 70)

hexdump(data, 0x0, 0x60, "File Header")

# Check if there's a table of contents / offset table after the header
header_magic = data[0:4]
field1 = struct.unpack_from('<I', data, 4)[0]
field2 = struct.unpack_from('<I', data, 8)[0]
print(f"\nHeader magic: {header_magic}")
print(f"Field at 0x04: 0x{field1:X} ({field1})")
print(f"Field at 0x08: 0x{field2:X} ({field2}) - possible data start offset?")

# Look at offset 0x30 (data start)
hexdump(data, 0x30, 0x60, "Data start at 0x30")

# Check for any index/pointer table
print("\n--- Searching for pointer tables ---")
# Look for sequences of increasing 4-byte values that could be offsets
for base in range(0x30, 0x200, 4):
    vals = [struct.unpack_from('<I', data, base + i*4)[0] for i in range(4)]
    if all(0x100 < v < len(data) for v in vals) and all(vals[i] < vals[i+1] for i in range(3)):
        if vals[1] - vals[0] < 0x10000:
            print(f"  Potential offset table at 0x{base:X}: {[f'0x{v:X}' for v in vals]}")

# ============= CLASS NAMES AND STRUCTURE =============
print("\n" + "=" * 70)
print("CLASS NAME REGION ANALYSIS")
print("=" * 70)

# Class names found at 0x98E8, 0x9930, 0x997B, etc.
hexdump(data, 0x98D0, 0x200, "Class Name Region (0x98D0)")

# ============= ITEM NAMES REGION =============
print("\n" + "=" * 70)
print("ITEM NAME/DATA REGION ANALYSIS")
print("=" * 70)

# Item flag data
hexdump(data, 0xFB60, 0x30, "Item Flags - Magic Medicine (0xFB60)")
hexdump(data, 0xFBD0, 0x30, "Item Flags - Charm Potion (0xFBD0)")
hexdump(data, 0xFC10, 0x30, "Item Flags - Hero License (0xFC10)")
