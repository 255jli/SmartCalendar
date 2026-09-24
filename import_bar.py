"""Панель импорта JSON-файлов с выбором через галочки."""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Callable, List, Optional

from import_handler import get_import_files, import_files


class ImportBar:
    """Кнопка импорта + диалог выбора файлов."""

    def __init__(self, parent: ttk.Frame,
                 on_import: Optional[Callable] = None):
        self.parent = parent
        self.on_import = on_import
        self._build()

    def _build(self) -> None:
        frame = tk.Frame(self.parent, bg='#f9f9f9')
        frame.pack(fill='x', pady=(0, 6))

        tk.Button(frame, text="Импортировать JSON",
                  command=self._open_dialog,
                  font=('Segoe UI', 10)).pack(side='left')

        self.status = tk.Label(frame, text="", font=('Segoe UI', 9),
                               fg='#666', bg='#f9f9f9')
        self.status.pack(side='left', padx=8)

    def _open_dialog(self) -> None:
        files = get_import_files()
        if not files:
            messagebox.showinfo(
                "Импорт",
                "JSON-файлы не найдены.\n"
                "Положите .json рядом с exe или в папку import/.")
            return
        dlg = _ImportDialog(self.parent, files)
        self.parent.wait_window(dlg.window)
        if dlg.result:
            self._run_import(dlg.result)

    def _run_import(self, paths: List[Path]) -> None:
        try:
            e, r, errs = import_files(paths)
            self.status.config(text=f"+{e} событий, +{r} повтор.")
            if errs:
                messagebox.showwarning("Импорт", "\n".join(errs[:8]))
        except Exception as ex:
            messagebox.showerror("Импорт", f"Ошибка: {ex}")
        if self.on_import:
            self.on_import()

    def set_status(self, text: str) -> None:
        self.status.config(text=text)


class _ImportDialog:
    """Модальное окно со списком файлов и галочками."""

    def __init__(self, parent: tk.Widget, files: List[Path]):
        self.parent = parent
        self.files = files
        self.result: Optional[List[Path]] = None
        self.vars: List[tuple] = []
        self.window = tk.Toplevel(parent)
        self.window.title("Выбор JSON для импорта")
        self.window.transient(parent.winfo_toplevel())
        self.window.geometry("460x420")
        self._build()
        self.window.grab_set()

    def _build(self) -> None:
        tk.Label(self.window, text="Отметьте файлы для импорта:",
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=10, pady=(10, 4))

        container = tk.Frame(self.window)
        container.pack(fill='both', expand=True, padx=10)
        canvas = tk.Canvas(container, highlightthickness=0)
        sb = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        inner = tk.Frame(canvas)
        inner.bind('<Configure>',
                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        for p in self.files:
            var = tk.BooleanVar(value=True)
            self.vars.append((p, var))
            tk.Checkbutton(inner, text=str(p), variable=var,
                           anchor='w', font=('Segoe UI', 9)).pack(fill='x', anchor='w')

        btns = tk.Frame(self.window)
        btns.pack(fill='x', padx=10, pady=10)
        tk.Button(btns, text="Импортировать выбранные",
                  command=self._ok).pack(side='right')
        tk.Button(btns, text="Отмена",
                  command=self._cancel).pack(side='right', padx=6)
        tk.Button(btns, text="Выбрать все",
                  command=lambda: [v.set(True) for _, v in self.vars]).pack(side='left')
        tk.Button(btns, text="Снять все",
                  command=lambda: [v.set(False) for _, v in self.vars]).pack(side='left', padx=6)

    def _ok(self) -> None:
        selected = [p for p, v in self.vars if v.get()]
        if not selected:
            messagebox.showinfo("Импорт", "Ничего не выбрано.")
            return
        self.result = selected
        self.window.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.window.destroy()