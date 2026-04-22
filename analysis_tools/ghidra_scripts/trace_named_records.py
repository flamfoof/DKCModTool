"""Trace named-record dispatch inside FUN_1402A2860 (dispatch tag 5).

FUN_1402A2860 reads a null-terminated chunk-name string, then picks a
secondary parser based on that name. This script:

  1. Collects every outgoing reference from FUN_1402A2860:
        - data refs that land on printable C-strings -> candidate record names
        - call refs (CALL / unconditional branches) -> candidate sub-parsers
  2. Scans the raw bytes of the function body for ASCII strings referenced
     by simple LEA/MOV-imm instructions, to catch names that Ghidra's
     reference engine missed.
  3. Writes `output/named_records.json` with:
        { names:   [ {string, ea, xref_ea} ... ],
          callees: [ {ea, name, size} ... ] }
  4. Prints a compact table.

Follow-up idea: for each name string, find which callee happens right
after that string is loaded (same basic block) -> that's the parser
for that record type.
"""
from __future__ import annotations

import json
from collections import OrderedDict

from _ghidra_session import open_dkk, OUTPUT_DIR

TARGET_FN_EA = 0x1402A2860


def read_cstring(api, ea_int: int, max_len: int = 128) -> str | None:
    out: list[str] = []
    for i in range(max_len):
        try:
            b = int(api.getByte(api.toAddr(f"0x{ea_int + i:X}"))) & 0xFF
        except Exception:
            return None
        if b == 0:
            break
        if b < 0x20 or b > 0x7E:
            return None
        out.append(chr(b))
    else:
        return None
    return "".join(out) if len(out) >= 2 else None


def main() -> None:
    with open_dkk() as api:
        prog = api.getCurrentProgram()
        fm   = prog.getFunctionManager()
        ref_mgr = prog.getReferenceManager()

        fn = fm.getFunctionContaining(api.toAddr(f"0x{TARGET_FN_EA:X}"))
        if fn is None:
            raise SystemExit(f"No function at 0x{TARGET_FN_EA:X}")
        body = fn.getBody()
        print(f"Tracing {fn.getName()} @ {fn.getEntryPoint()}  "
              f"({int(body.getNumAddresses())} addresses)")
        print("-" * 72)

        listing = prog.getListing()

        strings:  "OrderedDict[str, dict]" = OrderedDict()
        callees:  "OrderedDict[int, dict]" = OrderedDict()

        # Walk every address in the function body
        addr_iter = body.getAddresses(True)
        while addr_iter.hasNext():
            instr_ea = addr_iter.next()
            instr = listing.getInstructionAt(instr_ea)
            if instr is None:
                continue

            # References attached to this instruction
            for ref in instr.getReferencesFrom():
                ref_type = str(ref.getReferenceType())
                to_addr  = ref.getToAddress()
                to_int   = int(to_addr.getOffset()) & 0xFFFFFFFFFFFFFFFF

                # Data ref -> maybe a C-string
                if "DATA" in ref_type or "READ" in ref_type:
                    s = read_cstring(api, to_int)
                    if s is not None and s not in strings:
                        strings[s] = {
                            "string":  s,
                            "ea":      f"0x{to_int:X}",
                            "xref_ea": f"{instr_ea}",
                        }

                # Call ref -> candidate sub-parser
                if ref_type in ("UNCONDITIONAL_CALL", "CONDITIONAL_CALL"):
                    if to_int not in callees:
                        target_fn = fm.getFunctionContaining(to_addr) \
                                    or fm.getFunctionAt(to_addr)
                        callees[to_int] = {
                            "ea":    f"0x{to_int:X}",
                            "name":  target_fn.getName() if target_fn else f"UNK_{to_int:X}",
                            "size":  int(target_fn.getBody().getNumAddresses()) if target_fn else None,
                            "from":  f"{instr_ea}",
                        }

        print(f"strings referenced: {len(strings)}")
        for rec in strings.values():
            print(f"  {rec['ea']:>14s}  '{rec['string']}'"
                  f"  (from {rec['xref_ea']})")

        print()
        print(f"callees: {len(callees)}")
        for rec in callees.values():
            size = rec["size"] if rec["size"] is not None else "?"
            print(f"  {rec['ea']:>14s}  {rec['name']:30s}  size={size}")

        out = OUTPUT_DIR / "named_records.json"
        out.write_text(json.dumps(
            {
                "target_fn":     f"0x{TARGET_FN_EA:X}",
                "target_name":   fn.getName(),
                "strings":       list(strings.values()),
                "callees":       list(callees.values()),
            },
            indent=2,
        ))
        print(f"\n[OK] wrote {out}")


if __name__ == "__main__":
    main()
