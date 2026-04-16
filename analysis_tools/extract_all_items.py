"""Extract all items with their price offsets from stageBase_EN.DAT."""
import struct
import csv
import os

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"

with open(STAGEBASE, 'rb') as f:
    data = f.read()

# Load all items from CSV files
items = []

csv_files = [
    "dokapon_item_healing.csv",
    "dokapon_item_powerup.csv",
    "dokapon_item_assist.csv",
    "dokapon_item_cursed.csv",
    "dokapon_item_movement.csv",
    "dokapon_item_obstruct.csv",
    "dokapon_item_special.csv",
]

for csv_file in csv_files:
    csv_path = os.path.join("table_sample", "table_items", csv_file)
    if not os.path.exists(csv_path):
        continue
    
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        
        for row in reader:
            if row and row[0]:  # Item name
                item_name = row[0]
                # Parse sell price
                sell_price = row[2] if len(row) > 2 else "N/A"
                # Remove 'G' and commas from price
                if sell_price != "N/A":
                    sell_price = sell_price.replace("G", "").replace(",", "").strip()
                    # Handle special cases
                    if "/" in sell_price or "your" in sell_price:
                        sell_price = "0"
                    try:
                        sell_price = int(sell_price)
                    except:
                        sell_price = 0
                
                # Get effect/details
                effect = row[1] if len(row) > 1 else ""
                
                items.append({
                    "name": item_name,
                    "sell_price": sell_price,
                    "effect": effect,
                    "file": csv_file,
                })

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def read_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

print("=" * 70)
print("EXTRACTING ALL ITEMS WITH PRICE OFFSETS")
print("=" * 70)

extracted_items = []

for item in items:
    name = item["name"]
    sell_price = item["sell_price"]
    
    if sell_price == 0 or sell_price == "N/A":
        continue  # Skip items with no price
    
    try:
        name_bytes = name.encode('ascii')
    except:
        continue
    
    offset = data.find(name_bytes)
    if offset < 0:
        continue
    
    # Search for price*2 in the 32 bytes after the name
    search_start = offset + len(name) + 1
    search_end = min(search_start + 32, len(data))
    
    price_offset = None
    price_type = None
    
    for i in range(search_start, search_end - 1):
        if i + 2 <= len(data):
            val16 = read_uint16(data, i)
            if val16 == sell_price * 2:
                price_offset = i
                price_type = "uint16"
                break
        
        if i + 4 <= len(data):
            val32 = read_uint32(data, i)
            if val32 == sell_price * 2:
                price_offset = i
                price_type = "uint32"
                break
    
    if price_offset:
        extracted_items.append({
            "name": name,
            "name_offset": offset,
            "price_offset": price_offset,
            "price_type": price_type,
            "sell_price": sell_price,
            "stored_price": sell_price * 2,
            "effect": item["effect"],
            "file": item["file"],
        })
        print(f"{name:25} at 0x{price_offset:X} ({price_type}, offset +{price_offset - offset}) - Price: {sell_price}G")
    else:
        print(f"{name:25} - Price not found")

print(f"\nTotal items extracted: {len(extracted_items)}")

# Save to JSON
import json
output_path = r"..\..\Mods\Items-Editor\items.json"
output_dir = os.path.dirname(output_path)
os.makedirs(output_dir, exist_ok=True)

with open(output_path, 'w') as f:
    json.dump(extracted_items, f, indent=2)

print(f"\nSaved item data to {output_path}")
