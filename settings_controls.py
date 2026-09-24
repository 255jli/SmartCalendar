import tkinter as tk
from tkinter import messagebox
from typing import Any, Dict, Optional, Callable

from data_manager import BACKUP_FILE, swap_with_backup


def load_settings() -> Dict[str, Any]:
    return {
        "window": {"x": 100, "y": 100, "w": 1200, "h": 800},
        "notify_before": 10,
        "snooze_minutes": 5,
    }


def save_settings(settings: Dict[str, Any]) -> None:
    pass


class SettingsControls:
    """Компонент настроек."""

    def __init__(self, parent, on_settings_change: Optional[Callable] = None,
                 on_data_change: Optional[Callable] = None):
        self.parent = parent
        self.on_settings_change = on_settings_change
        self.on_data_change = on_data_change
        self._undo_applied = False
        self._create_widgets()
        self._load_settings()

    def _create_widgets(self) -> None:
        tk.Label(self.parent, text="Настройки",
                 font=('Segoe UI', 14, 'bold')).pack(pady=10, anchor='w')

        f = tk.Frame(self.parent)
        f.pack(fill='both', expand=True, padx=10, pady=5)

        tk.Label(f, text="Уведомлять до начала (мин):").pack(anchor='w', pady=(0, 5))
        self.notify_var = tk.IntVar()
        s1 = tk.Spinbox(f, from_=1, to=60, textvariable=self.notify_var, width=10)
        s1.pack(anchor='w', pady=(0, 10))
        s1.bind('<FocusOut>', self._save_settings)

        tk.Label(f, text="Время повтора уведомления (мин):").pack(anchor='w', pady=(0, 5))
        self.snooze_var = tk.IntVar()
        s2 = tk.Spinbox(f, from_=1, to=60, textvariable=self.snooze_var, width=10)
        s2.pack(anchor='w', pady=(0, 10))
        s2.bind('<FocusOut>', self._save_settings)

        tk.Button(f, text="Сбросить размеры и местоположение до заводских",
                  command=self._reset_to_defaults,
                  bg='#e6f3ff', font=('Segoe UI', 10)).pack(anchor='w', pady=(20, 10))

        tk.Label(f, text="Импорт", font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(20, 5))
        self.undo_btn = tk.Button(
            f,
            text="↶ Отменить последнее импортирование",
            command=self._toggle_undo,
            bg='#fff0e6',
            font=('Segoe UI', 10),
        )
        self.undo_btn.pack(anchor='w', pady=(0, 6))
        tk.Label(f, text="(использует import/db.back.json)",
                 font=('Segoe UI', 8), fg='#888').pack(anchor='w')

    def _load_settings(self) -> None:
        s = load_settings()
        self.notify_var.set(s.get('notify_before', 10))
        self.snooze_var.set(s.get('snooze_minutes', 5))

    def _save_settings(self, event=None) -> None:
        s = load_settings()
        s['notify_before'] = self.notify_var.get()
        s['snooze_minutes'] = self.snooze_var.get()
        if self.on_settings_change:
            self.on_settings_change(s)

    def _reset_to_defaults(self) -> None:
        s = load_settings()
        s['window'] = {"x": 100, "y": 100, "w": 1200, "h": 800}
        save_settings(s)
        if self.on_settings_change:
            self.on_settings_change(s)
        messagebox.showinfo("Настройки",
                            "Размеры и местоположение окна сброшены.")

    def _toggle_undo(self) -> None:
        if not BACKUP_FILE.exists():
            messagebox.showinfo(
                "Импорт",
                "Нет резервной копии.\nОтмена доступна только после импорта.")
            return
        if swap_with_backup():
            self._undo_applied = not self._undo_applied
            self.undo_btn.config(
                text="↷ Вернуть последнее импортирование"
                if self._undo_applied
                else "↶ Отменить последнее импортирование"
            )
            if self.on_data_change:
                self.on_data_change()