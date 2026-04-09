"""
Parser for Dokapon Kingdom: Connect stageBase_EN.DAT files.
Reads known data structures and exports to/imports from JSON.
"""
import struct
import json
import os
from data_tables import (
    JOB_NAMES, PROFICIENCY_NAMES, BAG_TABLE_OFFSET, BAG_ENTRY_SIZE, BAG_ENTRY_COUNT,
    BAG_FIELDS, LEVELUP_TABLE_OFFSET, LEVELUP_ENTRY_SIZE, LEVELUP_STAT_SIZE,
    LEVELUP_ENTRY_COUNT, LEVELUP_STAT_FIELDS, SKILL_NAMES, DEF_MAGIC_NAMES,
    ATK_MAGIC_NAMES, KNOWN_ITEMS, KNOWN_EQUIPMENT, SHOP_ENTRIES, ENEMY_ENTRIES,
    STATUS_EFFECTS, FORMULA_TEXT_ENTRIES, AI_ASSIGNMENTS, AI_WEIGHT_TABLES,
    KNOWN_LOOT_TABLES, ITEM_FLAG_BITS, DAMAGE_FORMULA_OFFSET, DAMAGE_FORMULA_REGION_SIZE,
)


class StageBaseParser:
    MAGIC = b'@BAS'
    
    def __init__(self, filepath):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = bytearray(f.read())
        if self.data[:4] != self.MAGIC:
            raise ValueError(f"Not a valid @BAS file: {filepath}")
        self.file_size = len(self.data)
    
    def read_uint8(self, offset):
        return self.data[offset]
    
    def read_uint16(self, offset):
        return struct.unpack_from('<H', self.data, offset)[0]
    
    def read_uint32(self, offset):
        return struct.unpack_from('<I', self.data, offset)[0]
    
    def read_int32(self, offset):
        return struct.unpack_from('<i', self.data, offset)[0]
    
    def read_string(self, offset, max_len=256):
        end = self.data.index(0, offset, offset + max_len) if 0 in self.data[offset:offset+max_len] else offset + max_len
        return self.data[offset:end].decode('ascii', errors='replace')
    
    def read_bytes(self, offset, length):
        return bytes(self.data[offset:offset+length])
    
    def write_uint8(self, offset, value):
        self.data[offset] = value & 0xFF
    
    def write_uint16(self, offset, value):
        struct.pack_into('<H', self.data, offset, value)
    
    def write_uint32(self, offset, value):
        struct.pack_into('<I', self.data, offset, value)
    
    def write_bytes(self, offset, data_bytes):
        for i, b in enumerate(data_bytes):
            self.data[offset + i] = b
    
    def write_string(self, offset, text, max_len):
        encoded = text.encode('ascii')[:max_len - 1]
        for i in range(max_len):
            if i < len(encoded):
                self.data[offset + i] = encoded[i]
            else:
                self.data[offset + i] = 0
    
    def save(self, filepath=None):
        filepath = filepath or self.filepath
        with open(filepath, 'wb') as f:
            f.write(self.data)
    
    # =========================================================================
    # BAG DATA
    # =========================================================================
    
    def read_bag_data(self):
        bags = []
        for i in range(BAG_ENTRY_COUNT):
            offset = BAG_TABLE_OFFSET + i * BAG_ENTRY_SIZE
            class_idx = i // 2
            variant_idx = i % 2
            class_name = JOB_NAMES[class_idx] if class_idx < len(JOB_NAMES) else f"Unknown({class_idx})"
            bags.append({
                "index": i,
                "class": class_name,
                "class_id": class_idx,
                "variant": "male" if variant_idx == 0 else "female",
                "item_slots": self.read_uint8(offset),
                "magic_slots": self.read_uint8(offset + 1),
                "total_cap": self.read_uint8(offset + 2),
                "offset": f"0x{offset:X}",
            })
        return bags
    
    def write_bag_entry(self, index, item_slots, magic_slots):
        offset = BAG_TABLE_OFFSET + index * BAG_ENTRY_SIZE
        self.write_uint8(offset, item_slots)
        self.write_uint8(offset + 1, magic_slots)
    
    # =========================================================================
    # LEVEL-UP DATA
    # =========================================================================
    
    def read_levelup_data(self):
        entries = []
        for i in range(LEVELUP_ENTRY_COUNT):
            offset = LEVELUP_TABLE_OFFSET + i * LEVELUP_ENTRY_SIZE
            class_idx = i // 2
            variant = i % 2
            class_name = JOB_NAMES[class_idx] if class_idx < len(JOB_NAMES) else f"Unknown({class_idx})"
            stats = {}
            for field_name, field_def in LEVELUP_STAT_FIELDS.items():
                stats[field_name] = self.read_uint16(offset + field_def["offset"])
            entries.append({
                "index": i,
                "class": class_name,
                "class_id": class_idx,
                "variant": "male" if variant == 0 else "female",
                "stats": stats,
                "offset": f"0x{offset:X}",
            })
        return entries
    
    def write_levelup_entry(self, index, stats):
        offset = LEVELUP_TABLE_OFFSET + index * LEVELUP_ENTRY_SIZE
        for field_name, field_def in LEVELUP_STAT_FIELDS.items():
            if field_name in stats:
                self.write_uint16(offset + field_def["offset"], stats[field_name])
    
    # =========================================================================
    # ENEMY DATA
    # =========================================================================
    
    def read_enemy_data(self):
        enemies = {}
        for name, fields in ENEMY_ENTRIES.items():
            enemy = {"name": name}
            if "def_magic_offset" in fields:
                val = self.read_uint8(fields["def_magic_offset"])
                enemy["def_magic_id"] = val
                enemy["def_magic"] = DEF_MAGIC_NAMES.get(val, f"Unknown(0x{val:02X})")
                enemy["def_magic_offset"] = f"0x{fields['def_magic_offset']:X}"
            if "atk_magic_offset" in fields:
                val = self.read_uint8(fields["atk_magic_offset"])
                enemy["atk_magic_id"] = val
                enemy["atk_magic"] = ATK_MAGIC_NAMES.get(val, f"Unknown(0x{val:02X})")
                enemy["atk_magic_offset"] = f"0x{fields['atk_magic_offset']:X}"
            if "skill_offset" in fields:
                val = self.read_uint8(fields["skill_offset"])
                enemy["skill_id"] = val
                enemy["skill"] = SKILL_NAMES.get(val, f"Unknown(0x{val:02X})")
                enemy["skill_offset"] = f"0x{fields['skill_offset']:X}"
            if "name_suffix_offset" in fields:
                val = self.read_uint8(fields["name_suffix_offset"])
                enemy["name_suffix"] = chr(val) if 32 <= val < 127 else f"0x{val:02X}"
                enemy["name_suffix_offset"] = f"0x{fields['name_suffix_offset']:X}"
            enemies[name] = enemy
        return enemies
    
    # =========================================================================
    # STATUS EFFECTS
    # =========================================================================
    
    def read_status_effects(self):
        effects = {}
        for name, fields in STATUS_EFFECTS.items():
            effect = {"name": name}
            if "duration_offset" in fields:
                off = fields["duration_offset"]
                effect["min_duration"] = self.read_uint8(off)
                effect["max_duration"] = self.read_uint8(off + 1)
                effect["duration_offset"] = f"0x{off:X}"
            if "name_offset" in fields:
                effect["display_name"] = self.read_string(fields["name_offset"], 32)
            effects[name] = effect
        return effects
    
    # =========================================================================
    # SHOP DATA
    # =========================================================================
    
    def read_shop_data(self):
        shops = {}
        for name, entry in SHOP_ENTRIES.items():
            val = self.read_uint8(entry["offset"])
            shops[name] = {
                "item_id": val,
                "item_id_hex": f"0x{val:02X}",
                "original": entry.get("original", ""),
                "offset": f"0x{entry['offset']:X}",
            }
        return shops
    
    # =========================================================================
    # DAMAGE FORMULAS
    # =========================================================================
    
    def read_damage_formulas(self):
        formulas = {}
        for name, entry in FORMULA_TEXT_ENTRIES.items():
            text = self.read_string(entry["offset"], entry["max_len"])
            formulas[name] = {
                "text": text.rstrip(),
                "offset": f"0x{entry['offset']:X}",
                "max_len": entry["max_len"],
            }
        return formulas
    
    # =========================================================================
    # ITEMS
    # =========================================================================
    
    def read_known_items(self):
        items = {}
        for name, fields in KNOWN_ITEMS.items():
            item = {"name": name}
            if "name_offset" in fields:
                item["display_name"] = self.read_string(fields["name_offset"], fields.get("name_max_len", 32))
                item["name_offset"] = f"0x{fields['name_offset']:X}"
            if "price_offset" in fields:
                item["price"] = self.read_uint32(fields["price_offset"])
                item["price_offset"] = f"0x{fields['price_offset']:X}"
            if "flags_offset" in fields:
                val = self.read_uint8(fields["flags_offset"])
                item["flags"] = val
                item["flags_hex"] = f"0x{val:02X}"
                item["flags_desc"] = ITEM_FLAG_BITS.get(val, "Normal")
                item["flags_offset"] = f"0x{fields['flags_offset']:X}"
            if "description_offset" in fields:
                item["description"] = self.read_string(fields["description_offset"], fields.get("description_max_len", 128))
                item["description_offset"] = f"0x{fields['description_offset']:X}"
            items[name] = item
        return items
    
    # =========================================================================
    # EQUIPMENT
    # =========================================================================
    
    def read_known_equipment(self):
        equip = {}
        for name, fields in KNOWN_EQUIPMENT.items():
            item = {"name": name}
            if "percentage_offset" in fields:
                item["percentage"] = self.read_uint8(fields["percentage_offset"])
                item["percentage_offset"] = f"0x{fields['percentage_offset']:X}"
            if "stats_offset" in fields:
                off = fields["stats_offset"]
                sz = fields["stats_size"]
                raw = self.read_bytes(off, sz)
                if sz == 10:
                    item["stats"] = {
                        "attack": struct.unpack_from('<H', raw, 0)[0],
                        "defense": struct.unpack_from('<H', raw, 2)[0],
                        "magic": struct.unpack_from('<H', raw, 4)[0],
                        "speed": struct.unpack_from('<H', raw, 6)[0],
                        "hp": struct.unpack_from('<H', raw, 8)[0],
                    }
                else:
                    item["stats_raw"] = raw.hex()
                item["stats_offset"] = f"0x{off:X}"
            if "class_req_offset" in fields:
                val = self.read_uint8(fields["class_req_offset"])
                item["class_req_id"] = val
                item["class_req"] = PROFICIENCY_NAMES.get(val, f"Unknown({val})")
                item["class_req_offset"] = f"0x{fields['class_req_offset']:X}"
            equip[name] = item
        return equip
    
    # =========================================================================
    # AI DATA
    # =========================================================================
    
    def read_ai_assignments(self):
        assignments = {}
        for name, offset in AI_ASSIGNMENTS.items():
            val = self.read_uint8(offset)
            assignments[name] = {
                "ai_value": val,
                "offset": f"0x{offset:X}",
            }
        return assignments
    
    def read_ai_weight_tables(self):
        tables = {}
        for name, entry in AI_WEIGHT_TABLES.items():
            off = entry["offset"]
            weights = {}
            for i, field in enumerate(entry["fields"]):
                weights[field] = self.read_uint8(off + i)
            tables[name] = {
                "weights": weights,
                "offset": f"0x{off:X}",
            }
        return tables
    
    # =========================================================================
    # STRING SCANNER
    # =========================================================================
    
    def scan_strings(self, min_length=4):
        """Scan the entire file for ASCII strings."""
        strings = []
        current = b""
        start = 0
        for i, b in enumerate(self.data):
            if 32 <= b < 127:
                if not current:
                    start = i
                current += bytes([b])
            else:
                if len(current) >= min_length:
                    strings.append({
                        "offset": f"0x{start:X}",
                        "offset_dec": start,
                        "text": current.decode('ascii', errors='replace'),
                    })
                current = b""
        return strings
    
    # =========================================================================
    # FULL EXPORT
    # =========================================================================
    
    def export_all(self):
        """Export all known data structures to a dictionary."""
        return {
            "file_info": {
                "path": self.filepath,
                "size": self.file_size,
                "magic": self.data[:4].decode('ascii'),
            },
            "bags": self.read_bag_data(),
            "level_ups": self.read_levelup_data(),
            "enemies": self.read_enemy_data(),
            "status_effects": self.read_status_effects(),
            "shops": self.read_shop_data(),
            "damage_formulas": self.read_damage_formulas(),
            "items": self.read_known_items(),
            "equipment": self.read_known_equipment(),
            "ai_assignments": self.read_ai_assignments(),
            "ai_weight_tables": self.read_ai_weight_tables(),
        }
    
    def export_json(self, output_path):
        """Export all data to a JSON file."""
        data = self.export_all()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path
    
    # =========================================================================
    # IMPORT FROM JSON
    # =========================================================================
    
    def import_json(self, json_path):
        """Import edited data from a JSON file and apply changes."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        changes = []
        
        # Apply bag changes
        if "bags" in data:
            for bag in data["bags"]:
                idx = bag["index"]
                offset = BAG_TABLE_OFFSET + idx * BAG_ENTRY_SIZE
                old_items = self.read_uint8(offset)
                old_magic = self.read_uint8(offset + 1)
                new_items = bag["item_slots"]
                new_magic = bag["magic_slots"]
                if old_items != new_items or old_magic != new_magic:
                    self.write_bag_entry(idx, new_items, new_magic)
                    changes.append(f"Bag {bag['class']} ({bag['variant']}): {old_items}/{old_magic} -> {new_items}/{new_magic}")
        
        # Apply level-up changes
        if "level_ups" in data:
            for entry in data["level_ups"]:
                idx = entry["index"]
                self.write_levelup_entry(idx, entry["stats"])
                changes.append(f"Level-up {entry['class']} ({entry['variant']}): updated stats")
        
        # Apply enemy changes
        if "enemies" in data:
            for name, enemy in data["enemies"].items():
                fields = ENEMY_ENTRIES.get(name, {})
                if "def_magic_id" in enemy and "def_magic_offset" in fields:
                    self.write_uint8(fields["def_magic_offset"], enemy["def_magic_id"])
                    changes.append(f"Enemy {name}: def magic -> {enemy['def_magic_id']}")
                if "atk_magic_id" in enemy and "atk_magic_offset" in fields:
                    self.write_uint8(fields["atk_magic_offset"], enemy["atk_magic_id"])
                    changes.append(f"Enemy {name}: atk magic -> {enemy['atk_magic_id']}")
                if "skill_id" in enemy and "skill_offset" in fields:
                    self.write_uint8(fields["skill_offset"], enemy["skill_id"])
                    changes.append(f"Enemy {name}: skill -> {enemy['skill_id']}")
        
        # Apply status effect changes
        if "status_effects" in data:
            for name, effect in data["status_effects"].items():
                fields = STATUS_EFFECTS.get(name, {})
                if "duration_offset" in fields:
                    off = fields["duration_offset"]
                    if "min_duration" in effect:
                        self.write_uint8(off, effect["min_duration"])
                    if "max_duration" in effect:
                        self.write_uint8(off + 1, effect["max_duration"])
                    changes.append(f"Status {name}: duration -> {effect.get('min_duration')}-{effect.get('max_duration')}")
        
        # Apply shop changes
        if "shops" in data:
            for name, shop in data["shops"].items():
                entry = SHOP_ENTRIES.get(name, {})
                if "offset" in entry and "item_id" in shop:
                    self.write_uint8(entry["offset"], shop["item_id"])
                    changes.append(f"Shop {name}: item -> 0x{shop['item_id']:02X}")
        
        # Apply damage formula text changes
        if "damage_formulas" in data:
            for name, formula in data["damage_formulas"].items():
                entry = FORMULA_TEXT_ENTRIES.get(name, {})
                if "offset" in entry and "text" in formula:
                    self.write_string(entry["offset"], formula["text"], entry["max_len"])
                    changes.append(f"Formula {name}: text -> '{formula['text']}'")
        
        # Apply AI assignment changes
        if "ai_assignments" in data:
            for name, assignment in data["ai_assignments"].items():
                if name in AI_ASSIGNMENTS and "ai_value" in assignment:
                    self.write_uint8(AI_ASSIGNMENTS[name], assignment["ai_value"])
                    changes.append(f"AI {name}: value -> {assignment['ai_value']}")
        
        return changes
