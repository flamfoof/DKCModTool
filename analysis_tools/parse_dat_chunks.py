"""Parse stageBase_EN.DAT at the chunk level using the schema reversed
from FUN_1402A2240 (the DAT loader) and the 13-entry dispatch table at
PTR_FUN_1404A5F58.

STATUS: Exploratory only.
    The raw stageBase_EN.DAT on disk does NOT match the tag/size chunk
    schema reversed from the EXE. The loader calls FUN_14003B110 to
    decompress / transform the file into an in-memory buffer before the
    chunk loop walks it. We have not yet reversed that decompressor, so
    this script cannot classify the raw file.

    What we DO know for modding purposes:
      - Equipment, class-stats, skill, and monster records live at
        hard-coded raw-file offsets (0x70FC, 0x9884, 0x1733E, etc.)
        because they are either stored verbatim or their positions are
        stable after any decompression transform.
      - The existing editors in DKCModTool/analysis_tools and
        Mods/*-Editor operate on those raw offsets directly and work.

    Parsing at the chunk level is not required to mod these tables. It
    would only become necessary for e.g. inserting *new* records, which
    requires understanding the container's post-decomp layout.

This file is kept as a scaffold. Rerun once FUN_14003B110 is reversed
and the decompressed buffer can be written to a temp file for parsing.

Chunk format (confirmed from decomp):
    u32 tag         # index 0..12 into dispatch table
    u32 size        # bytes of payload
    u8  data[size]  # opaque, handled by dispatch[tag]

Two chunk streams separated by the sentinel tag 0x52484340 (`@CHR`
little-endian). The loader walks stream A, finds `@CHR`, then walks
stream B.

This script:
  1. Locates the decompressed chunk region (the DAT file has a small
     header; payload starts at the offset recorded in the first 8 bytes
     — we probe).
  2. Walks chunks and records (offset, tag, size, first_16_bytes).
  3. Cross-references recorded chunk offsets against the equipment,
     class-stats, skills, and monster memory maps to identify which tag
     is responsible for which data.
  4. Writes `analysis_tools/dat_chunk_map.json`.

Usage:
    python parse_dat_chunks.py [path/to/stageBase_EN.DAT]

Default path is the vanilla backup copy.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

DEFAULT_DAT = Path(
    r"H:\Connect Mod Installer v2.0.0\Backup\assets\stageBase_EN.DAT"
)

# Tag 0 handler returns 0 (terminator). Sentinel "@CHR" in little-endian u32.
TAG_TERMINATOR = 0
CHR_SENTINEL   = 0x52484340  # bytes: 40 43 48 52 == '@CHR'

# Hand-derived names for the 13 tags, based on dispatch-handler sizes
# and decompilation. Tags 1-4, 7-11 are micro-helpers; tags 5/6/12 are
# the data-emitting handlers.
TAG_NAMES = {
    0:  "END",
    1:  "skip_size",
    2:  "dec_counter_at_0x70",
    3:  "set_ctx_at_0x68",
    4:  "get_ctx_at_0x68",
    5:  "named_subresource",     # calls FUN_1402B2F00(root, name+"_EN")
    6:  "store_ptr_at_0x10",     # emits data region ptr
    7:  "small_helper_7",
    8:  "small_helper_8",
    9:  "small_helper_9",
    10: "small_helper_A",
    11: "small_helper_B",
    12: "store_ptr_at_0x18",     # emits data region ptr
}

# Known memory-map offsets inside stageBase_EN.DAT.
# Values below are the START offset of each data block within the DAT
# payload (before any unpacking). We use them to identify the chunk
# that contains each region: the chunk whose [offset, offset+size)
# window covers the memory-map start offset.
KNOWN_REGIONS = {
    # Filled lazily from the JSON memory maps when available.
}


def _as_int(v) -> int | None:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        try:
            return int(v, 0)
        except ValueError:
            return None
    return None


def try_load_region_starts(tools_dir: Path) -> dict[str, int]:
    """Read memory-map JSONs and extract representative file offsets."""
    starts: dict[str, int] = {}
    eq = tools_dir / "equipment_memory_map.json"
    if eq.exists():
        data = json.loads(eq.read_text())
        for key in ("weapons", "shields", "accessories", "items"):
            lst = data.get(key) or []
            if isinstance(lst, list) and lst:
                vals = [_as_int(e.get("header_offset") or e.get("data_offset"))
                        for e in lst if isinstance(e, dict)]
                vals = [v for v in vals if v is not None]
                if vals:
                    starts[f"equipment.{key}"] = min(vals)

    cs = tools_dir / "class_stats_memory_map.json"
    if cs.exists():
        data = json.loads(cs.read_text())
        for k in ("levelup_table", "bag_table", "battle_req_table"):
            v = data.get(k)
            if isinstance(v, dict):
                off = _as_int(v.get("offset") or v.get("start_offset"))
                if off is not None:
                    starts[f"class_stats.{k}"] = off

    sk = tools_dir / "skill_tables_memory_map.json"
    if sk.exists():
        data = json.loads(sk.read_text())
        for k in ("field_skills_table", "battle_skills_table"):
            v = data.get(k)
            if isinstance(v, dict):
                off = _as_int(v.get("start_offset") or v.get("offset"))
                if off is not None:
                    starts[f"skills.{k}"] = off

    mo = tools_dir / "monsters_memory_map.json"
    if mo.exists():
        data = json.loads(mo.read_text())
        v = data.get("table") or data.get("monsters_table")
        if isinstance(v, dict):
            off = _as_int(v.get("start_offset") or v.get("offset"))
            if off is not None:
                starts["monsters"] = off
        # Also use the first entry's header_offset as a backup
        entries = data.get("entries") or []
        if entries and isinstance(entries[0], dict):
            off = _as_int(entries[0].get("header_offset"))
            if off is not None and "monsters" not in starts:
                starts["monsters"] = off

    return starts


def walk_chunks(payload: bytes, start: int, end: int) -> list[dict]:
    """Walk chunks from start (inclusive) until end (exclusive) or until a
    terminator / sentinel is hit or we run out of bytes.
    Returns list of {offset, tag, size, preview}.
    Does not interpret tag semantics.
    """
    out: list[dict] = []
    off = start
    while off + 8 <= end:
        tag, size = struct.unpack_from("<II", payload, off)
        if tag == CHR_SENTINEL:
            out.append({
                "offset":  off,
                "tag":     tag,
                "tag_hex": f"0x{tag:08X}",
                "name":    "@CHR_SENTINEL",
                "size":    size,
                "preview": "",
                "is_sentinel": True,
            })
            return out
        if tag == TAG_TERMINATOR:
            out.append({
                "offset":  off,
                "tag":     tag,
                "tag_hex": f"0x{tag:08X}",
                "name":    TAG_NAMES.get(tag, "?"),
                "size":    size,
                "preview": "",
                "is_terminator": True,
            })
            return out
        if tag > 12 or off + 8 + size > end:
            # Bad chunk — stop with an error marker.
            out.append({
                "offset":  off,
                "tag":     tag,
                "tag_hex": f"0x{tag:08X}",
                "name":    "BAD",
                "size":    size,
                "preview": payload[off:off + 16].hex(),
                "error":   "tag>12 or chunk overruns buffer",
            })
            return out

        preview_bytes = payload[off + 8 : off + 8 + min(16, size)]
        ascii_preview = "".join(
            chr(b) if 0x20 <= b < 0x7F else "." for b in preview_bytes
        )
        out.append({
            "offset":  off,
            "tag":     tag,
            "tag_hex": f"0x{tag:08X}",
            "name":    TAG_NAMES.get(tag, f"tag_{tag}"),
            "size":    size,
            "preview_hex":    preview_bytes.hex(),
            "preview_ascii":  ascii_preview,
        })
        off += 8 + size
    return out


def find_chunk_stream_start(data: bytes) -> int:
    """Probe the small header and return the offset at which stream A starts.

    The DAT loader computes the stream-A start as:
        pvVar3 + *(u32*)(pvVar3 + 4) + 8
    i.e. the u32 at file offset 4 plus 8 is the byte count of a pre-chunk
    header block. Default to that layout; fall back to probing if invalid.
    """
    if len(data) >= 8:
        hdr_len = struct.unpack_from("<I", data, 4)[0]
        candidate = hdr_len + 8
        if 0 < candidate < len(data):
            probe = walk_chunks(
                data, candidate, min(len(data), candidate + 8192)
            )
            if probe and any(ch.get("is_sentinel") for ch in probe[:64]):
                return candidate
    # Fallback probe
    best = (0, -1)
    for c in (0, 4, 8, 12, 16, 20, 24, 32, 0x14):
        chunks = walk_chunks(data, c, min(len(data), c + 8192))
        score = sum(1 for ch in chunks if "error" not in ch and ch["tag"] <= 12)
        if score > best[1]:
            best = (c, score)
    return best[0]


def walk_inner_chr(data: bytes, chr_chunk_offset: int) -> list[dict]:
    """Walk the chunks nested *inside* a @CHR container.

    From the loader: puVar5 = @CHR + local_c8[2], where local_c8[2] is
    the third u32 of the @CHR chunk. @CHR is at offset C:
        C+0: tag (@CHR)
        C+4: outer size
        C+8: inner header begins; u32 at C+8 is usually 0x30, meaning
             inner chunks start at C+0x30.
    Then the same tag/size/data format resumes until a NULL handler.
    """
    header_skip = struct.unpack_from("<I", data, chr_chunk_offset + 8)[0]
    inner_start = chr_chunk_offset + header_skip
    outer_size  = struct.unpack_from("<I", data, chr_chunk_offset + 4)[0]
    inner_end   = min(len(data), chr_chunk_offset + 8 + outer_size)
    return walk_chunks(data, inner_start, inner_end)


def classify_region(chunks: list[dict], region_off: int) -> dict | None:
    """Return the chunk whose data range covers region_off, if any."""
    for ch in chunks:
        if "error" in ch or ch.get("is_sentinel") or ch.get("is_terminator"):
            continue
        data_start = ch["offset"] + 8
        data_end   = data_start + ch["size"]
        if data_start <= region_off < data_end:
            return ch
    return None


def main() -> None:
    dat_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DAT
    if not dat_path.exists():
        raise SystemExit(f"DAT not found: {dat_path}")
    data = dat_path.read_bytes()
    print(f"DAT: {dat_path}  ({len(data):,} bytes)")

    start = find_chunk_stream_start(data)
    print(f"chunk stream probe -> start offset 0x{start:X}")

    # Walk stream A
    stream_a = walk_chunks(data, start, len(data))
    print(f"stream A: {len(stream_a)} records")

    # If last record is @CHR, descend INTO it (it is a container, not a
    # plain separator). Inner chunks follow the same tag/size format,
    # skipping a 0x30-byte metadata header.
    stream_b: list[dict] = []
    chr_off = None
    if stream_a and stream_a[-1].get("is_sentinel"):
        chr_off = stream_a[-1]["offset"]
        stream_b = walk_inner_chr(data, chr_off)
        print(f"stream B (inside @CHR @ 0x{chr_off:X}, outer size=0x{stream_a[-1]['size']:X}): "
              f"{len(stream_b)} records")

    # Tag frequency summary
    from collections import Counter
    def tag_hist(chunks):
        c = Counter()
        for ch in chunks:
            if "error" in ch or ch.get("is_sentinel"):
                continue
            c[ch["tag"]] += 1
        return c

    hist_a = tag_hist(stream_a)
    hist_b = tag_hist(stream_b)
    print("\nTag frequencies:")
    for t in sorted(set(hist_a) | set(hist_b)):
        print(f"  tag {t:2d} ({TAG_NAMES.get(t,'?'):22s})  "
              f"A={hist_a.get(t,0):4d}  B={hist_b.get(t,0):4d}")

    # Cross-reference against memory maps
    tools_dir = Path(__file__).resolve().parent
    regions = try_load_region_starts(tools_dir)
    print(f"\nKnown region start offsets: {len(regions)}")
    region_map: dict = {}
    for name, off in regions.items():
        hit_a = classify_region(stream_a, off)
        hit_b = classify_region(stream_b, off)
        hit = hit_a or hit_b
        which = "A" if hit_a else ("B" if hit_b else "-")
        if hit:
            print(f"  {name:35s}  off=0x{off:X}  in stream {which}  "
                  f"tag={hit['tag']} ({hit['name']})  "
                  f"chunk@0x{hit['offset']:X} size={hit['size']}")
            region_map[name] = {
                "region_offset": off,
                "stream":        which,
                "tag":           hit["tag"],
                "tag_name":      hit["name"],
                "chunk_offset":  hit["offset"],
                "chunk_size":    hit["size"],
            }
        else:
            print(f"  {name:35s}  off=0x{off:X}  NO CHUNK COVERS THIS")
            region_map[name] = {"region_offset": off, "stream": "-"}

    out_file = tools_dir / "dat_chunk_map.json"
    out_file.write_text(json.dumps(
        {
            "dat_path":      str(dat_path),
            "dat_size":      len(data),
            "stream_start":  start,
            "stream_a":      stream_a,
            "stream_b":      stream_b,
            "tag_freq_a":    dict(hist_a),
            "tag_freq_b":    dict(hist_b),
            "regions":       region_map,
        },
        indent=2,
    ))
    print(f"\n[OK] wrote {out_file}")


if __name__ == "__main__":
    main()
