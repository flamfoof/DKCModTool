"""Smoke test: print program info via pyghidra (Python 3)."""
from __future__ import annotations

from _ghidra_session import open_dkk, OUTPUT_DIR


def main() -> None:
    with open_dkk() as api:
        prog = api.getCurrentProgram()
        mem  = prog.getMemory()
        fm   = prog.getFunctionManager()

        print("=" * 60)
        print("pyghidra smoke test")
        print("=" * 60)
        print(f"Program name:   {prog.getName()}")
        print(f"Language:       {prog.getLanguage().getLanguageID()}")
        print(f"Image base:     0x{prog.getImageBase().getOffset():X}")
        print(f"Function count: {fm.getFunctionCount():,}")

        print("\nMemory blocks:")
        for block in mem.getBlocks():
            print(
                f"  {block.getName():<12s}  "
                f"start=0x{block.getStart().getOffset():X}  "
                f"size=0x{block.getSize():X}  "
                f"r={block.isRead()} w={block.isWrite()} x={block.isExecute()}"
            )

        marker = OUTPUT_DIR / "hello_ok.txt"
        marker.write_text(
            f"program={prog.getName()}\n"
            f"image_base=0x{prog.getImageBase().getOffset():X}\n"
            f"function_count={fm.getFunctionCount()}\n"
        )
        print(f"\n[OK] wrote {marker}")


if __name__ == "__main__":
    main()
