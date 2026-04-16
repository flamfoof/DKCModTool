"""Extract all monster names and try to find their data structure."""
import struct
import csv

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

with open(STAGEBASE, 'rb') as f:
    data = f.read()

# Load all monster names from CSV
monsters_csv = []
with open(r"table_sample\dokapon_monsters.csv", 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if row and len(row) >= 2 and row[1]:
            monsters_csv.append(row)

print("=" * 70)
print("FINDING ALL MONSTER NAMES IN DAT")
print("=" * 70)

monster_offsets = {}
for row in monsters_csv:
    name = row[1]
    try:
        name_bytes = name.encode('ascii')
    except:
        continue
    offset = data.find(name_bytes)
    if offset >= 0:
        monster_offsets[name] = offset
        print(f"{name:20} at 0x{offset:X}")

print(f"\nTotal monsters found: {len(monster_offsets)}")

# Analyze data structure around monster names
print("\n" + "=" * 70)
print("ANALYZING DATA STRUCTURE AROUND MONSTER NAMES")
print("=" * 70)

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def read_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

# Analyze a few monsters to find pattern
test_monsters = ["Rogue", "Berserker", "Barbarian", "Bandit", "Halfling"]

for name in test_monsters:
    if name not in monster_offsets:
        continue
    offset = monster_offsets[name]
    print(f"\n{name} at 0x{offset:X}:")
    
    # Dump 128 bytes before and after
    start = max(0, offset - 64)
    end = min(len(data), offset + 64)
    
    for i in range(start, end, 16):
        hex_str = " ".join(f"{data[j]:02X}" for j in range(i, min(i+16, end)))
        ascii_str = "".join(chr(data[j]) if 32 <= data[j] < 127 else "." for j in range(i, min(i+16, end)))
        marker = " <-- NAME" if i <= offset < i+16 else ""
        print(f"  0x{i:X}: {hex_str:48} {ascii_str}{marker}")
