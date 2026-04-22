"""Find bytes in stageBase_EN.DAT records that are NOT yet mapped to a
named field, so we can surface them as candidate modifiable properties.

Scope (all driven by existing memory-map JSON in this folder):
  - Weapons   : 20-byte data block, known mapped = bytes 0..18, byte 18-19 = `trail`
  - Shields   : same layout (meta[2..4] differ)
  - Accessories: same layout (meta[2..4] differ)
  - Monsters  : 36-byte record, known `_reserved_10` and `_reserved_15` unmapped

For each unmapped byte position we emit:
  - position (byte offset within record data block)
  - per-record values aligned with names
  - value histogram
  - variance hints (constant, boolean, small int, wide int, mostly zero)

Output: analysis_tools/unmapped_fields_report.json
Also prints a compact summary.
"""
from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
DAT_PATH  = Path(
    r"H:\Connect Mod Installer v2.0.0\Backup\assets\stageBase_EN.DAT"
)


def as_int(v) -> int | None:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        try:
            return int(v, 0)
        except ValueError:
            return None
    return None


def classify_values(values: list[int]) -> dict:
    """Return a loose classification of a column of byte values."""
    uniq = sorted(set(values))
    info: dict = {
        "count":           len(values),
        "distinct":        len(uniq),
        "min":             min(values) if values else None,
        "max":             max(values) if values else None,
        "nonzero_count":   sum(1 for v in values if v != 0),
    }
    info["top"] = Counter(values).most_common(8)
    if len(uniq) == 1:
        info["kind"] = "constant"
    elif len(uniq) == 2 and set(uniq) <= {0, 1}:
        info["kind"] = "boolean"
    elif info["max"] is not None and info["max"] <= 15:
        info["kind"] = "nibble_or_enum"
    elif info["max"] is not None and info["max"] <= 0xFF and info["nonzero_count"] < info["count"] // 4:
        info["kind"] = "sparse_flag"
    else:
        info["kind"] = "byte_var"
    return info


# ---------------------------------------------------------------------------
# Equipment: weapons / shields / accessories
# ---------------------------------------------------------------------------

# Which byte offsets within the 20-byte data block are already mapped
# to a named field, per the existing extractor (map_all_equipment.py):
#   [0..4]   meta bytes           -> named (sub_rank/job/effect_chance/rarity)
#   [4..8]   price (u32)          -> named
#   [8..18]  5 x int16 stats      -> named (attack/defense/magic/speed/hp)
#   [18..20] trail                -> UNMAPPED
EQUIP_DATA_SIZE = 20
EQUIP_MAPPED_BYTES = set(range(0, 18))
EQUIP_UNMAPPED_BYTES = sorted(set(range(EQUIP_DATA_SIZE)) - EQUIP_MAPPED_BYTES)


def scan_equipment(dat: bytes, category_name: str, entries: list[dict]) -> dict:
    rows: list[dict] = []
    for e in entries:
        data_off = as_int(e.get("data_offset"))
        if data_off is None:
            continue
        block = dat[data_off : data_off + EQUIP_DATA_SIZE]
        if len(block) < EQUIP_DATA_SIZE:
            continue
        row = {
            "name":        e.get("name"),
            "item_id":     e.get("item_id"),
            "data_offset": f"0x{data_off:05X}",
            "unmapped":    {f"+{pos:02X}": block[pos] for pos in EQUIP_UNMAPPED_BYTES},
            # Pair interpretation of the two trail bytes
            "trail_u16":   struct.unpack_from("<H", block, 18)[0],
            "trail_i16":   struct.unpack_from("<h", block, 18)[0],
            "trail_hex":   block[18:20].hex(),
        }
        rows.append(row)

    # Column stats per unmapped byte position
    columns: dict[str, dict] = {}
    for pos in EQUIP_UNMAPPED_BYTES:
        col = [r["unmapped"][f"+{pos:02X}"] for r in rows]
        columns[f"+{pos:02X}"] = classify_values(col)

    # Also analyse the u16 pair
    u16_col = [r["trail_u16"] for r in rows]
    columns["trail_u16"] = classify_values(u16_col)

    return {"entries": rows, "columns": columns}


# ---------------------------------------------------------------------------
# Monsters: use `_reserved_10` and `_reserved_15` fields from the map
# ---------------------------------------------------------------------------

def scan_monsters(dat: bytes, mon_map: dict) -> dict:
    entries = mon_map.get("entries") or []
    rows: list[dict] = []
    record_size = 0
    tbl = mon_map.get("table") or {}
    if isinstance(tbl, dict):
        rs = as_int(tbl.get("record_size") or tbl.get("entry_size"))
        if rs:
            record_size = rs

    # Extract every `_reserved_*` field the map already exposes, so we
    # don't hard-code byte offsets we can't verify.
    sample = entries[0] if entries else {}
    reserved_keys = [k for k in sample if k.startswith("_reserved")]

    reserved_cols: dict[str, list[int]] = {k: [] for k in reserved_keys}

    for e in entries:
        hdr_off   = as_int(e.get("header_offset"))
        stats_off = as_int(e.get("stats_offset"))
        rec_sz    = as_int(e.get("record_size")) or record_size
        base_off  = hdr_off or stats_off
        row = {
            "name":          e.get("name"),
            "self_id":       e.get("self_id"),
            "header_offset": e.get("header_offset"),
            "stats_offset":  e.get("stats_offset"),
            "record_size":   rec_sz,
            "reserved":      {k: e.get(k) for k in reserved_keys},
        }
        for k in reserved_keys:
            v = e.get(k)
            if isinstance(v, int):
                reserved_cols[k].append(v)

        # Also raw-dump the bytes of the record so we can eyeball
        # positions not covered by either named or `_reserved_*` fields.
        if base_off is not None and rec_sz:
            row["raw_hex"] = dat[base_off : base_off + rec_sz].hex()
        rows.append(row)

    columns = {k: classify_values(v) for k, v in reserved_cols.items() if v}

    return {
        "record_size":  record_size,
        "reserved_keys": reserved_keys,
        "entries":      rows,
        "columns":      columns,
    }


# ---------------------------------------------------------------------------

def main() -> None:
    dat = DAT_PATH.read_bytes()

    equip = json.loads((TOOLS_DIR / "equipment_memory_map.json").read_text())
    mon   = json.loads((TOOLS_DIR / "monsters_memory_map.json").read_text())

    report: dict = {
        "dat_path":      str(DAT_PATH),
        "dat_size":      len(dat),
        "generated_by":  "find_unmapped_fields.py",
        "equipment":     {},
        "monsters":      {},
    }

    print(f"DAT: {DAT_PATH}  ({len(dat):,} bytes)")
    print("=" * 78)

    for cat in ("weapons", "shields", "accessories"):
        entries = equip.get(cat) or []
        if not entries:
            continue
        out = scan_equipment(dat, cat, entries)
        report["equipment"][cat] = out

        print(f"\n[{cat}]  {len(out['entries'])} records, 20-byte data block")
        print(f"  Unmapped byte positions: {EQUIP_UNMAPPED_BYTES}")
        for col, stats in out["columns"].items():
            top_str = ", ".join(f"{v}:{c}" for v, c in stats["top"][:5])
            print(f"    {col:10s}  kind={stats['kind']:14s}  "
                  f"distinct={stats['distinct']:3d}  "
                  f"min={stats['min']}  max={stats['max']}  "
                  f"top=[{top_str}]")

    print()
    print("=" * 78)
    out = scan_monsters(dat, mon)
    report["monsters"] = out
    print(f"\n[monsters]  {len(out['entries'])} records, "
          f"record_size={out['record_size']}")
    print(f"  reserved keys in map: {out['reserved_keys']}")
    for col, stats in out["columns"].items():
        top_str = ", ".join(f"{v}:{c}" for v, c in stats["top"][:5])
        print(f"    {col:20s}  kind={stats['kind']:14s}  "
              f"distinct={stats['distinct']:3d}  "
              f"min={stats['min']}  max={stats['max']}  "
              f"top=[{top_str}]")

    out_file = TOOLS_DIR / "unmapped_fields_report.json"
    out_file.write_text(json.dumps(report, indent=2))
    print(f"\n[OK] wrote {out_file}")


if __name__ == "__main__":
    main()
