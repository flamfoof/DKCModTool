"""
Known data structure definitions for Dokapon Kingdom: Connect stageBase_EN.DAT.
All offsets are relative to the start of the stageBase_EN.DAT file.
Derived from reverse-engineering and the JaJo's Balance Patch changelog.
"""

# =============================================================================
# CLASS / JOB DEFINITIONS
# =============================================================================

JOB_NAMES = [
    "Warrior", "Magician", "Thief", "Cleric",
    "Spellsword", "Alchemist", "Ninja", "Monk",
    "Acrobat", "Robo Knight", "Hero", "Darkling"
]

# Proficiency IDs used for weapon/equipment class requirements (1-based)
PROFICIENCY_NAMES = {
    0: "Any",
    1: "Warrior",
    2: "Magician",
    3: "Thief",
    4: "Cleric",
    5: "Spellsword",
    6: "Alchemist",
    7: "Ninja",
    8: "Monk",
    9: "Acrobat",
    10: "Robo Knight",
    11: "Hero",
}

JOB_IDS = {name: i for i, name in enumerate(JOB_NAMES)}

# --- Bag Data ---
# Each entry: [item_slots, magic_slots, total_cap, 0, 0, 0, class_idx, variant]
# Two entries per class (male=0, female=1)
BAG_TABLE_OFFSET = 0x1884E
BAG_ENTRY_SIZE = 8
BAG_ENTRY_COUNT = 20  # 10 classes x 2 variants (first 10 classes)

BAG_FIELDS = {
    "item_slots":  {"offset": 0, "size": 1, "type": "uint8"},
    "magic_slots": {"offset": 1, "size": 1, "type": "uint8"},
    "total_cap":   {"offset": 2, "size": 1, "type": "uint8"},
    "padding1":    {"offset": 3, "size": 1, "type": "uint8"},
    "padding2":    {"offset": 4, "size": 1, "type": "uint8"},
    "padding3":    {"offset": 5, "size": 1, "type": "uint8"},
    "class_idx":   {"offset": 6, "size": 1, "type": "uint8"},
    "variant":     {"offset": 7, "size": 1, "type": "uint8"},
}

# --- Level-Up Stat Bonuses ---
# 10 bytes of stats within a 28-byte record
# Format: [att, 0, def, 0, mag, 0, spd, 0, hp, 0]
LEVELUP_TABLE_OFFSET = 0x185AE
LEVELUP_ENTRY_SIZE = 28  # 0x1C
LEVELUP_STAT_SIZE = 10
LEVELUP_ENTRY_COUNT = 24  # 12 classes x 2 variants (male/female)

LEVELUP_STAT_FIELDS = {
    "attack":  {"offset": 0, "size": 2, "type": "uint16"},
    "defense": {"offset": 2, "size": 2, "type": "uint16"},
    "magic":   {"offset": 4, "size": 2, "type": "uint16"},
    "speed":   {"offset": 6, "size": 2, "type": "uint16"},
    "hp":      {"offset": 8, "size": 2, "type": "uint16"},
}

# --- Skill Data ---
# Skill assignment per class
# Each class has skill entries with skill IDs
SKILL_TABLE_ENTRIES = {
    "Warrior_skill1":      {"offset": 0x18348, "size": 1},
    "Warrior_skill2":      {"offset": 0x18354, "size": 1},
    "Magician_skill1":     {"offset": 0x18360, "size": 1},  # Note: This was Thief in changelog
    "Thief_skill1":        {"offset": 0x18360, "size": 1},
    "Thief_skill2":        {"offset": 0x1836C, "size": 1},
    "Alchemist_skill1":    {"offset": 0x183A7, "size": 1},
    "Alchemist_skill2":    {"offset": 0x183B3, "size": 1},
}

SKILL_NAMES = {
    0x00: "None",
    0x01: "Charge",
    0x02: "Muscle",
    0x03: "Hustle",
    0x04: "Escape",
    0x05: "Celerity",
    0x06: "Concentrate",
    0x07: "Super Cure",
    0x08: "Alchemy",
    0x09: "Bounty",
    0x0A: "Vanish",
    0x0B: "Poison",
    0x0C: "Counter",
    0x0D: "Focus",
    0x0E: "Steal",
    0x0F: "Pierce",
    0x10: "Transform",
    0x11: "Robo Laser",
    0x12: "Robo Punch",
    0x13: "Item Snatch",
}


# --- Class Level-Up Battle Requirements ---
# Battles required to level up each class level
# Structure: [class_id, variant, battle_count, 0x00, 0x3E, 0x00, 0x00, 0x00]
# Entry size: 8 bytes
# 24 entries (12 classes x 2 variants)
BATTLE_REQ_OFFSET = 0x1768C
BATTLE_REQ_ENTRY_SIZE = 8
BATTLE_REQ_ENTRY_COUNT = 24

# --- Job Unlock Requirements ---
JOB_UNLOCK_OFFSET = 0x18B60
JOB_UNLOCK_ENTRY_SIZE = 16

# =============================================================================
# ITEM DEFINITIONS
# =============================================================================

# Item name table - variable length entries in a larger block
# Each item has: name (null-terminated), price (4 bytes), and other properties
ITEM_TABLE_REGION_START = 0xE000
ITEM_TABLE_REGION_END = 0x11000

# Known individual item locations (from changelog)
KNOWN_ITEMS = {
    "Hero License / Gold Voucher": {
        "name_offset": 0xE498,
        "name_max_len": 16,
        "price_offset": 0xE4A8,
        "price_size": 4,
        "flags_offset": 0xFC1E,
        "description_offset": 0x10DA4,
        "description_max_len": 128,
    },
    "Angel Wings": {
        "description_offset": 0x10C88,
        "description_max_len": 96,
    },
    "Magic Medicine": {
        "flags_offset": 0xFB6E,
    },
    "Charm Potion": {
        "flags_offset": 0xFBDE,
    },
}

# Item flags byte meanings
ITEM_FLAG_BITS = {
    0x10: "Cannot Duplicate",
    0x20: "Cannot Duplicate (alt)",
    0x30: "Cannot Duplicate + Cannot Sell",
    0x40: "Quest Item",
    0x68: "Special Quest Item",
}

# =============================================================================
# EQUIPMENT DEFINITIONS
# =============================================================================

# Equipment data region
WEAPON_TABLE_REGION_START = 0x7000
WEAPON_TABLE_REGION_END = 0x9800

SHIELD_TABLE_REGION_START = 0xA000
SHIELD_TABLE_REGION_END = 0xB000

# Known equipment locations
KNOWN_EQUIPMENT = {
    "M Guard DX": {
        "percentage_offset": 0x14F08,
        "percentage_size": 1,
    },
    "Wabbit Shield": {
        "stats_offset": 0xAC10,
        "stats_size": 10,  # [att, def, mag, spd, hp] as uint16 LE
    },
    "Dragon Guandao": {
        "class_req_offset": 0x8519,
        "class_req_size": 1,
    },
    "Ichimonji Katana": {
        "class_req_offset": 0x87A9,
        "class_req_size": 1,
    },
    "Nihilist Sword": {
        "class_req_offset": 0x8DC9,
        "class_req_size": 1,
    },
}

# =============================================================================
# SHOP DEFINITIONS
# =============================================================================

# Shop item ID entries at known offsets
SHOP_ENTRIES = {
    "Clovis_slot": {"offset": 0x51CC, "size": 1, "original": "Purse Cutter"},
    "Lava Cave_slot": {"offset": 0x51E3, "size": 1, "original": "Come Here"},
    "Afrike_weapon": {"offset": 0x5086, "size": 1, "original": "Longbow"},
    "Afrike_magic1": {"offset": 0x5207, "size": 1, "original": "Lockdown"},
    "Afrike_magic2": {"offset": 0x520E, "size": 1, "original": "Banish"},
    "Afrike_dmagic": {"offset": 0x5213, "size": 1, "original": "M Guard DX"},
    "Underground_magic1": {"offset": 0x5219, "size": 1, "original": "Lockdown"},
    "Underground_dmagic": {"offset": 0x5224, "size": 1, "original": "M Guard DX"},
    "Flinders_magic1": {"offset": 0x522D, "size": 1, "original": "Lockdown"},
    "Flinders_magic2": {"offset": 0x5233, "size": 1, "original": "Banish"},
    "Flinders_dmagic": {"offset": 0x5238, "size": 1, "original": "M Guard DX"},
    "Tower_item": {"offset": 0x5160, "size": 1, "original": "Charm Potion"},
    "Tower_magic1": {"offset": 0x5244, "size": 1, "original": "Giga Blaze"},
    "Tower_dmagic": {"offset": 0x5249, "size": 1, "original": "Refresh DX"},
}

# =============================================================================
# ENEMY DEFINITIONS
# =============================================================================

# Known enemy field offsets
ENEMY_ENTRIES = {
    "Rogue": {"def_magic_offset": 0x1B041},
    "Barbarian": {"skill_offset": 0x1B092},
    "Halfling": {"def_magic_offset": 0x1B0DD},
    "Ninja": {"def_magic_offset": 0x1B129},
    "Orc": {"skill_offset": 0x1B276},
    "Roc": {"def_magic_offset": 0x1B665},
    "Bat": {"def_magic_offset": 0x1B6A9},
    "Demon Bat": {"def_magic_offset": 0x1B6D1},
    "Scorpion-G": {"def_magic_offset": 0x1B799},
    "Sea Scorpion": {"def_magic_offset": 0x1B7C5},
    "Spider-G": {"def_magic_offset": 0x1B7ED},
    "Tarantula": {"def_magic_offset": 0x1B815},
    "Crawler": {"def_magic_offset": 0x1B839},
    "Worm": {"def_magic_offset": 0x1B85D},
    "Mycopath": {"def_magic_offset": 0x1B981},
    "Killer Fish": {"def_magic_offset": 0x1BA19},
    "Gunfish": {"def_magic_offset": 0x1BA3D},
    "Skeleton": {"def_magic_offset": 0x1BBD5},
    "Red Bones": {"def_magic_offset": 0x1BBFD},
    "Bone Knight": {"def_magic_offset": 0x1BC25},
    "Iron Golem": {"def_magic_offset": 0x1BD01},
    "Doppelganger": {"def_magic_offset": 0x1BD51},
    "Lich": {"def_magic_offset": 0x1BD75},
    "Demon's Guard": {"def_magic_offset": 0x1BFA9, "atk_magic_offset": 0x1BFAA},
    "Overlord Rico (Final)": {"def_magic_offset": 0x1C219},
    "Skeleton (Boss)": {"name_suffix_offset": 0x1C39C, "def_magic_offset": 0x1C3AD},
    "Red Bones (Boss)": {"name_suffix_offset": 0x1C3C5, "def_magic_offset": 0x1C3D5},
    "Dwarf (Boss)": {"name_suffix_offset": 0x1C3E9, "def_magic_offset": 0x1C3F9},
    "Squilla (Boss)": {"name_suffix_offset": 0x1C40F, "def_magic_offset": 0x1C41D},
    "Unseelie (Boss)": {"name_suffix_offset": 0x1C434, "def_magic_offset": 0x1C445},
}

DEF_MAGIC_NAMES = {
    0x00: "None",
    0x01: "M Guard",
    0x02: "M Guard+",
    0x03: "M Guard DX",
    0x04: "Bounce",
    0x05: "Reflect",
    0x06: "Refresh",
    0x07: "Super Cure",
    0x08: "Cure",
    0x09: "Absorb",
    0x0A: "Barrier",
    0x0B: "Mirror",
}

ATK_MAGIC_NAMES = {
    0x00: "None",
    0x01: "Fireball",
    0x02: "Blaze",
    0x03: "Mega Blaze",
    0x04: "Giga Blaze",
    0x05: "Iceball",
    0x06: "Ice Barrage",
    0x07: "Mega Ice",
    0x08: "Giga Ice",
    0x09: "Ice Barrage",
    0x0A: "Lightning",
    0x0B: "Guster",
    0x0C: "Psychokinesis",
    0x0D: "Heckfire",
    0x13: "Banish",
    0x1A: "Quake",
    0x2B: "Heckfire",
}

# =============================================================================
# STATUS EFFECT DEFINITIONS
# =============================================================================

STATUS_EFFECTS = {
    "Squeeze": {"duration_offset": 0x1A670, "name_offset": 0x1A674},
    "Petrify": {"duration_offset": 0x1A6AC, "name_offset": 0x1A6B0},
    "Sealed": {"duration_offset": 0x1AA98},
    "Invisible": {"duration_offset": 0x1AB04},
}
# Duration format: [min_turns, max_turns] (2 bytes)

# =============================================================================
# DAMAGE FORMULA DEFINITIONS
# =============================================================================

# Damage formula entries start around 0xB0DC0
# Each formula has: ID (4 bytes), display_type (4 bytes), display_text (17 bytes), padding,
#                   actual_formula_id (4 bytes), formula_data (variable)
DAMAGE_FORMULA_OFFSET = 0xB0DC0
DAMAGE_FORMULA_REGION_SIZE = 0x300

DAMAGE_FORMULA_ENTRY_SIZE = 0x2C  # approximate, varies

# Known formula text offsets
FORMULA_TEXT_ENTRIES = {
    "Attack ID 1": {"offset": 0xB0DEC, "max_len": 17},
    "Magic ID 1": {"offset": 0xB0E44, "max_len": 12},
    "Strike ID 1": {"offset": 0xB0EA4, "max_len": 17},
    "Counter ID 1": {"offset": 0xB0F00, "max_len": 17},
    "Curse ID 1": {"offset": 0xB0F4C, "max_len": 12},
}

# =============================================================================
# LOOT TABLE DEFINITIONS
# =============================================================================

LOOT_TABLE_REGION_START = 0x3F00
LOOT_TABLE_REGION_END = 0x5000

# Known loot tables
KNOWN_LOOT_TABLES = {
    "Table 15": {"offset": 0x40A0},
    "Table 58": {"offset": 0x4C68},
}

# =============================================================================
# AI TABLE DEFINITIONS
# =============================================================================

# AI table entries: 8 bytes each
# [monster_id, ai_table_id, ?, ?, weight_value, 0, 0, 0]
AI_TABLE_REGION_START = 0x1E1C0
AI_TABLE_REGION_END = 0x1E420

# AI weight tables at known offsets
AI_WEIGHT_TABLES = {
    "Table 24 (Wallace)": {
        "offset": 0x1E3F0,
        "fields": ["ai_id", "att_wt", "omag_wt", "skill_wt", "strike_wt", "def_wt", "counter_wt", "dmag_wt"],
    },
    "Table 25 (Boss)": {
        "offset": 0x1E3FD,
        "fields": ["att_wt", "omag_wt", "skill_wt", "strike_wt", "def_wt", "counter_wt", "dmag_wt"],
    },
}

# Known AI assignment offsets (monster -> ai table)
AI_ASSIGNMENTS = {
    "Demon's Guard": 0x1E1CA,
    "Rico Jr.": 0x1E23A,
    "Overlord Rico": 0x1E242,
    "Overlord Rico (Final)": 0x1E24A,
    "Clonus 1": 0x1E25A,
    "Clonus 2": 0x1E262,
    "Clonus 3": 0x1E26A,
    "Clonus 4": 0x1E272,
    "Robo-Sassin": 0x1E292,
    "Skeleton (Boss)": 0x1E2A2,
    "Red Bones (Boss)": 0x1E2AA,
    "Dwarf (Boss)": 0x1E2B2,
    "Squilla (Boss)": 0x1E2BA,
    "Unseelie (Boss)": 0x1E2C2,
    "Rico Jr. (Overworld)": 0x1E2CA,
}

# =============================================================================
# MAP / TILE DEFINITIONS (per stage file)
# =============================================================================

# These are in separate stg###_EN.DAT files, not stageBase
# stg019 = Underworld, stg022 = Prologue
TILE_ENTRIES = {
    "stg019": {
        "Underworld Locked Box type": {"offset": 0x7E0, "size": 1},
        "Underworld Locked Box table": {"offset": 0x7E4, "size": 2},
    },
    "stg022": {
        "Prologue Bridge 1": {"offset": 0x598, "size": 1},
        "Prologue Bridge 2": {"offset": 0x5A8, "size": 1},
        "Prologue Bridge 3": {"offset": 0x5B8, "size": 1},
    },
}
