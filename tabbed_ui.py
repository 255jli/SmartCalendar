import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Callable

class TabbedUI:
    """Компонент вкладок для настроек и событий."""
    
    def __init__(self, parent: ttk.Frame, events: List[Dict[str, Any]] = None,
                 on_select_event: Optional[Callable] = None,
                 on_settings_change: Optional[Callable] = None,
                 on_event_action: Optional[Callable] = None,
                 on_data_change: Optional[Callable] = None):
        """Инициализирует вкладки.
        
        Args:
            parent: Родительский виджет
            events: Список событий для отображения
            on_select_event: Функция обратного вызова при выборе события
            on_settings_change: Функция обратного вызова при изменении настроек
            on_event_action: Функция обратного вызова при действии над событием (complete, edit, delete)
            on_data_change: Функция обратного вызова при изменении данных (например, откат импорта)
        """
        self.parent = parent
        self.events = events or []
        self.filtered_events = self.events[:]  # Копия событий для фильтрации
        self.selected_event = None
        self.on_select_event = on_select_event
        self.on_settings_change = on_settings_change
        self.on_event_action = on_event_action
        self.on_data_change = on_data_change
        
        self._create_widgets()
        
    def _create_widgets(self) -> None:
        """Создает компоненты интерфейса."""
        # Initialize Notebook (tabs)
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self.events_tab = ttk.Frame(self.notebook)
        self.todo_tab = ttk.Frame(self.notebook)  # Новая вкладка задач
        self.details_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.events_tab, text='События')
        self.notebook.add(self.todo_tab, text='Задачи')  # Добавляем вкладку задач
        self.notebook.add(self.details_tab, text='Детали')
        self.notebook.add(self.settings_tab, text='Настройки')
        
        # Configure events tab content
        self._setup_events_tab()
        
        # Configure tasks tab content
        self._setup_todo_tab()
        
        # Configure details tab content
        self._setup_details_tab()
        
        # Configure settings tab content
        self._setup_settings_tab()
    
    def _setup_events_tab(self) -> None:
        """Настраивает вкладку событий."""
        # Create search frame
        search_frame = tk.Frame(self.events_tab)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        # Add search field
        tk.Label(search_frame, text="Поиск событий:", font=('Segoe UI', 10)).pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._filter_events)  # Обновляем при изменении
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Segoe UI', 10))
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        # Add event feed component to events tab
        from event_feed import EventFeed
        self.event_feed = EventFeed(self.events_tab, on_item_click=self._on_event_action)
        self.event_feed.update_events(self.filtered_events)
    
    def _setup_todo_tab(self) -> None:
        """Настраивает вкладку задач."""
        # Create search frame
        search_frame = tk.Frame(self.todo_tab)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        # Add search field
        tk.Label(search_frame, text="Поиск задач:", font=('Segoe UI', 10)).pack(side='left')
        self.todo_search_var = tk.StringVar()
        self.todo_search_var.trace('w', self._filter_todos)  # Обновляем при изменении
        search_entry = tk.Entry(search_frame, textvariable=self.todo_search_var, font=('Segoe UI', 10))
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        # Create tasks list frame
        todo_list_frame = tk.Frame(self.todo_tab)
        todo_list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create tasks list
        self.todo_listbox = tk.Listbox(todo_list_frame, font=('Segoe UI', 10))
        
        # Add scrollbar
        todo_scrollbar = ttk.Scrollbar(todo_list_frame, orient='vertical', command=self.todo_listbox.yview)
        self.todo_listbox.configure(yscrollcommand=todo_scrollbar.set)
        
        self.todo_listbox.pack(side='left', fill='both', expand=True)
        todo_scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to task view
        self.todo_listbox.bind('<Double-Button-1>', self._on_todo_double_click)
        
        # Populate tasks list
        self._refresh_todo_list()
    
    def _setup_details_tab(self) -> None:
        """Настраивает вкладку деталей."""
        # Create scrollable frame for event details
        detail_canvas = tk.Canvas(self.details_tab, bg='white')
        scrollbar = ttk.Scrollbar(self.details_tab, orient='vertical', command=detail_canvas.yview)
        scrollable_frame = tk.Frame(detail_canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: detail_canvas.configure(scrollregion=detail_canvas.bbox("all"))
        )
        
        detail_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        detail_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add label to display "Select an event"
        self.detail_label = tk.Label(
            scrollable_frame,
            text="Выберите событие в календаре или на вкладке 'События'\n\nДля просмотра деталей",
            font=('Segoe UI', 12),
            fg='#888888',
            bg='white',
            justify='center'
        )
        self.detail_label.pack(expand=True, fill='both', padx=20, pady=50)
        
        detail_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            detail_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        detail_canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
    
    def _setup_settings_tab(self) -> None:
        """Настраивает вкладку настроек."""
        # Add settings component to settings tab
        from settings_controls import SettingsControls
        self.settings_controls = SettingsControls(
            self.settings_tab,
            on_settings_change=self.on_settings_change,
            on_data_change=self.on_data_change,
        )
    
    def _on_event_action(self, action: str, event: Dict[str, Any]) -> None:
        """Обрабатывает действия с событием."""
        if action in ("complete", "edit", "delete"):
            if self.on_event_action:
                self.on_event_action(action, event)
        else:
            if self.on_select_event:
                self.on_select_event(event)
            self.show_event_details(event)
    
    def show_event_details(self, event: Dict[str, Any]) -> None:
        """Показывает детали события на вкладке деталей.
        
        Args:
            event: Событие для отображения деталей
        """
        self.selected_event = event
        
        # Clear details tab content
        for widget in self.details_tab.winfo_children():
            widget.destroy()
        
        # Create scrollable frame for event details
        detail_canvas = tk.Canvas(self.details_tab, bg='white')
        scrollbar = ttk.Scrollbar(self.details_tab, orient='vertical', command=detail_canvas.yview)
        scrollable_frame = tk.Frame(detail_canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: detail_canvas.configure(scrollregion=detail_canvas.bbox("all"))
        )
        
        detail_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        detail_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add event information
        # Title
        title_label = tk.Label(
            scrollable_frame,
            text=event['title'],
            font=('Segoe UI', 14, 'bold'),
            fg='#222222',
            bg='white',
            anchor='w'
        )
        title_label.pack(fill='x', padx=20, pady=(20, 10))
        
        # Date and time
        time_frame = tk.Frame(scrollable_frame, bg='white')
        time_frame.pack(fill='x', padx=20, pady=5)
        
        tk.Label(time_frame, text="Дата:", font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w')
        tk.Label(time_frame, text=event['date'], font=('Segoe UI', 10), bg='white').pack(anchor='w')
        
        tk.Label(time_frame, text="Время начала:", font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w', pady=(10, 0))
        tk.Label(time_frame, text=event['start'], font=('Segoe UI', 10), bg='white').pack(anchor='w')
        
        tk.Label(time_frame, text="Продолжительность:", font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w', pady=(10, 0))
        tk.Label(time_frame, text=f"{event.get('duration', 0)} мин", font=('Segoe UI', 10), bg='white').pack(anchor='w')
        
        # Категория
        tk.Label(time_frame, text="Категория:", font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w', pady=(10, 0))
        tk.Label(time_frame, text=event.get('category', 'Не указана'), font=('Segoe UI', 10), bg='white').pack(anchor='w')
        
        # Статус
        tk.Label(time_frame, text="Статус:", font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w', pady=(10, 0))
        status_text = event.get('status', 'pending')
        status_colors = {
            'pending': '#4a90d9',
            'done': '#6aa84f',
            'missed': '#d93838'
        }
        status_color = status_colors.get(status_text, '#4a90d9')
        status_label = tk.Label(
            time_frame,
            text=status_text.upper(),
            font=('Segoe UI', 10, 'bold'),
            bg='white',
            fg=status_color
        )
        status_label.pack(anchor='w')
        
        # Описание (если есть)
        if event.get('description'):
            desc_frame = tk.Frame(scrollable_frame, bg='white')
            desc_frame.pack(fill='x', padx=20, pady=(20, 5))
            
            tk.Label(desc_frame, text="Описание:", font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w')
            desc_text = tk.Text(
                desc_frame,
                height=min(len(event['description'].split('\n')), 5),
                wrap='word',
                font=('Segoe UI', 10),
                bg='#f9f9f9',
                relief='solid',
                borderwidth=1
            )
            desc_text.insert('1.0', event['description'])
            desc_text.config(state='disabled')
            desc_text.pack(fill='x', pady=5)
        
        # Дополнительные поля (если есть)
        extra_fields = []
        for key, value in event.items():
            if key not in ['id', 'title', 'date', 'start', 'duration', 'category', 'status', 'description']:
                extra_fields.append((key, str(value)))
        
        if extra_fields:
            extra_frame = tk.Frame(scrollable_frame, bg='white')
            extra_frame.pack(fill='x', padx=20, pady=(20, 5))
            
            tk.Label(extra_frame, text="Дополнительно:", font=('Segoe UI', 10, 'bold'), bg='white').pack(anchor='w')
            
            for key, value in extra_fields:
                field_frame = tk.Frame(extra_frame, bg='white')
                field_frame.pack(fill='x', pady=2)
                
                tk.Label(field_frame, text=f"{key}:", font=('Segoe UI', 9), bg='white').pack(side='left')
                tk.Label(field_frame, text=value, font=('Segoe UI', 9), bg='white', fg='#666666').pack(side='right')
        
        detail_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Привязываем колесо мыши к канвасу
        def _on_mousewheel(event):
            detail_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        detail_canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
    
    def _filter_todos(self, *args):
        """Фильтрует задачи по поисковому запросу."""
        # Перезагружаем список задач с учетом фильтра
        self._refresh_todo_list()
    
    def _refresh_todo_list(self):
        """Обновляет список задач."""
        # Очищаем текущий список
        self.todo_listbox.delete(0, tk.END)
        
        # Получаем задачи (события с категорией 'task')
        query = self.todo_search_var.get().lower()
        for event in self.events:
            if event.get('category') == 'task' and (not query or query in event['title'].lower()):
                status = '✓' if event.get('status') == 'done' else '○'
                self.todo_listbox.insert(tk.END, f"{status} {event['title']}")
    
    def _on_todo_double_click(self, event):
        """Обработка двойного клика по задаче."""
        selection = self.todo_listbox.curselection()
        if selection:
            index = selection[0]
            # Получаем соответствующее событие
            filtered_tasks = [e for e in self.events if e.get('category') == 'task']
            query = self.todo_search_var.get().lower()
            if query:
                filtered_tasks = [e for e in filtered_tasks if query in e['title'].lower()]
            
            if index < len(filtered_tasks):
                task = filtered_tasks[index]
                # Вызываем обработчик выбора события
                if self.on_select_event:
                    self.on_select_event(task)
    
    def _filter_events(self, *args):
        """Фильтрует события по поисковому запросу."""
        query = self.search_var.get().lower()
        if not query:
            self.filtered_events = self.events[:]
        else:
            self.filtered_events = [
                event for event in self.events
                if query in event['title'].lower() or 
                   query in event.get('description', '').lower() or
                   query in event['date'] or
                   query in event.get('category', '').lower()
            ]
        
        # Обновляем отображение событий
        if hasattr(self, 'event_feed'):
            self.event_feed.update_events(self.filtered_events)
    
    def update_events(self, events: List[Dict[str, Any]]) -> None:
        """Обновляет список событий на вкладке событий.
        
        Args:
            events: Список событий для обновления
        """
        self.events = events
        self._filter_events()  # Применяем фильтр к новым событиям
        self._refresh_todo_list()  # Обновляем список задач