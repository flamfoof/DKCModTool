"""Decompile every handler in the DAT dispatch table.

Reads `output/dispatch_table.json` (produced by walk_dispatch_table.py),
and for each of the 13 handlers:
  1. Force-disassembles the entry point if Ghidra hasn't (read-only-safe:
     we just ask the Listing for instructions; Ghidra will disassemble
     on demand without persisting).
  2. Attempts to decompile via DecompInterface. If there is no Function
     record (Ghidra auto-analysis missed it), we instead dump raw
     disassembly starting at the entry point until we hit a RET that is
     not in the middle of a branch path.
  3. Writes `output/handlers/handler_<idx>_<tag>_<name>.c` (or `.asm` for
     disasm fallback).
  4. Emits `output/dispatch_handlers_summary.json` with one record per
     tag: size, classification heuristic, first-mem-write offset, etc.

Classification heuristic (rough): scan the body for writes of the form
`mov [rcx+disp], ...` where RCX is the context pointer (first arg). The
set of `disp` values per handler tells us which fields of the context
struct each tag populates. The equipment handler is the one that writes
a large count/pointer pair into the field corresponding to the equipment
region.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from _ghidra_session import open_dkk, OUTPUT_DIR

TABLE_JSON = OUTPUT_DIR / "dispatch_table.json"
HANDLER_DIR = OUTPUT_DIR / "handlers"
HANDLER_DIR.mkdir(exist_ok=True)

MAX_DISASM_INSTRS = 256  # fallback limit when no Function record


def decompile(api, fn, timeout_s: int = 30) -> str:
    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor

    prog = api.getCurrentProgram()
    decomp = DecompInterface()
    decomp.openProgram(prog)
    try:
        res = decomp.decompileFunction(fn, timeout_s, ConsoleTaskMonitor())
        if res is None or not res.decompileCompleted():
            return "// decompile failed\n"
        return str(res.getDecompiledFunction().getC())
    finally:
        decomp.dispose()


def linear_disasm(api, entry_ea: int, max_instrs: int = MAX_DISASM_INSTRS) -> str:
    """Walk instructions from entry until RET, following fall-through only.

    Ghidra's Listing will disassemble on demand if bytes are code but no
    instruction exists yet. We do NOT commit this; it is transient.
    """
    prog = api.getCurrentProgram()
    listing = prog.getListing()
    lines: list[str] = []

    cur = api.toAddr(f"0x{entry_ea:X}")
    for _ in range(max_instrs):
        instr = listing.getInstructionAt(cur)
        if instr is None:
            # ask Ghidra to disassemble this one address (read-only-safe
            # in the sense that DefaultProjectData was opened forUpdate=False;
            # Ghidra will still produce an in-memory Instruction but cannot
            # save it back to the project).
            try:
                api.disassemble(cur)
                instr = listing.getInstructionAt(cur)
            except Exception:
                pass
        if instr is None:
            lines.append(f"{cur}:  (no disasm)")
            break
        lines.append(f"{cur}:  {instr}")
        mnemonic = str(instr.getMnemonicString()).upper()
        if mnemonic in ("RET", "RETF", "JMP"):
            # stop at unconditional flow break
            break
        cur = cur.add(instr.getLength())

    return "\n".join(lines) + "\n"


_CTX_WRITE_RE = re.compile(
    r"""\*  \s* \(  [^)]*?  \*  [^)]*?  \)  \s*
        \(\s*  param_1 | pcVar\d+ | local_\w+ \s*\)   # best-effort
    """,
    re.VERBOSE,
)


def classify(decomp_text: str) -> dict:
    """Rough heuristics: count mem-writes, detect loop, note param[0].

    Not strict analysis — the goal is just a hint to help eyeballing.
    """
    info: dict = {}
    text = decomp_text
    info["has_loop"]   = bool(re.search(r"\b(for|while|do)\b", text))
    info["has_malloc"] = "malloc" in text.lower()
    info["call_count"] = len(re.findall(r"\bFUN_[0-9a-f]+\s*\(", text))
    # Look for writes into a field of the first param: *(... *)((longlong)param_1 + 0xNN) = ...
    field_writes = re.findall(
        r"\*\s*\([^)]*\*\s*\)\s*\(\s*\(?\s*(?:longlong|ulonglong|longlong\s*\*)?\s*\)?\s*param_1\s*\+\s*(0x[0-9a-fA-F]+)\s*\)\s*=",
        text,
    )
    info["param1_field_writes"] = sorted(set(field_writes))
    return info


def main() -> None:
    if not TABLE_JSON.exists():
        raise SystemExit(
            f"{TABLE_JSON} not found. Run walk_dispatch_table.py first."
        )
    table = json.loads(TABLE_JSON.read_text())
    entries = table["entries"]
    print(f"Dumping {len(entries)} handlers -> {HANDLER_DIR}")
    print("-" * 72)

    summary: list[dict] = []

    with open_dkk() as api:
        prog = api.getCurrentProgram()
        fm   = prog.getFunctionManager()

        for e in entries:
            tag       = e["index"]
            handler_s = e["handler_ea"]
            handler_i = int(handler_s, 16)
            name_hint = e["handler_name"] or f"UNK_{handler_i:X}"

            addr = api.toAddr(f"0x{handler_i:X}")
            fn = fm.getFunctionContaining(addr) or fm.getFunctionAt(addr)

            rec: dict = {
                "tag":            tag,
                "entry_ea":       e["entry_ea"],
                "handler_ea":     handler_s,
                "handler_name":   name_hint,
                "function_known": fn is not None,
            }

            if fn is not None:
                body = decompile(api, fn)
                out = HANDLER_DIR / f"handler_{tag:02d}_{handler_i:X}_{fn.getName()}.c"
                out.write_text(
                    f"// Tag {tag}  handler @ 0x{handler_i:X}  size={fn.getBody().getNumAddresses()}\n"
                    f"// Entry table slot @ {e['entry_ea']}\n\n{body}"
                )
                rec["output_file"] = out.name
                rec["size_bytes"]  = int(fn.getBody().getNumAddresses())
                rec["heuristics"]  = classify(body)
                status = "DECOMP"
            else:
                asm = linear_disasm(api, handler_i)
                out = HANDLER_DIR / f"handler_{tag:02d}_{handler_i:X}_UNKFN.asm"
                out.write_text(
                    f"; Tag {tag}  handler @ 0x{handler_i:X}  (no Function record)\n"
                    f"; Entry table slot @ {e['entry_ea']}\n\n{asm}"
                )
                rec["output_file"] = out.name
                rec["size_bytes"]  = asm.count("\n")
                rec["heuristics"]  = {"disasm_lines": asm.count("\n")}
                status = "DISASM"

            summary.append(rec)
            fw = rec["heuristics"].get("param1_field_writes", [])
            print(
                f"  [tag {tag:2d}] 0x{handler_i:X}  {status:6s}  "
                f"{rec['size_bytes']:5d}  "
                f"{name_hint:28s}  "
                f"param1 writes: {', '.join(fw) if fw else '-'}"
            )

    summary_file = OUTPUT_DIR / "dispatch_handlers_summary.json"
    summary_file.write_text(json.dumps(
        {"table_base": table["table_base"], "handlers": summary}, indent=2
    ))
    print("-" * 72)
    print(f"[OK] {len(summary)} handlers, summary -> {summary_file}")
    print(f"[OK] per-handler files -> {HANDLER_DIR}")


if __name__ == "__main__":
    main()
