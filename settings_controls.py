"""Компонент вкладки Settings.

Содержит:
- сброс размеров окна к заводским;
- переключение между import/db.json и import/db.back.json (откат импорта).
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable

from data_manager import BACKUP_FILE, swap_with_backup


class SettingsControls:
    """Компонент настроек."""

    def __init__(self, parent, on_settings_change: Optional[Callable] = None,
                 on_data_change: Optional[Callable] = None):
        self.parent = parent
        self.on_settings_change = on_settings_change
        self.on_data_change = on_data_change
        self._undo_applied = False
        self._create_widgets()

    def _create_widgets(self) -> None:
        tk.Label(self.parent, text="Настройки",
                 font=('Segoe UI', 14, 'bold')).pack(pady=10, anchor='w')

        f = tk.Frame(self.parent)
        f.pack(fill='both', expand=True, padx=10, pady=5)

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

    def _toggle_undo(self) -> None:
        """Меняет местами db.json и db.back.json."""
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