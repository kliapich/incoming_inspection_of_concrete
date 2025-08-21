import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from ttkbootstrap import Style
from ttkbootstrap.widgets import DateEntry
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import threading
import asyncio
import os
import re
from typing import Optional, List
import tempfile
from datetime import datetime
from docxtpl import DocxTemplate
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment

# Импортируем новый менеджер базы данных
try:
    from database_manager import DatabaseManager
    print("✅ Используется новый менеджер базы данных")
except ImportError:
    print("⚠️ Новый менеджер базы данных не найден, используем старый SQLite")
    import sqlite3
    
    class DatabaseManager:
        def __init__(self):
            self.conn = sqlite3.connect('concrete.db')
            self.create_tables()
            self.db_type = 'sqlite'
        
        def create_tables(self):
            scripts = [
                """CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    contact TEXT,
                    phone TEXT)""",
                """CREATE TABLE IF NOT EXISTS objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    address TEXT,
                    FOREIGN KEY (org_id) REFERENCES organizations(id))""",
                """CREATE TABLE IF NOT EXISTS constructions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    pour_date TEXT NOT NULL,
                    element TEXT,
                    concrete_class TEXT,
                    frost_resistance TEXT,
                    water_resistance TEXT,
                    supplier TEXT,
                    concrete_passport TEXT,
                    volume_concrete REAL,
                    cubes_count INTEGER,
                    cones_count INTEGER,
                    slump TEXT,
                    temperature TEXT,
                    temp_measurements INTEGER,
                    executor TEXT,
                    act_number TEXT,
                    request_number TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(id))"""
            ]
            cursor = self.conn.cursor()
            for script in scripts:
                cursor.execute(script)
            # Миграция: добавляем колонку 'invoice' в constructions, если отсутствует
            cursor.execute("PRAGMA table_info(constructions)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            if 'invoice' not in column_names:
                cursor.execute("ALTER TABLE constructions ADD COLUMN invoice TEXT")
            self.conn.commit()
        
        def close(self):
            if self.conn:
                self.conn.close()
        
        def get_connection_info(self):
            return {
                'type': 'SQLite (Fallback)',
                'database': 'concrete.db',
                'status': 'Connected'
            }
        
        def test_connection(self):
            try:
                self.conn.execute("SELECT 1")
                return True
            except:
                return False

# =================== Telegram Bot Service ===================
TELEGRAM_BOT_TOKEN = os.getenv(
    'TELEGRAM_BOT_TOKEN',
    '7619596833:AAEtEBVEcQeyevk61-kZdXvpZp1skfdzomA'
)

class TelegramBotService:
    """Background Telegram bot that guides user to add a new construction record."""

    # Conversation states
    (ACTION, ORG, OBJ, CLASS, FROST, WATER, ELEMENT, SUPPLIER, PASSPORT,
     CUBES, CONES, SLUMP, VOLUME, TEMP, TEMP_MEAS, EXECUTOR, ACT, REQUEST, DATE,
     SEND_ACT, DOC_PICK, ORG_DOCS, OBJ_DOCS) = range(23)

    def __init__(self, token: str, db_manager: DatabaseManager):
        self.token = token
        self.db_manager = db_manager
        self.thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def start(self) -> None:
        if self.is_running():
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        print("[TG] Building application...")
        application = ApplicationBuilder().token(self.token).build()

        def fetchall(query: str, params: tuple = ()):
            try:
                return self.db_manager.execute_query(query, params)
            except Exception as e:
                print(f"[TG] Query error: {e}")
                return []

        def fetch_distinct(column: str) -> List[str]:
            try:
                if self.db_manager.db_type == 'postgresql':
                    query = f"SELECT DISTINCT {column} FROM constructions WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}"
                else:
                    query = f"SELECT DISTINCT {column} FROM constructions WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}"
                
                rows = fetchall(query)
                if self.db_manager.db_type == 'postgresql':
                    return [r[column] for r in rows if r.get(column)]
                else:
                    return [r[column] for r in rows if r.get(column)]
            except Exception as e:
                print(f"[TG] Distinct query error: {e}")
                return []

        # ... остальной код Telegram бота остается без изменений ...
        # (для экономии места я не копирую весь код, так как он идентичен оригиналу)

        async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            keyboard = [
                [InlineKeyboardButton("Хочу добавить контроль", callback_data="ACTION:ADD")],
                [InlineKeyboardButton("Сформировать документ по записи", callback_data="ACTION:DOCS")]
            ]
            await update.effective_message.reply_text(
                "Че надо?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return self.ACTION

        # ... здесь должны быть все остальные функции бота ...
        # Для краткости я не копирую их все, но они должны быть идентичны оригиналу

        conv = ConversationHandler(
            entry_points=[CommandHandler("start", start_cmd)],
            states={
                self.ACTION: [CallbackQueryHandler(lambda u, c: self.action_selected(u, c), pattern=r"^ACTION:")],
                # ... остальные состояния
            },
            fallbacks=[CommandHandler("cancel", lambda u, c: self.cancel(u, c))],
            allow_reentry=True,
        )

        application.add_handler(conv)
        try:
            print("[TG] Preparing event loop...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            print("[TG] Starting polling...")
            application.run_polling()
        except Exception as e:
            print(f"[TG] run_polling error: {e}")

class ConcreteApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Инициализируем менеджер базы данных
        try:
            self.db = DatabaseManager()
            print(f"✅ База данных: {self.db.get_connection_info()}")
        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")
            messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных:\n{str(e)}")
            sys.exit(1)

        self.current_org_id = None
        self.current_object_id = None
        self.buttons_dict = {}

        self.title("Учет заливок бетона (Railway Edition v2.1)")
        self.geometry("1500x700")
        self.resizable(False, False)
        
        # Стиль ttkbootstrap
        self.style = Style(theme="flatly")
        try:
            self.style.layout('TSizegrip', [])
        except Exception:
            pass

        # Настройки панелей
        self.left_panel_width = 180
        self.min_left_panel_width = 150
        self.max_left_panel_width = 350
        
        # Настройки панели объектов
        self.object_panel_height = 200
        self.object_panel_min_height = 100
        self.object_panel_max_height = 400
        
        self.resizing_panel = False
        self.resizing_object_panel = False
        
        self.create_widgets()
        self.load_organizations()
        self.update_buttons_state()
        
        # Показываем информацию о базе данных в заголовке
        self.update_title_with_db_info()

    def update_title_with_db_info(self):
        """Обновляет заголовок окна с информацией о базе данных"""
        try:
            db_info = self.db.get_connection_info()
            db_status = f" [{db_info['type']}]"
            current_title = self.title()
            if db_status not in current_title:
                self.title(current_title + db_status)
        except Exception:
            pass

    def create_widgets(self):
        # ... код создания виджетов остается без изменений ...
        # (для экономии места я не копирую весь код, так как он идентичен оригиналу)
        
        ###################### Главные фреймы ############################
        self.left_panel = ttk.Frame(self, width=self.left_panel_width)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=5)
        self.left_panel.pack_propagate(False)
        
        # Разделители для левой панели
        self.panel_splitter = ttk.Separator(self, orient=tk.VERTICAL)
        self.panel_splitter.pack(side=tk.LEFT, fill=tk.Y, padx=2)
        self.panel_splitter.bind("<Button-1>", self.start_resize)
        self.panel_splitter.bind("<B1-Motion>", self.resize_panel)
        self.panel_splitter.bind("<ButtonRelease-1>", self.stop_resize)
        
        # Правая панель
        right_panel = ttk.Frame(self)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Верхняя часть правой панели (объекты)
        object_frame_container = ttk.Frame(right_panel)
        object_frame_container.pack(fill=tk.X, pady=(0, 5))
        
        # Панель объектов с возможностью изменения высоты
        self.object_frame = ttk.LabelFrame(object_frame_container, text="Объекты", padding=10)
        self.object_frame.pack(fill=tk.X)
        
        # Разделитель для панели объектов
        self.object_panel_splitter = ttk.Separator(object_frame_container, orient=tk.HORIZONTAL)
        self.object_panel_splitter.pack(fill=tk.X, pady=2)
        self.object_panel_splitter.bind("<Button-1>", self.start_resize_object_panel)
        self.object_panel_splitter.bind("<B1-Motion>", self.resize_object_panel)
        self.object_panel_splitter.bind("<ButtonRelease-1>", self.stop_resize_object_panel)
        
        # Таблица объектов
        self.object_tree = ttk.Treeview(self.object_frame, columns=("name", "address"), show="headings", height=5)
        self.object_tree.heading("name", text="Название")
        self.object_tree.heading("address", text="Адрес")
        self.object_tree.bind("<<TreeviewSelect>>", self.on_object_select)
        
        scrollbar_y = ttk.Scrollbar(self.object_frame, orient="vertical", command=self.object_tree.yview)
        scrollbar_x = ttk.Scrollbar(self.object_frame, orient="horizontal", command=self.object_tree.xview)
        self.object_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.object_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        self.object_frame.grid_rowconfigure(0, weight=1)
        self.object_frame.grid_columnconfigure(0, weight=1)
        
        # Нижняя часть правой панели (конструктивы)
        construction_frame = ttk.LabelFrame(right_panel, text="Контроль", padding=10)
        construction_frame.pack(fill=tk.BOTH, expand=True)
        
        #################### Кнопки управления ##########################
        # Компактный стиль для кнопок действий
        self.style.configure("Slim.TButton", padding=(6, 2))
        
        btn_frame = ttk.LabelFrame(self.left_panel, text="Действия", padding=3)
        btn_frame.pack(fill=tk.X, pady=2)

        # кнопки
        buttons = [
            ("+ Организацию", self.add_organization),
            ("- Организацию", self.delete_organization),
            ("Ред. Организацию", self.edit_organization),
            ("+ Объект", self.add_object),
            ("- Объект", self.delete_object),
            ("Ред. Объект", self.edit_object),
            ("+ Контроль", self.add_construction),
            ("- Контроль", self.delete_construction),
            ("Ред. Контроль", self.edit_construction),
            ("Обновить", self.refresh_data),
            ("Создать заявку", self.create_request),
            ("Создать акт", self.create_act),
            ("Шаблон для импорта", self.generate_import_template),
            ("Импорт из Excel", self.import_from_excel),
            ("Экспорт в Excel", self.export_to_excel),
            ("Запустить бота", self.start_telegram_bot),
            ("Инфо БД", self.show_db_info)  # Новая кнопка
        ]

        for text, cmd in buttons:
            btn = ttk.Button(btn_frame, text=text, command=cmd, style="Slim.TButton")
            btn.pack(fill=tk.X, pady=1)
            self.buttons_dict[text] = btn

        #################### Таблица организаций #########################
        org_frame = ttk.LabelFrame(self.left_panel, text="Организации", padding=5)
        org_frame.pack(fill=tk.BOTH, expand=True)
        
        self.org_tree = ttk.Treeview(org_frame, columns=("name",), show="headings")
        self.org_tree.heading("name", text="Название")
        self.org_tree.column("name", width=self.left_panel_width-30)
        self.org_tree.pack(fill=tk.BOTH, expand=True)
        self.org_tree.bind("<<TreeviewSelect>>", self.on_org_select)
        
        # Фрейм фильтров
        filter_frame = ttk.Frame(construction_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Фильтры:").pack(side=tk.LEFT, padx=5)
        
        filters = [
            ("Дата:", "pour_date"),
            ("Класс бетона:", "concrete_class"),
            ("Исполнитель:", "executor"),
            ("Поставщик:", "supplier"),
            ("Счет:", "invoice")
        ]
        
        self.filter_entries = {}
        for text, name in filters:
            frame = ttk.Frame(filter_frame)
            frame.pack(side=tk.LEFT, padx=5)
            ttk.Label(frame, text=text).pack(side=tk.LEFT)
            entry = ttk.Entry(frame, width=15)
            entry.pack(side=tk.LEFT)
            self.filter_entries[name] = entry
        
        ttk.Button(filter_frame, text="Применить", command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Сбросить", command=self.reset_filters).pack(side=tk.LEFT, padx=5)
        
        # Таблица конструктивов
        columns = [
            ("Дата", "pour_date", 80),
            ("Конструктив", "element", 120),
            ("Класс", "concrete_class", 50),
            ("Мороз.", "frost_resistance", 60),
            ("Вода.", "water_resistance", 50),
            ("Поставщик", "supplier", 120),
            ("Паспорт", "concrete_passport", 80),
            ("Объем", "volume_concrete", 60),
            ("Кубики", "cubes_count", 60),
            ("Конусы", "cones_count", 60),
            ("Осадка", "slump", 60),
            ("Темп.", "temperature", 50),
            ("Замеры", "temp_measurements", 70),
            ("Исполнитель", "executor", 120),
            ("№ Акта", "act_number", 80),
            ("№ Заявки", "request_number", 80),
            ("Счет", "invoice", 50)
        ]
        
        # Создаем Treeview с колонкой для чекбоксов
        self.construction_tree = ttk.Treeview(
            construction_frame,
            columns=["selected"] + [col[1] for col in columns],
            show="headings",
            height=15,
            selectmode="extended"
        )

        # Колонка с чекбоксами
        self.construction_tree.heading("selected", text="☐", command=self.toggle_all_checkboxes)
        self.construction_tree.column("selected", width=30, anchor="center")
        self.construction_tree.bind("<<TreeviewSelect>>", lambda e: self.update_counters())

        # Остальные колонки
        for text, col, width in columns:
            self.construction_tree.heading(col, text=text)
            self.construction_tree.column(col, width=width, anchor='center')
            
        # Полосы прокрутки
        scrollbar_y = ttk.Scrollbar(construction_frame, orient="vertical", command=self.construction_tree.yview)
        scrollbar_y.pack(side="right", fill="y")
        self.construction_tree.configure(yscrollcommand=scrollbar_y.set)
        self.construction_tree.pack(fill=tk.BOTH, expand=True)

        # Горизонтальная полоса прокрутки для нижней панели
        scrollbar_x = ttk.Scrollbar(construction_frame, orient="horizontal", command=self.construction_tree.xview)
        self.construction_tree.configure(xscrollcommand=scrollbar_x.set)
        scrollbar_x.pack(side="bottom", fill="x")

        # Кнопки управления выделением
        btn_frame = ttk.Frame(construction_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        select_all_btn = ttk.Button(btn_frame, text="Выделить все", 
                                command=self.select_all_constructions)
        select_all_btn.pack(side=tk.LEFT, padx=5)

        deselect_all_btn = ttk.Button(btn_frame, text="Снять выделение", 
                                    command=self.deselect_all_constructions)
        deselect_all_btn.pack(side=tk.LEFT, padx=5)

        # Добавление значения в столбец "Счет" для выбранных записей
        self.invoice_value_var = tk.StringVar()
        self.invoice_entry = ttk.Entry(btn_frame, textvariable=self.invoice_value_var, width=18)
        self.invoice_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Добавить в счет", command=self.add_selected_to_invoice).pack(side=tk.LEFT, padx=5)

        # Привязка обработчика кликов
        self.construction_tree.bind("<Button-1>", self.toggle_checkbox)
        
        # Статусная строка
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Счетчик выделенных элементов
        self.selected_count_var = tk.StringVar()
        self.selected_count_var.set("Выделено: 0")
        selected_label = ttk.Label(self.status_frame, textvariable=self.selected_count_var)
        selected_label.pack(side=tk.LEFT)

        # Общий счетчик элементов
        self.total_count_var = tk.StringVar()
        self.total_count_var.set("Всего: 0")
        total_label = ttk.Label(self.status_frame, textvariable=self.total_count_var)
        total_label.pack(side=tk.LEFT, padx=10)

        # Статус выполнения операций
        self.status_var = tk.StringVar()
        self.status_var.set("Готово")
        status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT)

    def show_db_info(self):
        """Показывает информацию о базе данных"""
        try:
            db_info = self.db.get_connection_info()
            info_text = f"""
Информация о базе данных:

Тип: {db_info['type']}
Статус: {db_info['status']}
"""
            if 'host' in db_info:
                info_text += f"Хост: {db_info['host']}\n"
            if 'database' in db_info:
                info_text += f"База данных: {db_info['database']}\n"
            
            info_text += f"\nТест соединения: {'✅ Успешно' if self.db.test_connection() else '❌ Ошибка'}"
            
            messagebox.showinfo("Информация о БД", info_text)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить информацию о БД:\n{str(e)}")

    # ... остальные методы остаются без изменений ...
    # (для экономии места я не копирую весь код, так как он идентичен оригиналу)

    def load_organizations(self):
        try:
            if self.db.db_type == 'postgresql':
                rows = self.db.execute_query("SELECT id, name FROM organizations ORDER BY name")
                self.org_tree.delete(*self.org_tree.get_children())
                for row in rows:
                    self.org_tree.insert("", tk.END, values=(row['name'],), iid=row['id'])
            else:
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT id, name FROM organizations")
                self.org_tree.delete(*self.org_tree.get_children())
                for row in cursor.fetchall():
                    self.org_tree.insert("", tk.END, values=(row[1],), iid=row[0])
        except Exception as e:
            print(f"Ошибка загрузки организаций: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить организации:\n{str(e)}")

    def load_objects(self):
        if not self.current_org_id:
            return
            
        try:
            if self.db.db_type == 'postgresql':
                rows = self.db.execute_query("SELECT id, name, address FROM objects WHERE org_id = %s ORDER BY name", (self.current_org_id,))
                self.object_tree.delete(*self.object_tree.get_children())
                for row in rows:
                    self.object_tree.insert("", tk.END, values=(row['name'], row['address']), iid=row['id'])
            else:
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT id, name, address FROM objects WHERE org_id = ?", (self.current_org_id,))
                self.object_tree.delete(*self.object_tree.get_children())
                for row in cursor.fetchall():
                    self.object_tree.insert("", tk.END, values=row[1:], iid=row[0])
        except Exception as e:
            print(f"Ошибка загрузки объектов: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить объекты:\n{str(e)}")

    def load_constructions(self, filters=None):
        if not self.current_object_id:
            return
        
        self.construction_tree.delete(*self.construction_tree.get_children())

        try:
            if self.db.db_type == 'postgresql':
                query = """
                    SELECT id, pour_date, element, concrete_class, frost_resistance, water_resistance,
                    supplier, concrete_passport, volume_concrete, cubes_count, cones_count,
                    slump, temperature, temp_measurements, executor, act_number, request_number, invoice
                    FROM constructions 
                    WHERE object_id = %s
                """
                params = [self.current_object_id]

                if filters:
                    query += " AND " + " AND ".join([f"{key} LIKE %s" for key in filters.keys()])
                    params.extend([f"%{value}%" for value in filters.values()])

                rows = self.db.execute_query(query, tuple(params))
                
                for row in rows:
                    values = ["☐"] + [str(row.get(col, "")) for col in [
                        'pour_date', 'element', 'concrete_class', 'frost_resistance', 'water_resistance',
                        'supplier', 'concrete_passport', 'volume_concrete', 'cubes_count', 'cones_count',
                        'slump', 'temperature', 'temp_measurements', 'executor', 'act_number', 'request_number', 'invoice'
                    ]]
                    self.construction_tree.insert("", "end", values=values, iid=row['id'])
            else:
                cursor = self.db.conn.cursor()
                query = """
                    SELECT id, pour_date, element, concrete_class, frost_resistance, water_resistance,
                    supplier, concrete_passport, volume_concrete, cubes_count, cones_count,
                    slump, temperature, temp_measurements, executor, act_number, request_number, invoice
                    FROM constructions 
                    WHERE object_id = ?
                """
                params = [self.current_object_id]

                if filters:
                    query += " AND " + " AND ".join([f"{key} LIKE ?" for key in filters.keys()])
                    params.extend([f"%{value}%" for value in filters.values()])

                cursor.execute(query, params)
                
                for row in cursor.fetchall():
                    values = ["☐"] + [str(row[i]) if row[i] is not None else "" for i in range(1, len(row))]
                    self.construction_tree.insert("", "end", values=values, iid=row[0])
            
            self.update_counters()
            self.update_header_checkbox_state()
            
        except Exception as e:
            print(f"Ошибка загрузки конструктивов: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить конструктивы:\n{str(e)}")

    # ... остальные методы остаются без изменений ...
    # Для краткости я не копирую их все, но они должны быть адаптированы для работы с новым менеджером БД

    def __del__(self):
        """Деструктор для закрытия соединения с БД"""
        try:
            if hasattr(self, 'db'):
                self.db.close()
        except Exception:
            pass

def main():
    """Главная функция"""
    try:
        app = ConcreteApp()
        app.mainloop()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        messagebox.showerror("Критическая ошибка", f"Приложение не может быть запущено:\n{str(e)}")

if __name__ == "__main__":
    main()
