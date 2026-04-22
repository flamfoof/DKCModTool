"""Shared helper: open the existing `dokapon` Ghidra project
read-only via pyghidra, yielding a FlatProgramAPI for DkkStm.exe.

Uses `DefaultProjectData` directly instead of `pyghidra.open_project`
because the latter always acquires an exclusive lock and will fail
when the Ghidra GUI has the project open. `DefaultProjectData` in
read-only mode (forUpdate=False) coexists peacefully with the GUI.

Usage:
    from _ghidra_session import open_dkk

    with open_dkk() as api:
        prog = api.getCurrentProgram()
        print(prog.getFunctionCount())
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pyghidra

# Project-specific constants; adjust if the project moves.
PROJECT_DIR  = Path(r"G:\Decompiling\Dokapon")
PROJECT_NAME = "dokapon"
PROGRAM_NAME = "DkkStm.exe"

# Output dir sits beside this script: analysis_tools/ghidra_scripts/output/
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


@contextmanager
def open_dkk():
    """Yield a FlatProgramAPI bound to DkkStm.exe, read-only.

    Safe to run while the Ghidra GUI has the same project open.
    """
    pyghidra.start()

    # Late imports so pyghidra.start() can initialize the JVM first.
    from ghidra.framework.model import ProjectLocator
    from ghidra.framework.data import DefaultProjectData
    from ghidra.program.flatapi import FlatProgramAPI
    from ghidra.util.task import ConsoleTaskMonitor
    from java.lang import Object as JavaObject  # type: ignore

    locator = ProjectLocator(str(PROJECT_DIR), PROJECT_NAME)
    # DefaultProjectData(locator, forUpdate=False, resetOwner=False)
    # forUpdate=False opens without write-locking the project.
    project_data = DefaultProjectData(locator, False, False)
    try:
        df = None
        for f in project_data.getRootFolder().getFiles():
            if f.getName() == PROGRAM_NAME:
                df = f
                break
        if df is None:
            raise RuntimeError(
                f"{PROGRAM_NAME!r} not found in project "
                f"{PROJECT_DIR}/{PROJECT_NAME}"
            )

        consumer = JavaObject()
        monitor = ConsoleTaskMonitor()
        program = df.getReadOnlyDomainObject(consumer, -1, monitor)
        try:
            api = FlatProgramAPI(program)
            yield api
        finally:
            program.release(consumer)
    finally:
        project_data.close()
