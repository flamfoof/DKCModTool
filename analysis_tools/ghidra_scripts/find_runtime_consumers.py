"""Find runtime consumers of the stageBase_EN.DAT loader results.

The DAT loader at FUN_1402A2240 populates an in-memory context struct
owned by its caller. That caller stashes pointers from the context into
global pointer slots (in `.data` / `.bss`). Every later function that
reads those globals is a *consumer* of the loaded tables.

Strategy:
  1. Enumerate callers of the DAT loader.
  2. Within each caller, collect every instruction that WRITES to a
     global address in `.data` or `.bss` (i.e. `mov [rip+disp], reg` /
     `mov [abs64], reg`). These are the candidate table-base pointer
     slots.
  3. For each slot, count READ xrefs from code elsewhere in the EXE.
     High-count slots are the table pointers; low-count ones are
     housekeeping flags.
  4. For each high-count slot, emit the top N consumer functions with
     their entry addresses. Those are the runtime iterators / lookup
     functions you want to reverse next.

Output: ghidra_scripts/output/runtime_consumers.json
"""
from __future__ import annotations

import json
from collections import defaultdict

from _ghidra_session import open_dkk, OUTPUT_DIR

DAT_LOADER_EA = 0x1402A2240


def hexu(v: int) -> str:
    return f"0x{v & 0xFFFFFFFFFFFFFFFF:X}"


def is_in_block(prog, ea_int: int, names: tuple[str, ...]) -> bool:
    try:
        addr = prog.getAddressFactory().getDefaultAddressSpace().getAddress(ea_int)
    except Exception:
        return False
    block = prog.getMemory().getBlock(addr)
    return block is not None and block.getName() in names


def main() -> None:
    with open_dkk() as api:
        prog    = api.getCurrentProgram()
        fm      = prog.getFunctionManager()
        ref_mgr = prog.getReferenceManager()
        listing = prog.getListing()

        loader = fm.getFunctionContaining(api.toAddr(f"0x{DAT_LOADER_EA:X}"))
        if loader is None:
            raise SystemExit(f"DAT loader not found at {DAT_LOADER_EA:X}")

        # --- Step 1: callers of the DAT loader -----------------------------
        loader_entry = loader.getEntryPoint()
        caller_refs = ref_mgr.getReferencesTo(loader_entry)
        callers: list = []
        for ref in caller_refs:
            if "CALL" not in str(ref.getReferenceType()):
                continue
            caller_fn = fm.getFunctionContaining(ref.getFromAddress())
            if caller_fn is not None and caller_fn not in callers:
                callers.append(caller_fn)

        print(f"DAT loader FUN_{DAT_LOADER_EA:X} has {len(callers)} "
              f"unique caller function(s)")
        for cfn in callers:
            print(f"  caller: {cfn.getName()} @ {cfn.getEntryPoint()}")

        if not callers:
            raise SystemExit("No callers found; cannot locate table globals.")

        # --- Step 2: global writes in each caller --------------------------
        # A global-pointer write shows as an instruction with a DATA write
        # reference to an address in .data or .bss.
        slots: "dict[int, dict]" = {}
        for cfn in callers:
            body = cfn.getBody()
            it = body.getAddresses(True)
            while it.hasNext():
                ea = it.next()
                instr = listing.getInstructionAt(ea)
                if instr is None:
                    continue
                for ref in instr.getReferencesFrom():
                    rtype = str(ref.getReferenceType())
                    if "WRITE" not in rtype and "DATA" not in rtype:
                        continue
                    to_int = int(ref.getToAddress().getOffset()) & 0xFFFFFFFFFFFFFFFF
                    if not is_in_block(prog, to_int, (".data", ".bss", ".rdata")):
                        continue
                    # Only care about writes (RW-capable blocks); skip
                    # references that are merely READs.
                    if "WRITE" not in rtype:
                        continue
                    rec = slots.setdefault(to_int, {
                        "slot_ea":       hexu(to_int),
                        "written_by":    [],
                        "instr_sample":  str(instr),
                        "block":         prog.getMemory().getBlock(
                            prog.getAddressFactory()
                                .getDefaultAddressSpace()
                                .getAddress(to_int)
                        ).getName(),
                    })
                    rec["written_by"].append({
                        "caller":   cfn.getName(),
                        "instr_ea": str(ea),
                    })

        print(f"\nCandidate table-base slots written near DAT loader calls: "
              f"{len(slots)}")

        # --- Step 3: count READ xrefs to each slot from code ---------------
        for slot_ea_int, rec in slots.items():
            addr = prog.getAddressFactory().getDefaultAddressSpace().getAddress(slot_ea_int)
            read_callers: "dict[str, int]" = defaultdict(int)
            read_callers_ea: "dict[str, str]" = {}
            total_reads = 0
            for xref in ref_mgr.getReferencesTo(addr):
                rtype = str(xref.getReferenceType())
                if "WRITE" in rtype:
                    continue
                from_addr = xref.getFromAddress()
                cfn = fm.getFunctionContaining(from_addr)
                if cfn is None:
                    continue
                name = cfn.getName()
                read_callers[name] += 1
                read_callers_ea.setdefault(name, str(cfn.getEntryPoint()))
                total_reads += 1
            rec["read_xref_count"] = total_reads
            rec["read_fn_count"]   = len(read_callers)
            rec["top_readers"] = sorted(
                [{"fn": n, "entry": read_callers_ea[n], "reads": c}
                 for n, c in read_callers.items()],
                key=lambda d: -d["reads"],
            )[:15]

        # --- Step 4: report + write JSON -----------------------------------
        ranked = sorted(slots.values(), key=lambda r: -r["read_xref_count"])
        print()
        print(f"{'slot':>14s}  block  #readers  #reads  top callers")
        print("-" * 78)
        for rec in ranked[:40]:
            top = ", ".join(f"{t['fn']}({t['reads']})" for t in rec["top_readers"][:4])
            print(f"{rec['slot_ea']:>14s}  {rec['block']:6s}  "
                  f"{rec['read_fn_count']:>8d}  "
                  f"{rec['read_xref_count']:>6d}  {top}")

        out_file = OUTPUT_DIR / "runtime_consumers.json"
        out_file.write_text(json.dumps(
            {
                "dat_loader_ea": hexu(DAT_LOADER_EA),
                "callers":       [
                    {"name": c.getName(), "entry": str(c.getEntryPoint())}
                    for c in callers
                ],
                "slots_ranked":  ranked,
            },
            indent=2,
        ))
        print(f"\n[OK] wrote {out_file}")


if __name__ == "__main__":
    main()
