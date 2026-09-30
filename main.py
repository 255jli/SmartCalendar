#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Точка входа приложения Smart Calendar.

Режимы интерфейса:
- ttkbootstrap (если установлен) — современное оформление;
- чистый tkinter/ttk — базовый режим без внешних зависимостей.

Импорт JSON выполняется через import_handler. События в календарь
передаются явно при каждом обновлении.
"""

import datetime
import sys
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Необязательная библиотека оформления.
ttkbootstrap_ok = False
try:
    import ttkbootstrap as ttkb  # type: ignore
    ttkbootstrap_ok = True
except Exception:
    pass

# Корневой каталог проекта: рядом с exe (frozen) или со скриптом.
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
    _RES = Path(sys._MEIPASS)
    ICON_ICO = _RES / "calendar.ico"
    ICON_PNG = _RES / "calendar.png"
    ICON_PNG_512 = _RES / "calendar_512.png"
else:
    BASE_DIR = Path(__file__).resolve().parent
    ICON_ICO = BASE_DIR / "calendar.ico"
    ICON_PNG = BASE_DIR / "calendar.png"
    ICON_PNG_512 = BASE_DIR / "calendar_512.png"

sys.path.insert(0, str(BASE_DIR))

from data_manager import load_db, save_db
from calendar_view import CalendarView
from event_feed import EventFeed
from import_bar import ImportBar
from import_handler import get_import_files, import_files
from settings_controls import SettingsControls


APP_NAME = "Smart Calendar"
DEFAULT_CATEGORY = "event"


def log(msg: str) -> None:
    """Вывод сообщения в консоль с временной меткой."""
    print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {msg}')


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def gen_recurring_dates(rec, start, end):
    """Возвращает даты повторяющегося события в диапазоне [start, end].

    Требует поле start_date (YYYY-MM-DD). Если оно отсутствует,
    возвращает пустой список и логирует предупреждение.
    """
    dates = []
    start_date = rec.get('start_date')
    if not start_date:
        log(f"recurring '{rec.get('id', '?')}' пропущено: нет start_date")
        return dates

    try:
        base = datetime.date.fromisoformat(str(start_date))
    except (ValueError, TypeError):
        log(f"recurring '{rec.get('id', '?')}' пропущено: некорректный start_date")
        return dates

    rule = rec.get('rule') or {}
    freq = rule.get('freq', 'daily')
    interval = max(_safe_int(rule.get('interval', 1), 1), 1)

    until = None
    until_raw = rule.get('until')
    if until_raw:
        try:
            until = datetime.date.fromisoformat(str(until_raw))
        except (ValueError, TypeError):
            until = None

    limit = min(end, until) if until else end
    if base > limit:
        return dates

    current = base
    guard = 0
    while current <= limit and guard < 5000:
        guard += 1
        if current >= start:
            dates.append(current)

        if freq == 'daily':
            current += datetime.timedelta(days=interval)
        elif freq == 'weekly':
            current += datetime.timedelta(weeks=interval)
        elif freq == 'monthly':
            month = current.month + interval
            year = current.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            try:
                current = current.replace(year=year, month=month)
            except ValueError:
                break
        elif freq == 'yearly':
            try:
                current = current.replace(year=current.year + interval)
            except ValueError:
                break
        else:
            break
    return dates


def get_all_events(data, start, end):
    """Возвращает обычные и развёрнутые повторяющиеся события за период."""
    events = []

    for e in data.get('events', []):
        try:
            event_date = datetime.date.fromisoformat(e['date'])
        except (KeyError, ValueError, TypeError):
            continue
        if start <= event_date <= end:
            events.append(e)

    for rec in data.get('recurring', []):
        done = set(rec.get('done_dates', []) or [])
        skipped = set(rec.get('skipped_dates', []) or [])
        for d in gen_recurring_dates(rec, start, end):
            iso = d.isoformat()
            if iso in skipped:
                continue
            ev = dict(rec)
            ev['date'] = iso
            ev['id'] = f"rec:{rec.get('id', '?')}:{iso}"
            ev['status'] = 'done' if iso in done else 'pending'
            ev.pop('rule', None)
            ev.pop('done_dates', None)
            ev.pop('skipped_dates', None)
            events.append(ev)
    return events


class SmartCalendar:
    """Главное окно приложения."""

    def __init__(self):
        # Единый корневой виджет: либо ttkbootstrap.Window, либо tk.Tk.
        if ttkbootstrap_ok:
            self.root = ttkb.Window(themename="litera")
        else:
            self.root = tk.Tk()

        self.root.title(APP_NAME)
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        self._set_icon()

        self.db = load_db()
        self.current_date = datetime.date.today()

        self.create_menu()
        self.create_toolbar()
        self.create_status_bar()
        self.create_main_content()

        self._auto_import()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        log('Application initialized')

    def _set_icon(self) -> None:
        """Устанавливает иконку окна кросс-платформенно.

        Приоритет источников:
        1. calendar_512.png — максимальное качество для панели задач.
        2. calendar.png     — резервный PNG.
        3. calendar.ico     — запасной вариант для Windows.
        """
        for attr, path in (
            ("_icon_img_512", ICON_PNG_512),
            ("_icon_img", ICON_PNG),
        ):
            try:
                if path.exists():
                    img = tk.PhotoImage(file=str(path))
                    setattr(self, attr, img)
                    self.root.iconphoto(True, img)
                    return
            except Exception:
                continue
        try:
            if ICON_ICO.exists():
                self.root.iconbitmap(str(ICON_ICO))
        except Exception:
            pass

    def _auto_import(self) -> None:
        """Импорт подходящих JSON при запуске через import_handler."""
        try:
            files = get_import_files()
            if not files:
                return
            imported, _, errors = import_files(files)
            for err in errors[:5]:
                log(f"import: {err}")
            if imported:
                self.db = load_db()
                log(f"auto-import: {imported} новых событий")
        except Exception as e:
            log(f"auto-import failed: {e}")

    def create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self.refresh_all)

    def create_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        ttk.Button(toolbar, text="Add Event", command=self.add_event).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Today", command=self.go_to_today).pack(side=tk.LEFT, padx=2)

    def create_main_content(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.calendar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.calendar_frame, text='Calendar')

        self.feed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.feed_frame, text='Events')

        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text='Settings')

        self.calendar_view = CalendarView(
            parent=self.calendar_frame,
            on_date_select=self.show_date_events,
            on_month_change=self.on_calendar_month_change,
            on_event_select=self.show_event_detail_simple,
        )

        # Панель импорта над лентой событий.
        self.import_bar = ImportBar(
            parent=self.feed_frame,
            on_import=self._on_import_done,
        )

        self.event_feed = EventFeed(
            parent=self.feed_frame,
            on_item_click=self.show_event_detail_from_feed,
        )

        # Вкладка Settings: параметры уведомлений и swap db.json/db.back.json.
        self.settings_controls = SettingsControls(
            parent=self.settings_frame,
            on_settings_change=self._on_settings_change,
            on_data_change=self._reload_after_backup,
        )

        self.refresh_all()

    def create_status_bar(self) -> None:
        self.status_var = tk.StringVar()
        self.status_var.set(f"Ready | Today: {datetime.date.today().strftime('%A, %B %d, %Y')}")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_import_done(self) -> None:
        """Перечитывает базу и обновляет UI после ручного импорта."""
        self.db = load_db()
        self.refresh_all()

    def _reload_after_backup(self) -> None:
        """Перечитывает базу после swap db.json / db.back.json и обновляет UI."""
        self.db = load_db()
        self.refresh_all()

    def _on_settings_change(self, settings) -> None:
        """Реакция на изменение настроек в UI.

        Персистентность настроек будет добавлена отдельным этапом
        через data_manager.update_settings.
        """
        log(f"settings changed: {settings}")

    def on_calendar_month_change(self, *args) -> None:
        try:
            if args and isinstance(args[0], datetime.date):
                self.status_var.set(f"Showing: {args[0].strftime('%B %Y')}")
            else:
                self.status_var.set(
                    f"Ready | Today: {datetime.date.today().strftime('%A, %B %d, %Y')}"
                )
        except Exception as e:
            log(f"on_calendar_month_change: {e}")

    # ── Обработчики событий UI ────────────────────────────────────────

    def show_date_events(self, selected_date) -> None:
        """Обработчик выбора даты (заготовка для будущего развития)."""
        pass

    def show_event_detail_simple(self, event_data) -> None:
        self.show_event_detail(event_data)

    def show_event_detail_from_feed(self, action, event_data) -> None:
        if action == 'edit':
            self.show_event_detail(event_data)
        elif action == 'delete':
            if messagebox.askyesno("Confirm Delete",
                                   f"Delete event '{event_data['title']}'?"):
                self._delete_event(event_data)
        elif action == 'complete':
            self._complete_event(event_data)

    def _delete_event(self, event_data) -> None:
        eid = str(event_data.get('id', ''))
        if eid.startswith('rec:'):
            messagebox.showinfo("Delete",
                                "Recurring occurrence cannot be deleted individually.")
            return
        before = len(self.db['events'])
        self.db['events'] = [e for e in self.db['events'] if e.get('id') != eid]
        if len(self.db['events']) != before:
            save_db(self.db)
            self.refresh_all()

    def _complete_event(self, event_data) -> None:
        eid = str(event_data.get('id', ''))
        if eid.startswith('rec:'):
            parts = eid.split(':', 2)
            if len(parts) == 3:
                _, rec_id, iso = parts
                for rec in self.db.get('recurring', []):
                    if rec.get('id') == rec_id:
                        done = set(rec.get('done_dates', []) or [])
                        done.add(iso)
                        rec['done_dates'] = sorted(done)
                        save_db(self.db)
                        self.refresh_all()
                        return
            return
        for e in self.db['events']:
            if e.get('id') == eid:
                e['status'] = 'done'
                e['completed_at'] = datetime.datetime.now().isoformat()
                save_db(self.db)
                self.refresh_all()
                return

    # ── Лента событий и календарь ─────────────────────────────────────

    def _format_for_feed(self, event: dict) -> dict:
        """Приводит событие к виду, ожидаемому EventFeed."""
        return {
            'id': event.get('id', ''),
            'title': event.get('title', 'Untitled'),
            'date': event.get('date', str(datetime.date.today())),
            'description': event.get('description', ''),
            'status': event.get('status', 'pending'),
            'start': event.get('start', '00:00'),
            'duration': _safe_int(event.get('duration', 60), 60),
            'category': event.get('category', DEFAULT_CATEGORY),
        }

    def refresh_event_feed(self) -> None:
        """Обновляет ленту событий на год вперёд."""
        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=365)
        events = get_all_events(self.db, today, horizon)
        events.sort(key=lambda e: (e.get('date', ''), e.get('start', '')))
        formatted = [self._format_for_feed(e) for e in events]
        if hasattr(self.event_feed, 'update_events'):
            self.event_feed.update_events(formatted)

    def refresh_all(self) -> None:
        """Полное обновление календаря и ленты событий."""
        self.current_date = datetime.date.today()
        start, end = self.calendar_view._week_range()
        events = get_all_events(self.db, start, end)
        self.calendar_view.refresh(events=events)
        self.refresh_event_feed()
        self.status_var.set(
            f"Refreshed | Today: {datetime.date.today().strftime('%A, %B %d, %Y')}"
        )

    # ── Навигация ─────────────────────────────────────────────────────

    def go_to_today(self) -> None:
        today = datetime.date.today()
        self.current_date = today
        self.calendar_view.reset_to_today()
        self.refresh_all()
        self.status_var.set(f"Today: {today.strftime('%A, %B %d, %Y')}")

    def prev_month(self) -> None:
        self.calendar_view.prev_month()
        self.refresh_all()

    def next_month(self) -> None:
        self.calendar_view.next_month()
        self.refresh_all()

    # ── Диалоги ───────────────────────────────────────────────────────

    def add_event(self) -> None:
        """Диалог создания нового события."""
        title = simpledialog.askstring("New Event", "Event Title:")
        if not title:
            return

        date_str = simpledialog.askstring(
            "New Event",
            f"Date (YYYY-MM-DD) [default: {self.current_date}]:",
            initialvalue=str(self.current_date),
        )
        if not date_str:
            return
        try:
            datetime.date.fromisoformat(date_str)
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        time_str = simpledialog.askstring("New Event", "Time (HH:MM) [optional]:")
        if time_str:
            try:
                datetime.datetime.strptime(time_str, '%H:%M')
            except ValueError:
                messagebox.showerror("Error", "Invalid time format. Please use HH:MM.")
                return

        description = simpledialog.askstring("New Event", "Description [optional]:")

        event_id = f"event_{int(datetime.datetime.now().timestamp() * 1000)}"
        self.db['events'].append({
            'id': event_id,
            'title': title,
            'date': date_str,
            'start': time_str or '00:00',
            'duration': 60,
            'category': DEFAULT_CATEGORY,
            'description': description or '',
            'status': 'pending',
            'created_at': datetime.datetime.now().isoformat(),
        })
        save_db(self.db)
        self.refresh_all()
        messagebox.showinfo("Success", "Event added successfully!")

    def show_event_detail(self, event: dict) -> None:
        """Окно с деталями события."""
        win = tk.Toplevel(self.root)
        win.title(f"Event: {event.get('title', 'Untitled')}")
        win.geometry("420x360")
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text=event.get('title', ''),
                  font=('Segoe UI', 12, 'bold')).pack(padx=10, pady=5, anchor='w')
        ttk.Label(win, text=f"Date: {event.get('date', '')}") \
            .pack(padx=10, pady=2, anchor='w')
        ttk.Label(win, text=f"Start: {event.get('start', '')}") \
            .pack(padx=10, pady=2, anchor='w')
        ttk.Label(win, text=f"Duration: {event.get('duration', 60)} min") \
            .pack(padx=10, pady=2, anchor='w')
        ttk.Label(win, text=f"Category: {event.get('category', DEFAULT_CATEGORY)}") \
            .pack(padx=10, pady=2, anchor='w')
        ttk.Label(win, text=f"Status: {event.get('status', 'pending')}") \
            .pack(padx=10, pady=2, anchor='w')

        desc_frame = ttk.LabelFrame(win, text="Description")
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        desc = tk.Text(desc_frame, wrap=tk.WORD, height=6)
        desc.insert(tk.END, event.get('description', '') or 'No description')
        desc.config(state=tk.DISABLED)
        desc.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=8)

    def on_closing(self) -> None:
        self.root.quit()
        self.root.destroy()
        log('Application closed')

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    try:
        app = SmartCalendar()
        app.run()
    except Exception as e:
        log(f'Application error: {e}')
        log(traceback.format_exc())
        try:
            messagebox.showerror('Error', f'Application error: {e}')
        except Exception:
            pass


if __name__ == '__main__':
    main()