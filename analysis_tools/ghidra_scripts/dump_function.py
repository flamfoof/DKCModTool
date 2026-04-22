"""Decompile the function containing a given virtual address and write
its C pseudocode to ghidra_test/output/.

Usage:
    python dump_function.py 0x1402a2240
    python dump_function.py 1402a2240
"""
from __future__ import annotations

import sys

from _ghidra_session import open_dkk, OUTPUT_DIR


def parse_hex(s: str) -> int:
    s = s.strip()
    if s.lower().startswith("0x"):
        s = s[2:]
    return int(s, 16)


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python dump_function.py <hex-address>")
        sys.exit(1)
    target = parse_hex(sys.argv[1])

    with open_dkk() as api:
        from ghidra.app.decompiler import DecompInterface
        from ghidra.util.task import ConsoleTaskMonitor

        prog = api.getCurrentProgram()
        # pass hex string so toAddr(String) is chosen, not toAddr(int)/32-bit
        addr = api.toAddr(f"0x{target:X}")
        fn = api.getFunctionContaining(addr) or api.getFunctionAt(addr)
        if fn is None:
            print(f"ERROR: no function at 0x{target:X}")
            sys.exit(1)

        print(f"Decompiling {fn.getName()} @ {fn.getEntryPoint()}...")

        decomp = DecompInterface()
        decomp.openProgram(prog)
        try:
            result = decomp.decompileFunction(fn, 60, ConsoleTaskMonitor())
        finally:
            decomp.dispose()

        if not result.decompileCompleted():
            print(f"ERROR: decompile failed: {result.getErrorMessage()}")
            sys.exit(1)

        c_src = result.getDecompiledFunction().getC()

        print("-" * 70)
        print(c_src)
        print("-" * 70)

        safe = fn.getName().replace("/", "_").replace("\\", "_")
        out_file = OUTPUT_DIR / (
            f"func_{safe}_{fn.getEntryPoint().getOffset():X}.c"
        )
        out_file.write_text(
            f"// Function: {fn.getName()}\n"
            f"// Entry:    {fn.getEntryPoint()}\n"
            f"// Size:     {fn.getBody().getNumAddresses()} bytes\n\n"
            + c_src
        )
        print(f"\n[OK] wrote {out_file}")


if __name__ == "__main__":
    main()
