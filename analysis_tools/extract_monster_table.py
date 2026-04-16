"""Extract monster table using CSV names and stat pattern."""
import struct
import csv
import json

STAGEBASE = r"..\..\Backup\assets\stageBase_EN.DAT"
OUTPUT = r"..\..\Mods\Monsters-Editor\monsters.json"

with open(STAGEBASE, 'rb') as f:
    data = f.read()

# Load monster names from CSV
monsters_csv = []
with open(r"table_sample\dokapon_monsters.csv", 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if row and len(row) >= 13 and row[1]:
            def safe_int(val):
                try:
                    val = ''.join(c for c in str(val) if c.isdigit() or c == '-')
                    return int(val) if val else 0
                except:
                    return 0
            
            monsters_csv.append({
                "name": row[1],
                "hp": safe_int(row[3]),
                "at": safe_int(row[4]),
                "df": safe_int(row[5]),
                "mg": safe_int(row[6]),
                "sp": safe_int(row[7]),
                "exp": safe_int(row[10]),
                "gold": safe_int(row[11]),
                "battle_skill": row[8] if len(row) > 8 else "",
                "offensive_magic": row[9] if len(row) > 9 else "",
                "defensive_magic": row[10] if len(row) > 10 else "",
                "drop1": row[12] if len(row) > 12 else "",
                "drop2": row[13] if len(row) > 13 else "",
                "special_drop": row[14] if len(row) > 14 else "",
            })

def read_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

print("=" * 70)
print("EXTRACTING MONSTER TABLE")
print("=" * 70)

monster_data = []

for monster in monsters_csv:
    name = monster["name"]
    try:
        name_bytes = name.encode('ascii')
    except:
        continue
    
    offset = data.find(name_bytes)
    if offset < 0:
        continue
    
    # Stats start after name + null terminator
    stats_offset = offset + len(name) + 1
    
    # Read stats: HP, AT, DF, SP, MG (5 uint16 = 10 bytes) - MG/SP swapped in DAT
    # Then EXP, Gold (2 uint16 = 4 bytes)
    if stats_offset + 14 > len(data):
        continue
    
    hp = read_uint16(data, stats_offset)
    at = read_uint16(data, stats_offset + 2)
    df = read_uint16(data, stats_offset + 4)
    sp = read_uint16(data, stats_offset + 6)  # DAT stores SP here
    mg = read_uint16(data, stats_offset + 8)  # DAT stores MG here
    exp = read_uint16(data, stats_offset + 10)
    gold = read_uint16(data, stats_offset + 12)
    
    monster_data.append({
        "name": name,
        "name_offset": offset,
        "stats_offset": stats_offset,
        "hp": hp,
        "at": at,
        "df": df,
        "mg": mg,
        "sp": sp,
        "exp": exp,
        "gold": gold,
        "csv_hp": monster["hp"],
        "csv_at": monster["at"],
        "csv_df": monster["df"],
        "csv_mg": monster["mg"],
        "csv_sp": monster["sp"],
        "csv_exp": monster["exp"],
        "csv_gold": monster["gold"],
        "battle_skill": monster["battle_skill"],
        "offensive_magic": monster["offensive_magic"],
        "defensive_magic": monster["defensive_magic"],
        "drop1": monster["drop1"],
        "drop2": monster["drop2"],
        "special_drop": monster["special_drop"],
    })
    
    match = "OK" if (hp == monster["hp"] and at == monster["at"] and df == monster["df"] and mg == monster["mg"] and sp == monster["sp"]) else "MISMATCH"
    print(f"{name:20} at 0x{offset:X}: HP={hp:3} AT={at:3} DF={df:3} MG={mg:3} SP={sp:3} EXP={exp:4} Gold={gold:4} {match}")

print(f"\nTotal monsters extracted: {len(monster_data)}")

# Save to JSON
import os
output_dir = os.path.dirname(OUTPUT)
os.makedirs(output_dir, exist_ok=True)

with open(OUTPUT, 'w') as f:
    json.dump(monster_data, f, indent=2)

print(f"\nSaved monster data to {OUTPUT}")
