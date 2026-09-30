"""Weekly calendar view with hourly grid."""

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import date, timedelta
import calendar


class CalendarView:
    bg_color = '#ffffff'
    header_bg = '#f0f0f0'
    today_bg = '#e6e6e6'
    weekend_bg = '#f5f5f5'
    line_color = '#d0d0d0'
    text_color = '#333332'
    event_bgs = ['#4a6fa5', '#5b8c5a', '#a06a4a',
                 '#7a5a8c', '#4a8c8c', '#8c6a4a']

    ROW_MIN = 56     # height of one hour, px
    GUTTER = 52      # width of time label column
    DAY_MIN = 88     # minimum day width
    HEADER_H = 44    # height of header with days

    def __init__(self, parent, on_date_select=None, on_month_change=None, on_event_select=None):
        self.parent = parent
        self.on_date_select = on_date_select
        self.on_month_change = on_month_change
        self.on_event_select = on_event_select
        today = date.today()
        # _anchor — «логическая» текущая дата, от которой считается неделя.
        # _anchor_day — предпочтительный день месяца (например, 31),
        # сохраняется между перелистываниями месяцев, чтобы << и >>
        # возвращали ровно в исходное место.
        self._anchor: date = today
        self._anchor_day: int = today.day
        self.curr_week_start = today - timedelta(days=today.weekday())
        self.events: List[Dict[str, Any]] = []

        self._week_start: date = self.curr_week_start
        self._create_widgets()
        self.refresh()

    # ── Widget Construction ───────────────────────────────────────────

    def _create_widgets(self) -> None:
        container = tk.Frame(self.parent, bg=self.bg_color)
        container.pack(fill='both', expand=True, pady=(0, 10))

        nav = tk.Frame(container, bg=self.bg_color)
        nav.pack(fill='x', pady=(0, 8))
        # Двойные стрелки — сдвиг на один календарный месяц.
        tk.Button(nav, text="<<", command=self.prev_month,
                  font=('Segoe UI', 12)).pack(side='left')
        tk.Button(nav, text="◀", command=self._prev_week,
                  font=('Segoe UI', 12)).pack(side='left', padx=(4, 0))
        self.week_label = tk.Label(nav, text="", font=('Segoe UI', 14, 'bold'),
                                   bg=self.bg_color)
        self.week_label.pack(side='left', expand=True)
        tk.Button(nav, text="▶", command=self._next_week,
                  font=('Segoe UI', 12)).pack(side='right', padx=(0, 4))
        tk.Button(nav, text=">>", command=self.next_month,
                  font=('Segoe UI', 12)).pack(side='right')

        cal = tk.Frame(container)
        cal.pack(fill='both', expand=True)
        cal.grid_rowconfigure(1, weight=1)
        cal.grid_columnconfigure(0, weight=1)

        self.header_canvas = tk.Canvas(cal, bg='white', highlightthickness=0,
                                       height=self.HEADER_H)
        self.header_canvas.grid(row=0, column=0, sticky='ew')

        self.canvas = tk.Canvas(cal, bg='white', highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky='nsew')

        vbar = ttk.Scrollbar(cal, orient='vertical', command=self.canvas.yview)
        vbar.grid(row=0, column=1, rowspan=2, sticky='ns')
        self.canvas.configure(yscrollcommand=vbar.set)

        self._bind_mousewheel(self.canvas)
        self.canvas.bind('<Configure>', lambda e: self._redraw())
        self.header_canvas.bind('<Configure>', lambda e: self._redraw())

    def _bind_mousewheel(self, widget: tk.Widget) -> None:
        widget.bind('<MouseWheel>', self._on_mousewheel)   # Windows / macOS
        widget.bind('<Button-4>', self._on_mousewheel)     # Linux, scroll up
        widget.bind('<Button-5>', self._on_mousewheel)     # Linux, scroll down

    def _on_mousewheel(self, event) -> None:
        num = getattr(event, 'num', None)
        if num == 4:
            delta = -1
        elif num == 5:
            delta = 1
        else:
            delta = -int(event.delta / 120)
        self.canvas.yview_scroll(delta, 'units')

    # ── Navigation ─────────────────────────────────────────────────────

    def _set_anchor(self, d: date, remember_day: bool = True) -> None:
        """Обновляет опорную дату и пересчитывает начало недели.

        remember_day=True фиксирует день месяца как «предпочтительный»
        для последующей навигации по месяцам.
        """
        self._anchor = d
        if remember_day:
            self._anchor_day = d.day
        self.curr_week_start = d - timedelta(days=d.weekday())

    def _prev_week(self) -> None:
        self._set_anchor(self._anchor - timedelta(days=7))
        self.refresh()
        if self.on_month_change:
            self.on_month_change()

    def _next_week(self) -> None:
        self._set_anchor(self._anchor + timedelta(days=7))
        self.refresh()
        if self.on_month_change:
            self.on_month_change()

    def _shift_month(self, delta: int) -> None:
        """Сдвиг ровно на один календарный месяц.

        Предпочтительный день месяца сохраняется. Если в целевом месяце
        такого дня нет, берётся последний день, но предпочтение остаётся —
        обратный переход вернёт исходный день.
        """
        m = self._anchor.month + delta
        y = self._anchor.year + (m - 1) // 12
        m = (m - 1) % 12 + 1
        day = min(self._anchor_day, calendar.monthrange(y, m)[1])
        self._set_anchor(date(y, m, day), remember_day=False)
        self.refresh()
        if self.on_month_change:
            self.on_month_change()

    def prev_month(self):
        self._shift_month(-1)

    def next_month(self):
        self._shift_month(+1)

    def reset_to_today(self) -> None:
        """Возвращает вид на текущую неделю."""
        self._set_anchor(date.today())
        self.refresh()
        if self.on_month_change:
            self.on_month_change()

    def _week_range(self) -> Tuple[date, date]:
        """Границы видимой недели (понедельник — воскресенье)."""
        return self.curr_week_start, self.curr_week_start + timedelta(days=6)

    # ── Public API ─────────────────────────────────────────────────────

    def refresh(self, events: Optional[List[Dict[str, Any]]] = None) -> None:
        if events is not None:
            self.events = events
        self._week_start = self.curr_week_start

        start, end = self._week_range()
        self.week_label.config(
            text=f"{start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}")
        self._redraw()

    def bind_date_select(self, callback):
        self.on_date_select = callback

    # ── Rendering ──────────────────────────────────────────────────────

    def _day_width(self, total_w: int) -> float:
        avail = max(total_w - self.GUTTER, 0)
        return max(self.DAY_MIN, avail / 7.0)

    def _redraw(self) -> None:
        self._draw_header()
        self._draw_grid()

    def _draw_header(self) -> None:
        c = self.header_canvas
        c.delete('all')
        W = c.winfo_width()
        if W <= 1:
            return
        day_w = self._day_width(W)
        total_w = self.GUTTER + day_w * 7
        c.configure(scrollregion=(0, 0, total_w, self.HEADER_H))

        c.create_rectangle(0, 0, self.GUTTER, self.HEADER_H,
                           fill=self.header_bg, outline=self.line_color)

        for i in range(7):
            d = self._week_start + timedelta(days=i)
            x0 = self.GUTTER + i * day_w
            bg = self.bg_color
            if d.weekday() >= 5:
                bg = self.weekend_bg
            if d == date.today():
                bg = self.today_bg
            c.create_rectangle(x0, 0, x0 + day_w, self.HEADER_H,
                               fill=bg, outline=self.line_color)
            c.create_text(x0 + day_w / 2, 14,
                          text=calendar.day_abbr[d.weekday()].upper(),
                          font=('Segoe UI', 10, 'bold'), fill=self.text_color)
            c.create_text(x0 + day_w / 2, 30, text=str(d.day),
                          font=('Segoe UI', 14, 'bold'), fill=self.text_color)

    def _draw_grid(self) -> None:
        c = self.canvas
        c.delete('all')
        W = c.winfo_width()
        H = 24 * self.ROW_MIN
        if W <= 1:
            return
        day_w = self._day_width(W)
        total_w = self.GUTTER + day_w * 7
        c.configure(scrollregion=(0, 0, total_w, H))

        # Background for weekends and "today" (under lines)
        for i in range(7):
            d = self._week_start + timedelta(days=i)
            bg = None
            if d == date.today():
                bg = self.today_bg
            elif d.weekday() >= 5:
                bg = self.weekend_bg
            if bg:
                x0 = self.GUTTER + i * day_w
                c.create_rectangle(x0, 0, x0 + day_w, H,
                                   fill=bg, outline='', tags=('bg',))
        c.tag_lower('bg')

        # Horizontal lines
        for h in range(25):
            y = h * self.ROW_MIN
            c.create_line(0, y, total_w, y, fill=self.line_color)

        # Hour labels
        for h in range(24):
            y = h * self.ROW_MIN + 4
            c.create_text(self.GUTTER - 6, y, text=f"{h:02d}:00",
                          anchor='ne', font=('Segoe UI', 9), fill='#888')

        # Vertical lines
        for i in range(8):
            x = self.GUTTER + i * day_w
            c.create_line(x, 0, x, H, fill=self.line_color)

        # Events
        for idx, (ev, col, ncols) in enumerate(self._layout_events(self.events)):
            self._draw_event(c, idx, ev, col, ncols, day_w)

    def _draw_event(self, canvas: tk.Canvas, idx: int,
                    ev: Dict[str, Any], col: int, ncols: int,
                    day_w: float) -> None:
        d = ev['_day_idx']
        slot_w = day_w / ncols
        x0 = self.GUTTER + d * day_w + col * slot_w + 2
        x1 = x0 + slot_w - 4
        y0 = ev['_start_min'] * (self.ROW_MIN / 60.0) + 2
        y1 = ev['_end_min'] * (self.ROW_MIN / 60.0) - 2
        if y1 - y0 < 14:
            y1 = y0 + 14

        key = ev.get('id') or ev.get('title', '')
        color = self.event_bgs[sum(ord(ch) for ch in key) % len(self.event_bgs)]
        tag = f'ev_{idx}'

        canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline='',
                                tags=('event', tag))
        title = ev.get('title', '')
        if len(title) > 40:
            title = title[:38] + '…'
        canvas.create_text(x0 + 5, y0 + 4, text=title, anchor='nw',
                           fill='white', font=('Segoe UI', 9, 'bold'),
                           width=max(int(x1 - x0 - 10), 20),
                           tags=('event', tag))
        canvas.tag_bind(tag, '<Button-1>',
                        lambda e, x=ev: self._select_event(x))

    # ── Event Layout Algorithm (Intersection Algorithm) ──────────────────────

    @staticmethod
    def _time_to_min(t: str) -> int:
        try:
            h, m = str(t).split(':')
            return int(h) * 60 + int(m)
        except Exception:
            return 0

    def _layout_events(self, events):
        """Groups transitively intersecting events and arranges them in columns."""
        by_day: Dict[int, List[Dict[str, Any]]] = {}
        for raw in self.events:
            try:
                d = date.fromisoformat(raw['date'])
            except Exception:
                continue
            day_idx = (d - self._week_start).days
            if not 0 <= day_idx <= 6:
                continue
            start_min = self._time_to_min(raw.get('start', '00:00'))
            dur = int(raw.get('duration', 60) or 60)
            end_min = min(start_min + max(dur, 15), 24 * 60)
            ev = dict(raw)
            ev['_day_idx'] = day_idx
            ev['_start_min'] = start_min
            ev['_end_min'] = end_min
            by_day.setdefault(day_idx, []).append(ev)

        result: List[Tuple[Dict[str, Any], int, int]] = []
        for day_events in by_day.values():
            result.extend(self._layout_day(day_events))
        return result

    @classmethod
    def _layout_day(cls, events: List[Dict[str, Any]]
                    ) -> List[Tuple[Dict[str, Any], int, int]]:
        """Группирует транзитивно пересекающиеся события и разводит их по колонкам."""
        events = sorted(events, key=lambda e: (e['_start_min'], -e['_end_min']))
        out: List[Tuple[Dict[str, Any], int, int]] = []
        group: List[Dict[str, Any]] = []
        group_end = -1
        for ev in events:
            if group and ev['_start_min'] >= group_end:
                out.extend(cls._assign_columns(group))
                group, group_end = [], -1
            group.append(ev)
            group_end = max(group_end, ev['_end_min'])
        if group:
            out.extend(cls._assign_columns(group))
        return out

    @staticmethod
    def _assign_columns(group: List[Dict[str, Any]]
                        ) -> List[Tuple[Dict[str, Any], int, int]]:
        columns: List[int] = []  # end_min for each column
        assigned: List[Tuple[Dict[str, Any], int]] = []
        for ev in group:
            for i, end in enumerate(columns):
                if end <= ev['_start_min']:
                    columns[i] = ev['_end_min']
                    assigned.append((ev, i))
                    break
            else:
                columns.append(ev['_end_min'])
                assigned.append((ev, len(columns) - 1))
        n = max(len(columns), 1)
        return [(ev, i, n) for ev, i in assigned]

    # ── Callback ──────────────────────────────────────────────────────

    def _select_event(self, event: Dict[str, Any]) -> None:
        if not self.on_event_select:
            return
        clean = {k: v for k, v in event.items() if not k.startswith('_')}
        self.on_event_select(clean)

    def on_date_click(self, day):
        if not self.on_date_select:
            return
        self.on_date_select(day)
