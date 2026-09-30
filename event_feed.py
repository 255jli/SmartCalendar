import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, date

class EventFeed:
    """Компонент ленты событий."""
    
    BG = '#f9f9f9'
    CARD_BG = '#ffffff'
    TEXT = '#222222'
    PENDING = '#4a90d9'
    DONE = '#6aa84f'
    MISSED = '#d93838'
    BORDER = '#e0e0e0'

    def __init__(self, parent: ttk.Frame, on_item_click: Optional[Callable] = None):
        """Инициализирует ленту событий.
        
        Args:
            parent: Родительский виджет
            on_item_click: Функция обратного вызова при клике на элемент
        """
        self.parent = parent
        self.on_item_click = on_item_click
        
        self._create_widgets()
        
    def _create_widgets(self) -> None:
        """Creates UI components."""
        # Create container for scrolling
        container = tk.Frame(self.parent, bg=self.BG)
        container.pack(fill='both', expand=True)
        
        # Canvas for scrollable area
        canvas = tk.Canvas(container, bg=self.BG, highlightthickness=0)
        
        # Vertical scrollbar
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        
        # Content frame
        self.feed_frame = tk.Frame(canvas, bg=self.BG)
        self.feed_frame.bind('<Configure>',
                             lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        
        # Save window id and create window without fixed width
        self._win = canvas.create_window((0, 0), window=self.feed_frame, anchor='nw')
        
        # Add canvas resize handler
        def _on_canvas_resize(event):
            canvas.itemconfigure(self._win, width=event.width)
        canvas.bind('<Configure>', _on_canvas_resize)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Прокрутка колесом: Windows/macOS — MouseWheel, Linux — Button-4/5.
        def _on_mousewheel(event):
            num = getattr(event, 'num', None)
            if num == 4:
                delta = -1
            elif num == 5:
                delta = 1
            else:
                delta = -int(event.delta / 120)
            canvas.yview_scroll(delta, "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel)
        canvas.bind("<Button-5>", _on_mousewheel)
        
        canvas.pack(side='left', fill='both', expand=True)

    def update_events(self, events: List[Dict[str, Any]]) -> None:
        """Обновляет список событий.
        
        Args:
            events: Список событий для отображения
        """
        # Clear current content
        for w in self.feed_frame.winfo_children():
            w.destroy()

        if not events:
            lbl = tk.Label(self.feed_frame, text="Нет предстоящих дел",
                           bg=self.BG, fg='#888', font=('Segoe UI', 13))
            lbl.pack(pady=20)
            return

        # Display events
        for event in events:
            self._create_event_item(event)

    def _create_event_item(self, event: Dict[str, Any]) -> None:
        """Создает элемент интерфейса для события.
        
        Args:
            event: Событие для отображения
        """
        frame = tk.Frame(self.feed_frame, bg=self.CARD_BG,
                         relief='solid', borderwidth=1,
                         highlightbackground=self.BORDER,
                         highlightthickness=1)
        frame.pack(fill='x', pady=2, padx=2, ipadx=2, ipady=2)

        # Main event content
        content = tk.Frame(frame, bg=self.CARD_BG)
        content.pack(side='left', fill='x', expand=True, padx=8, pady=6)

        title = event['title'] + (" (пропущено)" if event['status'] == 'missed' else "")
        tk.Label(content, text=title, font=('Segoe UI', 11, 'bold'),
                 bg=self.CARD_BG, fg=self.TEXT, anchor='w').pack(anchor='w', pady=(0, 4))

        # Метаинформация о событии
        meta = f"{event['date']} {event['start']} · {event['duration']} мин · {event['category']}"
        if event.get('description'):
            meta += f"\n{event['description']}"
        
        tk.Label(content, text=meta, font=('Segoe UI', 9), fg='#666',
                 bg=self.CARD_BG, wraplength=380, justify='left').pack(anchor='w')

        # Кнопки действий (редактировать, удалить, завершить)
        btns_frame = tk.Frame(frame, bg=self.CARD_BG)
        btns_frame.pack(side='right', padx=4, pady=4)

        # Кнопки всегда видны, чтобы пользователь мог легко взаимодействовать с событием
        if event['status'] in ('pending','missed'):
            tk.Button(btns_frame, text="✓", font=('Segoe UI', 10, 'bold'),
                      bg=self.DONE, fg='white', borderwidth=0,
                      width=3, height=1,
                      command=lambda: self._handle_complete(event)).pack(side='top', pady=1)
        
        tk.Button(btns_frame, text="✎", font=('Segoe UI', 10, 'bold'),
                  bg='#e8e8e8', borderwidth=0, width=3, height=1,
                  command=lambda: self._handle_edit(event)).pack(side='top', pady=1)
        
        tk.Button(btns_frame, text="×", font=('Segoe UI', 10, 'bold'),
                  bg='#f0f0f0', borderwidth=0, width=3, height=1,
                  command=lambda: self._handle_delete(event)).pack(side='top', pady=1)

    def _handle_complete(self, event: Dict[str, Any]) -> None:
        """Обрабатывает завершение события.
        
        Args:
            event: Событие для завершения
        """
        if self.on_item_click:
            self.on_item_click('complete', event)

    def _handle_edit(self, event: Dict[str, Any]) -> None:
        """Обрабатывает редактирование события.
        
        Args:
            event: Событие для редактирования
        """
        if self.on_item_click:
            self.on_item_click('edit', event)

    def _handle_delete(self, event: Dict[str, Any]) -> None:
        """Обрабатывает удаление события.
        
        Args:
            event: Событие для удаления
        """
        if self.on_item_click:
            self.on_item_click('delete', event)