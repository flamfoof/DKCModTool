"""Extract status effects data from stageBase_EN.DAT for reference."""
import csv
import struct

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

with open(STAGEBASE, 'rb') as f:
    data = f.read()

# Load status effects from CSV
status_effects = []
with open(r"table_sample\dokapon_status_effects.csv", 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if row and len(row) >= 1:
            name = row[0]
            duration = row[4] if len(row) > 4 else ""
            field_effect = row[1] if len(row) > 1 else ""
            battle_effect = row[2] if len(row) > 2 else ""
            caused_by = row[3] if len(row) > 3 else ""
            status_effects.append({
                "name": name,
                "duration": duration,
                "field_effect": field_effect,
                "battle_effect": battle_effect,
                "caused_by": caused_by
            })

def read_uint8(data, offset):
    return data[offset]

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def read_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

print("=" * 70)
print("STATUS EFFECTS DATA TABLE")
print("=" * 70)

# Create a table of all status effects with their data
output_data = []

for effect in status_effects:
    name = effect["name"]
    duration = effect["duration"]
    field_effect = effect["field_effect"]
    battle_effect = effect["battle_effect"]
    caused_by = effect["caused_by"]
    
    # Try to find the name in the DAT
    try:
        name_bytes = name.encode('ascii')
    except:
        output_data.append({
            "name": name,
            "offset": None,
            "duration": duration,
            "field_effect": field_effect,
            "battle_effect": battle_effect,
            "caused_by": caused_by,
            "hex_data": "N/A (non-ASCII)"
        })
        continue
    
    offset = data.find(name_bytes)
    if offset >= 0:
        # Get hex data around the name (32 bytes after name)
        start = offset
        end = min(offset + 48, len(data))
        hex_data = " ".join(f"{data[j]:02X}" for j in range(start, end))
        
        output_data.append({
            "name": name,
            "offset": f"0x{offset:X}",
            "duration": duration,
            "field_effect": field_effect,
            "battle_effect": battle_effect,
            "caused_by": caused_by,
            "hex_data": hex_data
        })
    else:
        output_data.append({
            "name": name,
            "offset": None,
            "duration": duration,
            "field_effect": field_effect,
            "battle_effect": battle_effect,
            "caused_by": caused_by,
            "hex_data": "N/A (not found)"
        })

# Print the table
print(f"{'Name':<20} {'Offset':<12} {'Duration':<30} {'Hex Data'}")
print("-" * 120)
for item in output_data:
    print(f"{item['name']:<20} {item['offset'] or 'N/A':<12} {item['duration']:<30} {item['hex_data'][:40]}")

# Save to JSON
import json
import os

output_dir = r"..\..\Mods\Status_Effects-Editor"
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "status_effects_data.json")
with open(output_path, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\nSaved status effects data to {output_path}")

# Focus on status effects with numeric duration values
print("\n" + "=" * 70)
print("STATUS EFFECTS WITH NUMERIC DURATION VALUES")
print("=" * 70)

numeric_duration_effects = [
    ("Blind", "Battle; 2~4 turns", [2, 3, 4]),
    ("Confused", "Battle", []),
    ("Doom", "7~10 Days", [7, 8, 9, 10]),
    ("Footsore", "2~3 Days", [2, 3]),
    ("Paralysis", "1 Day", [1]),
    ("Seal", "3~5 Days", [3, 4, 5]),
    ("Sleep", "1~2 Days", [1, 2]),
    ("Stun", "Battle; 1~3 turns", [1, 2, 3]),
    ("Wanted", "7 Days", [7]),
    ("AT Down", "3~5 Days", [3, 4, 5]),
    ("DF Down", "3~5 Days", [3, 4, 5]),
    ("MG Down", "3~5 Days", [3, 4, 5]),
    ("SP Down", "3~5 Days", [3, 4, 5]),
    ("All Down", "3~5 Days", [3, 4, 5]),
]

for name, duration, expected_values in numeric_duration_effects:
    try:
        name_bytes = name.encode('ascii')
    except:
        continue
    
    offset = data.find(name_bytes)
    if offset >= 0:
        print(f"\n{name} (Duration: {duration}) at 0x{offset:X}:")
        
        # Dump 64 bytes around the name
        start = max(0, offset - 16)
        end = min(len(data), offset + 48)
        
        print("  Hex dump:")
        for i in range(start, end, 16):
            hex_str = " ".join(f"{data[j]:02X}" for j in range(i, min(i+16, end)))
            marker = " <-- NAME" if i <= offset < i+16 else ""
            print(f"    0x{i:X}: {hex_str}{marker}")
        
        # Search for expected duration values
        if expected_values:
            print(f"  Searching for expected duration values {expected_values} in nearby data...")
            found_at = []
            for val in expected_values:
                for i in range(start, end - 3):
                    if i < len(data):
                        if read_uint8(data, i) == val:
                            found_at.append((val, i, "uint8"))
                    if i + 2 <= len(data):
                        if read_uint16(data, i) == val:
                            found_at.append((val, i, "uint16"))
            
            if found_at:
                for val, off, dtype in found_at:
                    print(f"    Found {val} as {dtype} at 0x{off:X}")
            else:
                print(f"    No matches found for expected values")
