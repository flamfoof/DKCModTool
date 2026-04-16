"""Extract all battle magic with their price and power offsets from stageBase_EN.DAT."""
import struct
import csv
import os

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

with open(STAGEBASE, 'rb') as f:
    data = f.read()

# Load attack magic from CSV
attack_magics = []
with open(r"table_sample\dokapon_atk_magic.csv", 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if row and len(row) >= 3:
            name = row[1]
            price = row[2].replace("G", "").replace(",", "").strip()
            power_str = row[3]
            try:
                power = float(power_str)
                # Try converting to integer (multiplied by 100)
                power_int = int(power * 100) if power > 0 else 0
            except:
                power = 0
                power_int = 0
            attack_magics.append({
                "name": name,
                "price": int(price) if price else 0,
                "power": power,
                "power_int": power_int,
                "type": "attack"
            })

# Load defensive magic from CSV
def_magics = []
with open(r"table_sample\dokapon_def_magic.csv", 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if row and len(row) >= 3:
            name = row[1]
            price = row[2].replace("G", "").replace(",", "").strip()
            power_str = row[3].replace("%", "")
            try:
                power = int(power_str)
            except:
                power = 0
            def_magics.append({
                "name": name,
                "price": int(price) if price else 0,
                "power": power,
                "power_int": power,
                "type": "defensive"
            })

all_magics = attack_magics + def_magics

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def read_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

def read_float(data, offset):
    return struct.unpack_from('<f', data, offset)[0]

print("=" * 70)
print("EXTRACTING ALL BATTLE MAGIC WITH PRICE AND POWER OFFSETS")
print("=" * 70)

extracted_magics = []

for magic in all_magics:
    name = magic["name"]
    price = magic["price"]
    power_int = magic["power_int"]
    magic_type = magic["type"]
    
    try:
        name_bytes = name.encode('ascii')
    except:
        continue
    
    offset = data.find(name_bytes)
    if offset < 0:
        continue
    
    # Search for price in the 32 bytes after the name
    search_start = offset + len(name) + 1
    search_end = min(search_start + 32, len(data))
    
    price_offset = None
    power_offset = None
    
    # Find price (uint16 or uint32)
    for i in range(search_start, search_end - 3):
        if i + 2 <= len(data):
            val16 = read_uint16(data, i)
            if val16 == price:
                price_offset = i
                break
        
        if i + 4 <= len(data):
            val32 = read_uint32(data, i)
            if val32 == price:
                price_offset = i
                break
    
    # Find power
    if power_int > 0:
        for i in range(search_start, search_end - 3):
            if i + 2 <= len(data):
                val16 = read_uint16(data, i)
                if val16 == power_int:
                    power_offset = i
                    break
            
            if i + 4 <= len(data):
                val32 = read_uint32(data, i)
                if val32 == power_int:
                    power_offset = i
                    break
    
    if price_offset:
        extracted_magics.append({
            "name": name,
            "name_offset": offset,
            "price_offset": price_offset,
            "price": price,
            "power_offset": power_offset,
            "power": magic["power"],
            "power_int": power_int,
            "type": magic_type,
        })
        power_str = f"at 0x{power_offset:X}" if power_offset else "not found"
        print(f"{name:20} - Price: 0x{price_offset:X} ({price}G), Power: {power_str}")
    else:
        print(f"{name:20} - Price not found")

print(f"\nTotal magics extracted: {len(extracted_magics)}")

# Save to JSON
import json
output_path = r"..\..\Mods\Battle_Magic-Editor\magic.json"
output_dir = os.path.dirname(output_path)
os.makedirs(output_dir, exist_ok=True)

with open(output_path, 'w') as f:
    json.dump(extracted_magics, f, indent=2)

print(f"\nSaved magic data to {output_path}")
