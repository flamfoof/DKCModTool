"""Walk the DAT chunk-handler dispatch table at PTR_FUN_1404A5F58.

Derived from the decompilation of FUN_1402A2240 (the DAT loader):

    (code *)(&PTR_FUN_1404a5f58)[(ulonglong)*puVar4 * 3]

So the table is an array of 24-byte entries (three qwords each) indexed by
the chunk tag (first u32 of each chunk). Only slot 0 is the handler pointer;
slots 1 and 2 carry auxiliary data (probably tag-name string + flags/size,
or vtable-ish metadata). We walk forward until we hit an entry whose slot-0
pointer is zero or doesn't land inside `.text`.

For every valid entry we record:
    index, entry_addr, handler_ea, handler_name, handler_size,
    slot1_hex, slot2_hex, slot1_deref (if it looks like a string),
    slot1_target_symbol (if slot1 is a code/data pointer)

Output: ghidra_scripts/output/dispatch_table.json
Also prints a compact summary to stdout.
"""
from __future__ import annotations

import json

from _ghidra_session import open_dkk, OUTPUT_DIR

TABLE_BASE = 0x1404A5F58
STRIDE     = 24          # 3 qwords per entry
MAX_ENTRIES = 256        # hard cap; real table is tiny (tag is a u32 index)


def qword(api, ea_int: int) -> int:
    """Read little-endian qword at a virtual address, as signed-safe uint64."""
    addr = api.toAddr(f"0x{ea_int:X}")
    # getLong returns a signed Java long; mask back to uint64.
    return int(api.getLong(addr)) & 0xFFFFFFFFFFFFFFFF


def dword(api, ea_int: int) -> int:
    addr = api.toAddr(f"0x{ea_int:X}")
    return int(api.getInt(addr)) & 0xFFFFFFFF


def try_read_cstring(api, ea_int: int, max_len: int = 64) -> str | None:
    """Return an ASCII C-string at ea_int if all bytes are printable, else None."""
    try:
        out = []
        for i in range(max_len):
            addr = api.toAddr(f"0x{ea_int + i:X}")
            b = int(api.getByte(addr)) & 0xFF
            if b == 0:
                break
            if b < 0x20 or b > 0x7E:
                return None
            out.append(chr(b))
        else:
            return None  # no terminator within max_len
        if len(out) < 2:
            return None
        return "".join(out)
    except Exception:
        return None


def addr_in_text(prog, ea_int: int) -> bool:
    block = prog.getMemory().getBlock(prog.getAddressFactory().getDefaultAddressSpace().getAddress(ea_int))
    return block is not None and block.getName() == ".text"


def main() -> None:
    with open_dkk() as api:
        prog = api.getCurrentProgram()
        fm   = prog.getFunctionManager()
        st   = prog.getSymbolTable()

        print(f"Walking dispatch table at 0x{TABLE_BASE:X} "
              f"(stride={STRIDE} bytes, max={MAX_ENTRIES})")
        print("-" * 72)

        entries: list[dict] = []
        stop_reason = "max entries reached"

        for i in range(MAX_ENTRIES):
            entry_ea = TABLE_BASE + i * STRIDE

            slot0 = qword(api, entry_ea + 0)   # handler
            slot1 = qword(api, entry_ea + 8)
            slot2 = qword(api, entry_ea + 16)

            if slot0 == 0:
                stop_reason = f"slot0 is NULL at entry {i}"
                break
            if not addr_in_text(prog, slot0):
                stop_reason = (
                    f"slot0 0x{slot0:X} outside .text at entry {i}"
                )
                break

            handler_addr = api.toAddr(f"0x{slot0:X}")
            fn = fm.getFunctionContaining(handler_addr) \
                 or fm.getFunctionAt(handler_addr)

            record = {
                "index":         i,
                "entry_ea":      f"0x{entry_ea:X}",
                "handler_ea":    f"0x{slot0:X}",
                "handler_name":  fn.getName() if fn else None,
                "handler_size":  int(fn.getBody().getNumAddresses()) if fn else None,
                "slot1_hex":     f"0x{slot1:X}",
                "slot2_hex":     f"0x{slot2:X}",
            }

            # Try to interpret slot1 as a data pointer -> string or symbol.
            if slot1 != 0:
                s = try_read_cstring(api, slot1)
                if s:
                    record["slot1_string"] = s
                sym = st.getPrimarySymbol(api.toAddr(f"0x{slot1:X}"))
                if sym is not None:
                    record["slot1_symbol"] = str(sym.getName())

            entries.append(record)

            print(
                f"  [{i:3d}] entry=0x{entry_ea:X}  "
                f"handler=0x{slot0:012X} "
                f"{(fn.getName() if fn else '<no fn>'):28s}"
                f"  s1={slot1:>18X}  s2={slot2:>10X}"
                f"{'  ' + record['slot1_string'] if 'slot1_string' in record else ''}"
            )

        print("-" * 72)
        print(f"stopped: {stop_reason}")
        print(f"valid entries: {len(entries)}")

        out_file = OUTPUT_DIR / "dispatch_table.json"
        out_file.write_text(json.dumps(
            {
                "table_base":     f"0x{TABLE_BASE:X}",
                "stride_bytes":   STRIDE,
                "entry_count":    len(entries),
                "stop_reason":    stop_reason,
                "entries":        entries,
            },
            indent=2,
        ))
        print(f"\n[OK] wrote {out_file}")


if __name__ == "__main__":
    main()
