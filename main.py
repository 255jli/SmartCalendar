#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import sys
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from apscheduler.schedulers.background import BackgroundScheduler

# ─── Base Directory Configuration (For PyInstaller and Standard Execution) ───
if getattr(sys, 'frozen', False):
    base_dir = Path(sys.executable).resolve().parent
else:
    base_dir = Path(__file__).resolve().parent

# ─── Secure Import of ttkbootstrap ───
ttkbootstrap_ok = False
try:
    import ttkbootstrap as ttkb
    from ttkbootstrap.constants import *
    ttkbootstrap_ok = True
except Exception:
    pass

# ─── Secure Import of plyer ───
plyer_ok = False
try:
    from plyer import notification as plyer_notify
    plyer_ok = True
except Exception:
    pass

# ─── Project Module Imports ───
sys.path.insert(0, str(base_dir))
from data_manager import load_db, save_db, initialize_db, get_settings, update_settings
from calendar_view import CalendarView
from event_feed import EventFeed
from settings_controls import SettingsControls
from import_bar import ImportBar
from tabbed_ui import TabbedUI

# ─── Constants Definition ───
APP_NAME = "Smart Calendar"

# ─── Вспомогательные функции ───
def log(msg):
    """Logs application messages with timestamp."""
    print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {msg}')

def get_all_events(data, start, end):
    """Retrieves all events within a specified date range."""
    events = []
    
    # Standard events
    for e in data['events']:
        try:
            event_date = datetime.date.fromisoformat(e['date'])
            if start <= event_date <= end:
                events.append(e)
        except:
            pass
    
    # Recurring events
    for rec in data['recurring']:
        try:
            dates = gen_recurring_dates(rec, start, end)
            for date in dates:
                if date not in rec.get('skipped_dates', []):
                    ev = {
                        **rec,
                        'date': date.isoformat(),
                        'id': f'rec:{rec["id"]}:{date.isoformat()}',
                        'status': 'pending' if date not in rec.get('done_dates', []) else 'done'
                    }
                    if start <= date <= end:
                        events.append(ev)
        except:
            pass
    
    return events


def gen_recurring_dates(rec, start, end):
    """Generates dates for recurring events based on recurrence rules."""
    dates = []
    try:
        rule = rec.get('rule', {})
        freq = rule.get('freq', 'daily')
        interval = rule.get('interval', 1)
        
        if freq == 'daily':
            current = start
            while current <= end:
                dates.append(current)
                current += datetime.timedelta(days=interval)
        elif freq == 'weekly':
            current = start
            while current <= end:
                dates.append(current)
                current += datetime.timedelta(weeks=interval)
        elif freq == 'monthly':
            current = start
            while current <= end:
                dates.append(current)
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
        elif freq == 'yearly':
            current = start
            while current <= end:
                dates.append(current)
                current = current.replace(year=current.year + 1)
    except Exception as e:
        log(f'gen_recurring_dates error: {e}')
    
    return dates


def update_statuses(data):
    """Updates event statuses based on current date."""
    today = datetime.date.today()
    
    for e in data['events']:
        try:
            event_date = datetime.date.fromisoformat(e['date'])
            if e['status'] == 'pending' and event_date < today:
                e['status'] = 'missed'
        except:
            pass
    
    return data

# ─── Глобальные переменные ───
scheduler = BackgroundScheduler()
scheduler.start()

# ─── Main Application Class ───
class CalendarApp:
    def __init__(self):
        """Initializes the Smart Calendar application."""
        initialize_db()
        self.data = load_db()
        self.editing_id = None
        self.today = datetime.date.today()
        
        if ttkbootstrap_ok:
            self.root = ttkb.Window(themename="flatly")
        else:
            self.root = tk.Tk()
        self.root.title(APP_NAME)
        window_settings = get_settings().get('window', {'x': 100, 'y': 100, 'w': 1200, 'h': 800})
        self.root.geometry(f"{window_settings['w']}x{window_settings['h']}+{window_settings['x']}+{window_settings['y']}")
        self.root.configure(bg='#f9f9f9')

        self._setup_styles()
        self._build_ui()
        self.refresh()
        self.root.after(120000, self._auto_refresh)
        self.root.bind('<Configure>', self._on_configure)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.configure('TFrame', background='#f9f9f9')
        style.configure('TLabel', background='#f9f9f9', foreground='#222222', font=('Segoe UI', 11))
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#333')
        style.configure('Subheader.TLabel', font=('Segoe UI', 10), foreground='#888')
        style.configure('TButton', font=('Segoe UI', 9), background='#ffffff')
        style.map('TButton', background=[('active', '#e8e8e8')])

    def _build_ui(self):
        """Constructs the main user interface components."""
        # Main container
        main = ttk.Frame(self.root)
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Left panel (calendar and import)
        left = ttk.Frame(main, width=600)
        left.pack(side='left', fill='y', padx=(0, 10))
        left.pack_propagate(False)

        # Right panel (settings and events tabs)
        right = ttk.Frame(main, width=400)
        right.pack(side='left', fill='y', padx=(10, 0))
        right.pack_propagate(False)

        # Initialize UI components
        self.import_bar = ImportBar(left, on_import=self._manual_import)
        self.calendar = CalendarView(left, on_month_change=self._refresh_calendar, on_event_select=self._on_event_selected)
        
        # Create tabs for events and settings
        self.tabbed_ui = TabbedUI(
            right,
            events=[],
            on_select_event=self._on_event_selected,
            on_event_action=self._handle_feed_item_click,
            on_settings_change=self._update_settings,
            on_data_change=self.refresh,
        )

        # Configure column weights for optimal layout
        main.columnconfigure(0, weight=1)

    def _on_event_selected(self, event):
        """Обработчик выбора события."""
        if isinstance(event, dict) and 'title' in event:
            self.tabbed_ui.show_event_details(event)

    def _refresh_calendar(self):
        """Обновляет календарь."""
        week_start = self.calendar.curr_week_start
        week_end = week_start + datetime.timedelta(days=6)
        events = get_all_events(self.data, week_start, week_end)
        self.calendar.refresh(events)

    def _update_settings(self, settings: dict) -> None:
        """Updates application settings and applies changes."""
        try:
            if 'notify_before' in settings or 'snooze_minutes' in settings:
                reschedule_all()
            
            if 'window' in settings:
                window_settings = settings['window']
                self.root.geometry(f"{window_settings['w']}x{window_settings['h']}+{window_settings['x']}+{window_settings['y']}")
        except Exception as ex:
            log(f'update_settings failed: {ex}')

    def _handle_feed_item_click(self, action: str, event: dict) -> None:
        """Handles actions from event feed items."""
        if action == 'complete':
            self._complete_event(event)
        elif action == 'edit':
            self._edit_event(event)
        elif action == 'delete':
            self._delete_event(event)

    def refresh(self):
        """Refreshes application data and interface."""
        try:
            self.data = load_db()
            self.data = update_statuses(self.data)
            save_db(self.data)
            
            events_to_show = get_all_events(self.data, self.today - datetime.timedelta(days=7),
                                           self.today + datetime.timedelta(days=60))
            if len(events_to_show) > 30:
                events_to_show = sorted(events_to_show, key=lambda x: (x['date'], x['start']))[:30]
            
            self.tabbed_ui.update_events(events_to_show)
            self._refresh_calendar()
        except Exception as ex:
            log(f'refresh failed: {ex}')

    def _manual_import(self):
        """Triggered after successful import from the import panel."""
        self.refresh()

    def _complete_event(self, event: dict) -> None:
        """Marks an event as completed."""
        try:
            data = load_db()
            now_iso = datetime.datetime.now().isoformat()
            event_id = event['id']
            
            if event_id.startswith('rec:'):
                _, rec_id, date = event_id.split(':', 2)
                for rec in data['recurring']:
                    if rec['id'] == rec_id:
                        if date not in rec['done_dates']:
                            rec['done_dates'].append(date)
                        break
            else:
                for e in data['events']:
                    if e['id'] == event_id:
                        e['status'] = 'done'
                        e['completed_at'] = now_iso
                        unschedule_event(event_id)
                        break
            save_db(data)
            self.refresh()
        except Exception as ex:
            log(f'complete_event failed: {ex}')

    def _edit_event(self, event: dict) -> None:
        """Edits an existing event."""
        title = simpledialog.askstring("Edit", "Title:",
                                       initialvalue=event['title'], parent=self.root)
        if not title:
            return
        desc = simpledialog.askstring("Edit", "Description:",
                                      initialvalue=event.get('description', ''), parent=self.root)
        new_date = simpledialog.askstring("Edit", "Date (YYYY-MM-DD):",
                                          initialvalue=event['date'], parent=self.root)
        if not new_date:
            return
        try:
            datetime.date.fromisoformat(new_date)
        except:
            messagebox.showerror("Error", "Invalid date format")
            return

        data = load_db()
        for ev in data['events']:
            if ev['id'] == event['id']:
                unschedule_event(ev['id'])
                ev['title'] = title
                ev['description'] = desc or ''
                ev['date'] = new_date
                ev['updated_at'] = datetime.datetime.now().isoformat()
                break
        save_db(data)
        reschedule_all()
        self.refresh()

    def _delete_event(self, event: dict) -> None:
        """Deletes an event."""
        try:
            data = load_db()
            event_id = event['id']
            
            if event_id.startswith('rec:'):
                _, rec_id, _ = event_id.split(':', 2)
                data['recurring'] = [r for r in data['recurring'] if r['id'] != rec_id]
            else:
                unschedule_event(event_id)
                data['events'] = [e for e in data['events'] if e['id'] != event_id]
            
            save_db(data)
            reschedule_all()
            self.refresh()
            
            messagebox.showinfo("Deletion", f"Event '{event['title']}' successfully removed.")
        except Exception as ex:
            log(f'delete_event failed: {ex}')
            messagebox.showerror("Error", f"Error deleting event: {ex}")

    def _on_configure(self, event):
        """Handles window resize events."""
        if event.widget == self.root:
            try:
                update_settings({
                    "window": {
                        "x": self.root.winfo_x(),
                        "y": self.root.winfo_y(),
                        "w": self.root.winfo_width(),
                        "h": self.root.winfo_height()
                    }
                })
            except:
                pass

    def _on_close(self):
        """Handles application close event."""
        try:
            scheduler.shutdown(wait=False)
        except:
            pass
        self.root.destroy()

    def _auto_refresh(self):
        """Performs automatic refresh at regular intervals."""
        self.refresh()
        self.root.after(120000, self._auto_refresh)

# ─── Scheduler Functions ───
def unschedule_event(event_id):
    """Removes an event from the scheduler."""
    try:
        scheduler.remove_job(event_id)
    except:
        pass


def reschedule_all():
    """Reschedules all events in the scheduler."""
    scheduler.remove_all_jobs()
    
    data = load_db()
    now = datetime.datetime.now()
    notify_before = get_settings().get('notify_before', 10)
    
    for e in data['events']:
        try:
            if e['status'] != 'pending':
                continue
            event_time = datetime.datetime.fromisoformat(f"{e['date']} {e['start']}")
            if event_time > now:
                scheduler.add_job(
                    notify_event, 'date', run_date=event_time - datetime.timedelta(minutes=notify_before),
                    args=[e['id']], id=e['id'], misfire_grace_time=60
                )
        except Exception as ex:
            log(f'Error scheduling event: {ex}')

    for rec in data['recurring']:
        try:
            dates = gen_recurring_dates(rec, datetime.date.today(),
                                        datetime.date.today() + datetime.timedelta(days=365))
            for date in dates:
                if date not in rec.get('skipped_dates', []):
                    event_time = datetime.datetime.fromisoformat(f"{date.isoformat()} {rec['start']}")
                    if event_time > now:
                        event_id = f'rec:{rec["id"]}:{date.isoformat()}'
                        if event_id not in [j.id for j in scheduler.get_jobs()]:
                            scheduler.add_job(
                                notify_event, 'date',
                                run_date=event_time - datetime.timedelta(minutes=notify_before),
                                args=[event_id], id=event_id, misfire_grace_time=60
                            )
        except Exception as ex:
            log(f'Error scheduling recurring event: {ex}')

# ─── Notifications ───
def notify_event(event_id):
    """Sends event notification to the user."""
    try:
        data = load_db()
        event = None
        
        for e in data['events']:
            if e['id'] == event_id:
                event = e
                break
        if not event and event_id.startswith('rec:'):
            parts = event_id.split(':', 2)
            if len(parts) >= 3:
                rec_id, date = parts[1], parts[2]
                for rec in data['recurring']:
                    if rec['id'] == rec_id:
                        event = {
                            **rec,
                            'date': date,
                            'id': event_id,
                            'status': 'pending' if date not in rec.get('done_dates', []) else 'done'
                        }
                        break
        
        if event and plyer_ok:
            plyer_notify.notify(
                title='Smart Calendar - Event Notification',
                message=f"Event Reminder: {event['title']}\nDate: {event['date']} Time: {event['start']}",
                timeout=10,
                app_name='Smart Calendar',
                app_icon='calendar.ico'
            )
    except Exception as ex:
        log(f'notify_event failed: {ex}')

# ─── Application Startup ───
if __name__ == '__main__':
    try:
        app = CalendarApp()
        app.root.title(APP_NAME)
        reschedule_all()  # Start event notifications
        app.root.mainloop()
    except Exception as e:
        log(f'Critical error: {e}')
        print(f'Critical error occurred: {e}')
        input("Press Enter to exit...")
