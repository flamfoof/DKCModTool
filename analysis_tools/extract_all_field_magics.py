"""Extract all field magics with their price offsets from stageBase_EN.DAT."""
import struct
import csv
import os

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

with open(STAGEBASE, 'rb') as f:
    data = f.read()

# Load field magics from CSV
csv_path = os.path.join("table_sample", "dokapon_field_magic.csv")
magics = []

with open(csv_path, 'r') as f:
    reader = csv.reader(f)
    header = next(reader)  # Skip header
    
    for row in reader:
        if row and row[0]:  # ID
            magic_id = row[0]
            name = row[1]
            buying_price = row[2] if len(row) > 2 else "N/A"
            power = row[3] if len(row) > 3 else "N/A"
            target = row[5] if len(row) > 5 else ""
            effect = row[6] if len(row) > 6 else ""
            
            # Parse buying price
            if buying_price != "N/A":
                buying_price = buying_price.replace("G", "").replace(",", "").strip()
                try:
                    buying_price = int(buying_price)
                except:
                    buying_price = 0
            
            # Parse power
            if power != "N/A" and power != "-":
                try:
                    power = float(power)
                except:
                    power = 0
            else:
                power = 0
            
            magics.append({
                "id": magic_id,
                "name": name,
                "buying_price": buying_price,
                "power": power,
                "target": target,
                "effect": effect,
            })

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def read_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

print("=" * 70)
print("EXTRACTING ALL FIELD MAGICS WITH PRICE OFFSETS")
print("=" * 70)

extracted_magics = []

for magic in magics:
    name = magic["name"]
    buying_price = magic["buying_price"]
    
    if buying_price == 0:
        continue  # Skip magics with no price
    
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
    price_type = None
    
    for i in range(search_start, search_end - 1):
        if i + 2 <= len(data):
            val16 = read_uint16(data, i)
            if val16 == buying_price:
                price_offset = i
                price_type = "uint16"
                break
        
        if i + 4 <= len(data):
            val32 = read_uint32(data, i)
            if val32 == buying_price:
                price_offset = i
                price_type = "uint32"
                break
    
    if price_offset:
        extracted_magics.append({
            "name": name,
            "name_offset": offset,
            "price_offset": price_offset,
            "price_type": price_type,
            "buying_price": buying_price,
            "power": magic["power"],
            "target": magic["target"],
            "effect": magic["effect"],
        })
        print(f"{name:20} at 0x{price_offset:X} ({price_type}, offset +{price_offset - offset}) - Price: {buying_price}G Power: {magic['power']}")
    else:
        print(f"{name:20} - Price not found")

print(f"\nTotal magics extracted: {len(extracted_magics)}")

# Save to JSON
import json
output_path = r"..\..\Mods\Field-Magic-Editor\field_magics.json"
output_dir = os.path.dirname(output_path)
os.makedirs(output_dir, exist_ok=True)

with open(output_path, 'w') as f:
    json.dump(extracted_magics, f, indent=2)

print(f"\nSaved field magic data to {output_path}")
