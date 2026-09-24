"""Модуль управления данными приложения."""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict


def _resolve_base_dir() -> Path:
    """Каталог exe/скрипта — рядом с ним портативно лежит папка import/."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR: Path = _resolve_base_dir()
IMPORT_DIR: Path = BASE_DIR / "import"
DB_FILE: Path = IMPORT_DIR / "db.json"
BACKUP_FILE: Path = IMPORT_DIR / "db.back.json"
TMP_FILE: Path = IMPORT_DIR / "db.tmp.json"


def ensure_dirs() -> None:
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)


ensure_dirs()


DEFAULT_SETTINGS: Dict[str, Any] = {
    "window": {"x": 100, "y": 100, "w": 1200, "h": 800},
    "notify_before": 10,
    "snooze_minutes": 5,
}


def _empty_db() -> Dict[str, Any]:
    return {"events": [], "recurring": [], "templates": []}


def load_db() -> Dict[str, Any]:
    """Загружает базу данных из файла import/db.json."""
    if DB_FILE.exists():
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for key, default in _empty_db().items():
                data.setdefault(key, default)
            return data
        except Exception as e:
            print(f"Ошибка загрузки базы данных: {e}")
    return _empty_db()


def save_db(data: Dict[str, Any]) -> None:
    """Сохраняет базу данных в import/db.json."""
    ensure_dirs()
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения базы данных: {e}")


def initialize_db() -> None:
    ensure_dirs()
    if not DB_FILE.exists():
        save_db(_empty_db())


def make_backup() -> None:
    """Копирует текущий db.json в db.back.json (перед импортом)."""
    ensure_dirs()
    if DB_FILE.exists():
        try:
            shutil.copy2(DB_FILE, BACKUP_FILE)
        except Exception as e:
            print(f"Ошибка создания резервной копии: {e}")


def swap_with_backup() -> bool:
    """Меняет местами db.json и db.back.json. True если swap удался."""
    if not BACKUP_FILE.exists():
        return False
    ensure_dirs()
    try:
        if not DB_FILE.exists():
            os.replace(BACKUP_FILE, DB_FILE)
            return True
        os.replace(DB_FILE, TMP_FILE)
        os.replace(BACKUP_FILE, DB_FILE)
        os.replace(TMP_FILE, BACKUP_FILE)
        return True
    except Exception as e:
        print(f"Ошибка swap db/back: {e}")
        return False


def get_settings() -> Dict[str, Any]:
    return {
        "window": dict(DEFAULT_SETTINGS["window"]),
        "notify_before": DEFAULT_SETTINGS["notify_before"],
        "snooze_minutes": DEFAULT_SETTINGS["snooze_minutes"],
    }


def update_settings(settings: Dict[str, Any]) -> None:
    """Заглушка: настройки на диск не сохраняются."""
    pass