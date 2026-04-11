"""Re-analyze bag data structure based on user feedback."""
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

def read_stagebase():
    with open(STAGEBASE, 'rb') as f:
        return f.read()

def hexdump(data, offset, length=64):
    result = []
    for i in range(0, length, 16):
        chunk = data[offset+i:offset+i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"  0x{offset+i:06X}: {hex_str:<48} {ascii_str}")
    return '\n'.join(result)

print("=" * 70)
print("RE-ANALYZING BAG DATA STRUCTURE")
print("=" * 70)

data = read_stagebase()

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight"]

# User says Thief has 6 items and 10 field magic inventory
# Let me search for these values in the bag data

BAG_TABLE_OFFSET = 0x1884E
BAG_ENTRY_SIZE = 8

print("\nSearching for Thief (class 2) with 6 items and 10 magic:")
for offset in range(BAG_TABLE_OFFSET, BAG_TABLE_OFFSET + 20 * BAG_ENTRY_SIZE):
    if offset + 8 < len(data):
        # Try different interpretations
        # Interpretation: [item_slots, magic_slots, ...]
        item_slots = data[offset]
        magic_slots = data[offset + 1]
        
        if item_slots == 6 and magic_slots == 10:
            class_idx = data[offset + 6]
            variant = data[offset + 7]
            print(f"Found at 0x{offset:X}: item_slots={item_slots}, magic_slots={magic_slots}, class_idx={class_idx}, variant={variant}")
            print(f"  Context: {data[offset-4:offset+12].hex()}")

# Also try uint16 interpretation
print("\nTrying uint16 interpretation:")
for offset in range(BAG_TABLE_OFFSET, BAG_TABLE_OFFSET + 20 * BAG_ENTRY_SIZE):
    if offset + 8 < len(data):
        item_slots = struct.unpack_from('<H', data, offset)[0]
        magic_slots = struct.unpack_from('<H', data, offset + 2)[0]
        
        if item_slots == 6 and magic_slots == 10:
            class_idx = data[offset + 6]
            variant = data[offset + 7]
            print(f"Found at 0x{offset:X}: item_slots={item_slots}, magic_slots={magic_slots}, class_idx={class_idx}, variant={variant}")
            print(f"  Context: {data[offset-4:offset+12].hex()}")

# Dump all bag entries and look for patterns
print("\nAll bag entries (hex):")
for i in range(20):
    offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
    bytes_data = data[offset:offset+8]
    class_idx = data[offset + 6]
    variant = data[offset + 7]
    
    if class_idx <= 9:
        variant_str = "M" if variant == 0 else "F"
        class_name = JOB_NAMES[class_idx]
        print(f"Entry {i}: {class_name} {variant_str} - {bytes_data.hex()}")

# Try to find where 6 and 10 might be stored for Thief
print("\nSearching for values 6 and 10 in bag data region:")
for offset in range(BAG_TABLE_OFFSET, BAG_TABLE_OFFSET + 20 * BAG_ENTRY_SIZE):
    if offset + 8 < len(data):
        for i in range(8):
            if data[offset + i] == 6:
                class_idx = data[offset + 6]
                variant = data[offset + 7]
                if class_idx <= 9:
                    variant_str = "M" if variant == 0 else "F"
                    class_name = JOB_NAMES[class_idx]
                    print(f"0x{offset:X}+{i}: value=6, class={class_name} {variant_str}")
