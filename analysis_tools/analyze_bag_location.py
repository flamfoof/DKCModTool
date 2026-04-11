"""Analyze bag data location near battle requirement table."""
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

print("Analyzing bag data location near battle requirement table:")
print("=" * 70)

data = read_stagebase()

JOB_NAMES = ["Warrior", "Magician", "Thief", "Cleric", "Spellsword", "Alchemist", "Ninja", "Monk", "Acrobat", "Robo Knight"]

# Found [6, 10] patterns at 0x175EE, 0x175F6, 0x1762E, 0x17636
# Let me analyze this region
print("\nHex dump around 0x175EE (found [6, 10] pattern):")
print(hexdump(data, 0x175E0, 128))

# Look for class_id patterns followed by [6, 10]
print("\nSearching for class_id followed by [6, 10] in this region:")
for offset in range(0x17500, 0x17700):
    if offset + 10 < len(data):
        class_id = data[offset]
        if class_id <= 9:
            # Check if next bytes are [6, 10]
            if data[offset + 1] == 6 and data[offset + 2] == 10:
                variant = data[offset + 3]
                class_name = JOB_NAMES[class_id]
                print(f"0x{offset:X}: {class_name} class_id={class_id}, item_slots=6, magic_slots=10, variant={variant}")
                print(f"  Context: {data[offset-4:offset+12].hex()}")

# Try different structure: [class_id, item_slots, magic_slots, ...]
print("\nTrying structure [class_id, item_slots, magic_slots, ...]:")
for offset in range(0x17500, 0x17700):
    if offset + 10 < len(data):
        class_id = data[offset]
        if class_id <= 9:
            item_slots = data[offset + 1]
            magic_slots = data[offset + 2]
            if item_slots > 0 or magic_slots > 0:
                variant = data[offset + 3]
                class_name = JOB_NAMES[class_id]
                print(f"0x{offset:X}: {class_name} class_id={class_id}, item_slots={item_slots}, magic_slots={magic_slots}, variant={variant}")

# Try structure: [item_slots, magic_slots, class_id, variant, ...]
print("\nTrying structure [item_slots, magic_slots, class_id, variant, ...]:")
for offset in range(0x17500, 0x17700):
    if offset + 10 < len(data):
        item_slots = data[offset]
        magic_slots = data[offset + 1]
        class_id = data[offset + 2]
        if class_id <= 9:
            variant = data[offset + 3]
            if item_slots > 0 or magic_slots > 0:
                class_name = JOB_NAMES[class_id]
                print(f"0x{offset:X}: {class_name} item_slots={item_slots}, magic_slots={magic_slots}, class_id={class_id}, variant={variant}")
