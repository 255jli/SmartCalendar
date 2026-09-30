#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for Smart Calendar.
Same behavior on Windows, Linux, and macOS.

IMPORTANT: PyInstaller does NOT support cross-compilation.
An executable can only be built for the OS on which this script runs.
We cannot produce a Windows .exe on Linux, or a macOS .app on Windows,
without a matching host system. So the build always targets the
current OS.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from _common import ROOT, ensure_venv, install_missing, ask_extras


APP_NAME = "SmartCalendar"
BUILD_REQUIRED = ["PyInstaller"]  # Removed apscheduler and plyer dependencies
OPTIONAL_VISUAL = ["ttkbootstrap"]


def build_command(python: Path, extras: bool) -> list:
    """Формирует команду PyInstaller с учётом ОС.

    Иконка приложения:
    - Windows: .ico (качество зависит от количества размеров внутри файла);
    - macOS:   .icns (обязательно для иконки в Dock);
    - Linux:   --icon не влияет на бинарник, но --add-data нужен
               для иконки внутри окна через iconphoto.
    """
    sep = os.pathsep
    system = platform.system().lower()

    cmd = [
        str(python), "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        "--hidden-import=tkinter",
    ]

    if extras:
        cmd += [
            "--hidden-import=ttkbootstrap",
            "--collect-all=ttkbootstrap",
        ]

    # Иконка уровня приложения (exe / .app / .app bundle).
    ico = ROOT / "calendar.ico"
    icns = ROOT / "calendar.icns"
    if system == "windows" and ico.exists():
        cmd.append(f"--icon={ico}")
    elif system == "darwin" and icns.exists():
        cmd.append(f"--icon={icns}")

    # Ресурсы, кладём в бандл рядом с main.py.
    for res in ("calendar.ico", "calendar.png", "calendar_512.png"):
        p = ROOT / res
        if p.exists():
            cmd.append(f"--add-data={p}{sep}.")

    import_dir = ROOT / "import"
    if import_dir.is_dir():
        cmd.append(f"--add-data={import_dir}{sep}.")

    cmd.append("main.py")
    return cmd


def cleanup() -> None:
    for name in ("build", "__pycache__"):
        p = ROOT / name
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    spec = ROOT / f"{APP_NAME}.spec"
    if spec.exists():
        spec.unlink()


def main() -> int:
    system = platform.system()

    print("=== Smart Calendar Build Script ===")
    print(f"Host OS: {system}")
    print()
    print("Note: PyInstaller cannot cross-compile.")
    print(f"      The executable will be built for {system} only.")
    print()

    if not (ROOT / "main.py").exists():
        print(f"main.py not found in {ROOT}")
        input("Press Enter to exit...")
        return 1

    python = ensure_venv()
    extras = ask_extras()

    packages = list(BUILD_REQUIRED)
    if extras:
        packages += OPTIONAL_VISUAL

    if not install_missing(python, packages):
        input("Press Enter to exit...")
        return 1

    print("\n=== Running PyInstaller ===\n")
    try:
        subprocess.run(build_command(python, extras), cwd=str(ROOT), check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        return 1

    cleanup()

    sysname = system.lower()
    if sysname == "windows":
        out = f"{APP_NAME}.exe"
    elif sysname == "darwin":
        out = f"{APP_NAME}.app"
    else:
        out = APP_NAME
    print(f"\nBuild complete: dist/{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())