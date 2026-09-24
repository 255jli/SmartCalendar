#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Script for Smart Calendar Application.
Provides cross-platform compilation capabilities for Windows, Linux, and macOS.
Allows selection of target operating system for project generation.
"""

import os
import shutil
import subprocess
import platform
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
APP_NAME = "SmartCalendar"


def _venv_python() -> Optional[Path]:
    """Determines the Python executable path in the virtual environment based on the operating system."""
    if os.name == 'nt':
        p = ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        p = ROOT / ".venv" / "bin" / "python"
    return p if p.exists() else None


def _ensure_pyinstaller(python: Path) -> bool:
    try:
        r = subprocess.run([str(python), "-c", "import PyInstaller"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return True
    except Exception:
        pass
    print("Installing PyInstaller in virtual environment...")
    try:
        subprocess.run([str(python), "-m", "pip", "install", "pyinstaller"],
                       check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller installation error: {e}")
        return False


def select_target_os():
    """Allows user to select the target operating system for the build."""
    print("Select target operating system for build:")
    print("1. Current OS ({})".format(platform.system()))
    print("2. Windows")
    print("3. Linux") 
    print("4. macOS")
    print("5. All platforms")
    
    while True:
        try:
            choice = input("Enter your choice (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            else:
                print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")
        except KeyboardInterrupt:
            print("\nBuild cancelled by user.")
            return None


def build_project(target_os=None) -> bool:
    if target_os is None:
        target_os = select_target_os()
        if target_os is None:
            return False
    
    # Map choices to OS names
    os_map = {'1': platform.system(), '2': 'Windows', '3': 'Linux', '4': 'Darwin', '5': 'All'}
    selected_os = os_map[target_os]
    
    print(f"=== Building {APP_NAME} for {selected_os} ===")
    
    python = _venv_python()
    if python is None:
        print("Virtual environment .venv not found.")
        return False

    main_file = ROOT / "main.py"
    if not main_file.exists():
        print("main.py not found.")
        return False

    if not _ensure_pyinstaller(python):
        return False

    # Determine separator based on the host OS (where we're building)
    sep = os.pathsep  # Correct separator for the host OS
    cmd = [
        str(python), "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        "--hidden-import=apscheduler",
        "--hidden-import=plyer",
        "--hidden-import=ttkbootstrap",
        "--hidden-import=tkinter",
        "--hidden-import=datetime",
        main_file.name,
    ]
    icon = ROOT / "calendar.ico"
    if icon.exists():
        cmd.append(f"--icon={icon}")
        # Use correct path separator for PyInstaller (semicolon on Windows)
        if os.name == 'nt':  # Windows
            cmd.append(f"--add-data={icon};.")
        else:  # Unix-like systems
            cmd.append(f"--add-data={icon}:{os.curdir}")

    # Include data files required by the application
    import_dirs = ["import"]
    for import_dir in import_dirs:
        dir_path = ROOT / import_dir
        if dir_path.exists() and dir_path.is_dir():
            if os.name == 'nt':  # Windows
                cmd.append(f"--add-data={dir_path};.")
            else:  # Unix-like systems
                cmd.append(f"--add-data={dir_path}:{os.curdir}")

    print("Starting PyInstaller...")
    try:
        subprocess.run(cmd, cwd=str(ROOT), check=True)
        print("Build completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build error: {e}")
        return False


def clean_up() -> None:
    print("\n=== Cleanup Process ===")
    for d in ("build", "__pycache__"):
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
            print(f"Removed: {d}")
    spec = ROOT / f"{APP_NAME}.spec"
    if spec.exists():
        spec.unlink()
        print(f"Removed: {spec.name}")


def main() -> None:
    if build_project():
        clean_up()
        current_os = platform.system()
        if current_os.lower() == 'windows':
            exe = f"{APP_NAME}.exe"
        else:
            exe = APP_NAME
        print(f"\nBuild completed successfully. Executable: dist/{exe}")
    else:
        print("\nBuild failed.")


if __name__ == "__main__":
    main()