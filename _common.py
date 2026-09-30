#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared helpers for _run.py and _build.py.

This file is NOT an entry point.
Do not run it directly. Use one of:

    python _run.py      # launch the application
    python _build.py    # build an executable for the current OS

Importing this module has no side effects: it only defines functions.
"""

import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def venv_python() -> Path:
    """Path to the Python interpreter inside .venv, per OS."""
    if platform.system().lower() == "windows":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def ask(prompt: str, default_no: bool = True) -> bool:
    """Yes/no prompt. Empty input -> default_no (True = 'no' on Enter)."""
    suffix = " (y/N): " if default_no else " (Y/n): "
    try:
        answer = input(prompt + suffix).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if not answer:
        return not default_no
    return answer in ("y", "yes", "д", "да")


def has_package(python: Path, name: str) -> bool:
    try:
        r = subprocess.run(
            [str(python), "-c", f"import {name}"],
            capture_output=True, text=True, check=False,
        )
        return r.returncode == 0
    except Exception:
        return False


def create_venv() -> bool:
    print("Creating virtual environment in .venv ...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(ROOT / ".venv")],
            check=True,
        )
        print("Virtual environment created.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e}")
        return False


def ensure_venv() -> Path:
    """
    Returns the Python interpreter to use.
    If .venv is missing, offers to create it from the running interpreter.
    """
    py = venv_python()
    if py.exists():
        print(f"Using virtual environment: {py}")
        return py

    print("Virtual environment (.venv) was not found.")
    if ask("Create venv from base Python?", default_no=False):
        if create_venv():
            py = venv_python()
            if py.exists():
                return py
        print("Falling back to base Python interpreter.")
    else:
        print("Using base Python interpreter.")
    return Path(sys.executable)


def install_missing(python: Path, packages) -> bool:
    """Install packages that are not yet importable. Returns True on success."""
    missing = [p for p in packages if not has_package(python, p)]
    if not missing:
        return True

    # Non-fatal: some distros restrict pip self-upgrade.
    subprocess.run(
        [str(python), "-m", "pip", "install", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )

    print("Installing: " + ", ".join(missing))
    try:
        subprocess.run(
            [str(python), "-m", "pip", "install", *missing],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Package installation failed: {e}")
        return False


def ask_extras() -> bool:
    """Single question about the optional visual library."""
    print()
    print("Optional: 'ttkbootstrap' makes the UI look nicer.")
    print("Press Enter to use standard widgets, or 'y' to install the extra library.")
    return ask("Install extra visual library?", default_no=True)

if __name__ == "__main__":
    print("_common.py is an internal helper and is not meant to be run directly.")
    print()
    print("Use one of:")
    print("    python _run.py      # launch the application")
    print("    python _build.py    # build an executable for the current OS")
    sys.exit(1)