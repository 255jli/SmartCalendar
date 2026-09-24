"""Модуль обработки импорта JSON-файлов."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime

from data_manager import load_db, save_db, make_backup, BASE_DIR, IMPORT_DIR

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VALID_CATEGORIES = {'event', 'meeting', 'task', 'reminder', 'personal'}
VALID_STATUSES = {'pending', 'done', 'missed'}
VALID_FREQS = {'daily', 'weekly', 'monthly', 'yearly'}
SKIP_PREFIXES = ('settings', 'example', 'test_')
SKIP_NAMES = {'db.json', 'db.back.json', 'db.tmp.json'}


def _parse_time(value: Any) -> bool:
    try:
        h, m = str(value).split(':')
        return 0 <= int(h) <= 23 and 0 <= int(m) <= 59
    except (ValueError, AttributeError):
        return False


def _parse_date(value: Any) -> bool:
    try:
        datetime.fromisoformat(str(value))
        return True
    except (ValueError, TypeError):
        return False


def validate_event(event: Dict[str, Any]) -> bool:
    for field in ('id', 'title', 'date', 'start'):
        if field not in event:
            return False
    if not _parse_date(event['date']) or not _parse_time(event['start']):
        return False
    if 'duration' in event:
        try:
            if int(event['duration']) <= 0:
                return False
        except (ValueError, TypeError):
            return False
    if event.get('category') and event['category'] not in VALID_CATEGORIES:
        return False
    if event.get('status') and event['status'] not in VALID_STATUSES:
        return False
    return True


def validate_recurring_event(rec: Dict[str, Any]) -> bool:
    for field in ('id', 'title', 'start', 'rule'):
        if field not in rec:
            return False
    if not _parse_time(rec['start']):
        return False
    rule = rec['rule']
    if not isinstance(rule, dict) or rule.get('freq') not in VALID_FREQS:
        return False
    if 'interval' in rule:
        try:
            if int(rule['interval']) <= 0:
                return False
        except (ValueError, TypeError):
            return False
    if 'duration' in rec:
        try:
            if int(rec['duration']) <= 0:
                return False
        except (ValueError, TypeError):
            return False
    if rec.get('category') and rec['category'] not in VALID_CATEGORIES:
        return False
    if rec.get('status') and rec['status'] not in VALID_STATUSES:
        return False
    return True


def _normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    e = dict(event)
    e.setdefault('duration', 60)
    e.setdefault('category', 'event')
    e.setdefault('description', '')
    e.setdefault('status', 'pending')
    e.setdefault('created_at', datetime.now().isoformat())
    try:
        e['duration'] = int(e['duration'])
    except (ValueError, TypeError):
        e['duration'] = 60
    return e


def _normalize_recurring(rec: Dict[str, Any]) -> Dict[str, Any]:
    r = dict(rec)
    r.setdefault('duration', 60)
    r.setdefault('category', 'event')
    r.setdefault('description', '')
    r.setdefault('status', 'pending')
    r.setdefault('done_dates', [])
    r.setdefault('skipped_dates', [])
    r.setdefault('created_at', datetime.now().isoformat())
    rule = dict(r.get('rule') or {'freq': 'daily'})
    rule.setdefault('interval', 1)
    try:
        rule['interval'] = int(rule['interval'])
    except (ValueError, TypeError):
        rule['interval'] = 1
    r['rule'] = rule
    try:
        r['duration'] = int(r['duration'])
    except (ValueError, TypeError):
        r['duration'] = 60
    return r


def import_file(file_path: Path) -> Tuple[int, int, List[str]]:
    """Импортирует один JSON в db.json (merge по id)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return 0, 0, [f"Ошибка чтения {file_path.name}: {e}"]

    if not isinstance(data, dict):
        return 0, 0, [f"{file_path.name}: ожидался объект"]
    events = data.get('events', [])
    recurring = data.get('recurring', [])
    if not isinstance(events, list) or not isinstance(recurring, list):
        return 0, 0, [f"{file_path.name}: 'events'/'recurring' должны быть массивами"]

    db = load_db()
    existing_events = {e['id']: e for e in db['events'] if 'id' in e}
    existing_rec = {r['id']: r for r in db['recurring'] if 'id' in r}

    imported_events = 0
    imported_rec = 0
    errors: List[str] = []

    for raw in events:
        if not isinstance(raw, dict):
            errors.append(f"{file_path.name}: событие не объект")
            continue
        ev = _normalize_event(raw)
        if not validate_event(ev):
            errors.append(f"{file_path.name}: невалидное событие {ev.get('id', '?')}")
            continue
        if ev['id'] in existing_events:
            existing_events[ev['id']].update(ev)
        else:
            db['events'].append(ev)
            existing_events[ev['id']] = ev
            imported_events += 1

    for raw in recurring:
        if not isinstance(raw, dict):
            errors.append(f"{file_path.name}: повтор. событие не объект")
            continue
        rec = _normalize_recurring(raw)
        if not validate_recurring_event(rec):
            errors.append(f"{file_path.name}: невалидное повтор. {rec.get('id', '?')}")
            continue
        if rec['id'] in existing_rec:
            existing_rec[rec['id']].update(rec)
        else:
            db['recurring'].append(rec)
            existing_rec[rec['id']] = rec
            imported_rec += 1

    save_db(db)
    logger.info(f"{file_path.name}: +{imported_events}, +{imported_rec}")
    return imported_events, imported_rec, errors


def import_files(paths: List[Path]) -> Tuple[int, int, List[str]]:
    """Импортирует список файлов; один бэкап db.json перед началом."""
    make_backup()
    total_e = total_r = 0
    errors: List[str] = []
    for p in paths:
        try:
            e, r, errs = import_file(p)
            total_e += e
            total_r += r
            errors.extend(errs)
        except Exception as ex:
            errors.append(f"{p.name}: {ex}")
    return total_e, total_r, errors


def get_import_files() -> List[Path]:
    """JSON-кандидаты: рядом с exe и в import/. Без db.* и служебных."""
    result: List[Path] = []
    seen: set = set()
    for folder in (BASE_DIR, IMPORT_DIR):
        if not folder.exists():
            continue
        for f in sorted(folder.iterdir()):
            if not f.is_file() or f.suffix.lower() != '.json':
                continue
            name_low = f.name.lower()
            if name_low in SKIP_NAMES:
                continue
            if name_low.startswith(SKIP_PREFIXES):
                continue
            rp = f.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            result.append(f)
    return result


def auto_import() -> List[str]:
    """Служебный автоимпорт (сейчас не используется основным UI)."""
    errors: List[str] = []
    for file_path in get_import_files():
        try:
            _, _, errs = import_file(file_path)
            errors.extend(errs)
        except Exception as e:
            errors.append(f"Ошибка импорта {file_path.name}: {e}")
    return errors