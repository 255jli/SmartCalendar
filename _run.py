#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launcher for Smart Calendar.

Работает на Windows, Linux и macOS.
Порядок действий:
  1. Проверить наличие .venv; при отсутствии — предложить создать.
  2. Если ttkbootstrap не установлен — предложить поставить (опционально).
  3. Запустить main.py.
"""

import sys

from _common import ROOT, ensure_venv, install_missing, has_package, ask_extras


def main() -> int:
    print("=== Smart Calendar Launcher ===\n")

    if not (ROOT / "main.py").exists():
        print(f"main.py not found in {ROOT}")
        input("Press Enter to exit...")
        return 1

    python = ensure_venv()

    packages = []
    if not has_package(python, "ttkbootstrap"):
        if ask_extras():
            packages.append("ttkbootstrap")

    if packages and not install_missing(python, packages):
        input("Press Enter to exit...")
        return 1

    print("\n=== Launching Smart Calendar ===\n")
    sys.path.insert(0, str(ROOT))
    try:
        from main import main as app_main
        app_main()
        return 0
    except ImportError as e:
        print(f"Failed to import main application: {e}")
        input("Press Enter to exit...")
        return 1
    except Exception as e:
        print(f"Error running application: {e}")
        input("Press Enter to exit...")
        return 1


if __name__ == "__main__":
    sys.exit(main())