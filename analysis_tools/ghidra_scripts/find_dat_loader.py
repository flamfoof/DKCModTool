"""Locate DAT-related filename strings in DkkStm.exe and list the
functions that reference them. The function with the fewest / most
specific xrefs to `STAGEBASE_EN.DAT` is the DAT loader."""
from __future__ import annotations

import json
from pathlib import Path

from _ghidra_session import open_dkk, OUTPUT_DIR

TARGETS = [
    "STAGEBASE_EN.DAT",   # observed casing in the binary
    "stageBase_EN.DAT",
    "STAGEBASE_JP.DAT",
    "Data_eng.cpk",
    "CommonData.cpk",
    "Data.cpk",
]


def find_defined_string_hits(listing, needle: str) -> list[tuple]:
    """Return (address, value) for every defined Data item whose value contains needle."""
    needle_lower = needle.lower()
    out = []
    for data in listing.getDefinedData(True):
        try:
            v = data.getValue()
            if v is None:
                continue
            s = str(v)
            if needle_lower in s.lower():
                out.append((data.getAddress(), s))
        except Exception:
            pass
    return out


def main() -> None:
    with open_dkk() as api:
        prog    = api.getCurrentProgram()
        listing = prog.getListing()
        fm      = prog.getFunctionManager()
        refs    = prog.getReferenceManager()

        print("=" * 70)
        print("DAT loader search")
        print("=" * 70)

        summary: dict[str, dict] = {}
        for needle in TARGETS:
            hits = find_defined_string_hits(listing, needle)
            fn_set = set()
            for addr, _ in hits:
                for xref in refs.getReferencesTo(addr):
                    fn = fm.getFunctionContaining(xref.getFromAddress())
                    if fn:
                        fn_set.add(fn)

            print(f"\n{needle!r}  ({len(hits)} string match(es))")
            for addr, val in hits[:3]:
                print(f"    string at {addr}  {val!r}")
            if fn_set:
                for fn in sorted(fn_set, key=lambda f: f.getEntryPoint().getOffset()):
                    print(
                        f"    -> {fn.getName():<25s}  "
                        f"entry={fn.getEntryPoint()}  "
                        f"size={fn.getBody().getNumAddresses()}"
                    )
            else:
                print("    (no function xrefs)")

            summary[needle] = {
                "string_hits": [
                    {"addr": str(a), "value": v} for a, v in hits
                ],
                "referencing_functions": [
                    {
                        "name": fn.getName(),
                        "entry": f"0x{fn.getEntryPoint().getOffset():X}",
                        "size":  fn.getBody().getNumAddresses(),
                    }
                    for fn in sorted(
                        fn_set, key=lambda f: f.getEntryPoint().getOffset()
                    )
                ],
            }

        out_file = OUTPUT_DIR / "dat_loader_candidates.json"
        out_file.write_text(json.dumps(
            {
                "program":    prog.getName(),
                "image_base": f"0x{prog.getImageBase().getOffset():X}",
                "searches":   summary,
            },
            indent=2,
        ))
        print(f"\n[OK] wrote {out_file}")


if __name__ == "__main__":
    main()
