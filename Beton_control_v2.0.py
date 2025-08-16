import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
from datetime import datetime
import os
from docxtpl import DocxTemplate
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment


class ConcreteDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('concrete.db')
        self.create_tables()
    
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
        self.conn.commit()


class ConcreteApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.db = ConcreteDatabase()
        # Проверяем соединение с базой
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Доступные таблицы:", tables)  # Для отладки
            
        self.current_org_id = None
        self.current_object_id = None
        self.buttons_dict = {}
              
      

        self.title("Учет бетонных работ (prototipe by Kliapich v2.0)")
        self.geometry("1500x600")
        # Инициализация базы данных
        self.db = ConcreteDatabase()
        self.current_org_id = None
        self.current_object_id = None
        self.buttons_dict = {}
        
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
        
        # Остальная инициализация...
        self.create_widgets()
        self.load_organizations()
        self.update_buttons_state()

    

    def create_widgets(self):
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
        btn_frame = ttk.LabelFrame(self.left_panel, text="Действия", padding=5)
        btn_frame.pack(fill=tk.X, pady=5)

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
            ("Экспорт в Excel", self.export_to_excel)
        ]

        for text, cmd in buttons:
            btn = ttk.Button(btn_frame, text=text, command=cmd)
            btn.pack(fill=tk.X, pady=2)
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
            ("Поставщик:", "supplier")
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
            ("Класс", "concrete_class", 70),
            ("Мороз", "frost_resistance", 70),
            ("Вода", "water_resistance", 70),
            ("Поставщик", "supplier", 120),
            ("Паспорт", "concrete_passport", 120),
            ("Объем", "volume_concrete", 60),
            ("Кубики", "cubes_count", 60),
            ("Конусы", "cones_count", 60),
            ("Осадка", "slump", 60),
            ("Темп.", "temperature", 60),
            ("Замеры", "temp_measurements", 70),
            ("Исполнитель", "executor", 120),
            ("№ Акта", "act_number", 80),
            ("№ Заявки", "request_number", 80)
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
        scrollbar = ttk.Scrollbar(construction_frame, orient="vertical", command=self.construction_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.construction_tree.configure(yscrollcommand=scrollbar.set)
        self.construction_tree.pack(fill=tk.BOTH, expand=True)
        

        # Кнопки управления выделением
        btn_frame = ttk.Frame(construction_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        select_all_btn = ttk.Button(btn_frame, text="Выделить все", 
                                command=self.select_all_constructions)
        select_all_btn.pack(side=tk.LEFT, padx=5)

        deselect_all_btn = ttk.Button(btn_frame, text="Снять выделение", 
                                    command=self.deselect_all_constructions)
        deselect_all_btn.pack(side=tk.LEFT, padx=5)

        # Привязка обработчика кликов
        self.construction_tree.bind("<Button-1>", self.toggle_checkbox)
        
     
    ###### Метод для работы с чекбоксами ######
    def update_selection_status(self):
        """Обновляет статусную строку с количеством выделенных элементов"""
        selected_count = len(self.construction_tree.selection())
        total_count = len(self.construction_tree.get_children())
        self.status_var.set(f"Выделено: {selected_count}/{total_count} записей")

    def toggle_all_checkboxes(self):
        current_state = self.construction_tree.heading("selected", "text")
        new_state = "☐" if current_state == "☑" else "☑"
        
        self.construction_tree.heading("selected", text=new_state)
        
        for item in self.construction_tree.get_children():
            self.construction_tree.set(item, "selected", new_state)
        
       

    def toggle_checkbox(self, event):
        region = self.construction_tree.identify("region", event.x, event.y)
        column = self.construction_tree.identify_column(event.x)
        
        if region == "heading" and column == "#1":
            self.toggle_all_checkboxes()
            return
            
        if region == "cell" and column == "#1":
            item = self.construction_tree.identify_row(event.y)
            current_value = self.construction_tree.set(item, "selected")
            new_value = "☑" if current_value != "☑" else "☐"
            self.construction_tree.set(item, "selected", new_value)
        
        
        self.update_header_checkbox_state()

    def select_all_constructions(self):
        items = self.construction_tree.get_children()
        self.construction_tree.selection_set(items)
        for item in items:
            self.construction_tree.set(item, "selected", "☑")
        self.construction_tree.heading("selected", text="☑")
       

    def deselect_all_constructions(self):
        self.construction_tree.selection_remove(self.construction_tree.selection())
        for item in self.construction_tree.get_children():
            self.construction_tree.set(item, "selected", "☐")
        self.construction_tree.heading("selected", text="☐")
       

    def update_header_checkbox_state(self):
        """Обновляет состояние заголовка"""
        selected_count = len(self.construction_tree.selection())
        total_count = len(self.construction_tree.get_children())
        
        if selected_count == 0:
            self.construction_tree.heading("selected", text="☐")
        elif selected_count == total_count:
            self.construction_tree.heading("selected", text="☑")
        else:
            self.construction_tree.heading("selected", text="☒") 
            

        
    

    ################## Методы для работы с интерфейсом ##################
    def start_resize(self, event):
        self.resizing_panel = True
        self.start_x = event.x_root
    
    def resize_panel(self, event):
        if self.resizing_panel:
            delta = event.x_root - self.start_x
            new_width = self.left_panel_width + delta
            new_width = max(self.min_left_panel_width, min(self.max_left_panel_width, new_width))
            self.left_panel.config(width=new_width)
            self.org_tree.column("name", width=new_width-30)
            self.left_panel_width = new_width
            self.start_x = event.x_root
 
    def stop_resize(self, event):
        self.resizing_panel = False

    def start_resize_object_panel(self, event):
        self.resizing_object_panel = True
        self.start_y = event.y_root
    
    def resize_object_panel(self, event):
        if self.resizing_object_panel:
            delta = event.y_root - self.start_y
            new_height = self.object_frame.winfo_height() + delta
            new_height = max(self.object_panel_min_height, min(self.object_panel_max_height, new_height))
            self.object_frame.config(height=new_height)
            self.start_y = event.y_root
    
    def stop_resize_object_panel(self, event):
        self.resizing_object_panel = False

    

    def get_selected_constructions(self):
        """Получаем список выбранных конструктивов"""
        selected = []
        for item in self.construction_tree.get_children():
            if self.construction_tree.set(item, "selected") == "☑":
                selected.append(item)
        return selected if selected else self.construction_tree.selection()

    ################## Методы для работы с данными ######################
    def load_organizations(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, name FROM organizations")
        self.org_tree.delete(*self.org_tree.get_children())
        for row in cursor.fetchall():
            self.org_tree.insert("", tk.END, values=(row[1],), iid=row[0])

    def on_org_select(self, event=None):
        selected = self.org_tree.selection()
        if selected:
            self.current_org_id = int(selected[0])
            self.load_objects()
        else:
            self.current_org_id = None
        self.current_object_id = None
        self.update_buttons_state()

    def load_objects(self):
        if not self.current_org_id:
            return
            
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, name, address FROM objects WHERE org_id = ?", (self.current_org_id,))
        self.object_tree.delete(*self.object_tree.get_children())
        for row in cursor.fetchall():
            self.object_tree.insert("", tk.END, values=row[1:], iid=row[0])

    def on_object_select(self, event=None):
        selected = self.object_tree.selection()
        if selected:
            self.current_object_id = int(selected[0])
            self.load_constructions()
        else:
            self.current_object_id = None
        self.update_buttons_state()


    ################## Методы для работы с организациями ################
    def add_organization(self):
        dialog = tk.Toplevel(self)
        dialog.title("Добавить организацию")
        dialog.geometry("270x150")
        
        fields = [
            ("Название:", "name"),
            ("Контакт:", "contact"),
            ("Телефон:", "phone")
        ]
        
        entries = {}
        for i, (label, name) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            entry = ttk.Entry(dialog, width=30)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            entries[name] = entry
        
        def save():
            try:
                self.db.conn.execute(
                    "INSERT INTO organizations (name, contact, phone) VALUES (?, ?, ?)",
                    (entries['name'].get(), entries['contact'].get(), entries['phone'].get())
                )
                self.db.conn.commit()
                self.refresh_data()
                dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Ошибка", "Организация с таким названием уже существует")
        
        ttk.Button(dialog, text="Сохранить", command=save).grid(row=len(fields), columnspan=2, pady=10)
    
    def delete_organization(self):
        selected = self.org_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите организацию для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную организацию и все связанные данные?"):
            self.db.conn.execute("DELETE FROM organizations WHERE id=?", (selected[0],))
            self.db.conn.commit()
            self.current_org_id = None
            self.current_object_id = None
            self.refresh_data()
    
    def edit_organization(self):
        selected = self.org_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите организацию для редактирования")
            return
            
        org_id = int(selected[0])
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name, contact, phone FROM organizations WHERE id=?", (org_id,))
        org_data = cursor.fetchone()
        
        dialog = tk.Toplevel(self)
        dialog.title("Редактировать организацию")
        dialog.geometry("270x150")
        
        fields = [
            ("Название:", "name", org_data[0]),
            ("Контакт:", "contact", org_data[1]),
            ("Телефон:", "phone", org_data[2])
        ]
        
        entries = {}
        for i, (label, name, value) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            entry = ttk.Entry(dialog, width=30)
            entry.insert(0, value if value else "")
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            entries[name] = entry
        
        def save():
            try:
                self.db.conn.execute(
                    "UPDATE organizations SET name=?, contact=?, phone=? WHERE id=?",
                    (entries['name'].get(), entries['contact'].get(), entries['phone'].get(), org_id)
                )
                self.db.conn.commit()
                self.refresh_data()
                dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Ошибка", "Организация с таким названием уже существует")
        
        ttk.Button(dialog, text="Сохранить", command=save).grid(row=len(fields), columnspan=2, pady=10)

    ################## Методы для работы с объектами ####################
    def add_object(self):
        if not self.current_org_id:
            messagebox.showwarning("Ошибка", "Сначала выберите организацию")
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("Добавить объект")
        dialog.geometry("210x110")
        
        fields = [
            ("Название:", "name"),
            ("Адрес:", "address")
        ]
        
        entries = {}
        for i, (label, name) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            entry = ttk.Entry(dialog)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            entries[name] = entry
        
        def save():
            try:
                self.db.conn.execute(
                    "INSERT INTO objects (org_id, name, address) VALUES (?, ?, ?)",
                    (self.current_org_id, entries['name'].get(), entries['address'].get())
                )
                self.db.conn.commit()
                self.refresh_data()
                dialog.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", str(e))
        
        ttk.Button(dialog, text="Сохранить", command=save).grid(row=len(fields), columnspan=2, pady=10)
    
    def delete_object(self):
        selected = self.object_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите объект для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранный объект и все связанные данные?"):
            self.db.conn.execute("DELETE FROM objects WHERE id=?", (selected[0],))
            self.db.conn.commit()
            self.current_object_id = None
            self.refresh_data()

    def edit_object(self):
        selected = self.object_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите объект для редактирования")
            return
            
        object_id = int(selected[0])
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name, address FROM objects WHERE id=?", (object_id,))
        obj_data = cursor.fetchone()
        
        dialog = tk.Toplevel(self)
        dialog.title("Редактировать объект")
        dialog.geometry("210x110")
        
        fields = [
            ("Название:", "name", obj_data[0]),
            ("Адрес:", "address", obj_data[1])
        ]
        
        entries = {}
        for i, (label, name, value) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            entry = ttk.Entry(dialog)
            entry.insert(0, value if value else "")
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            entries[name] = entry
        
        def save():
            try:
                self.db.conn.execute(
                    "UPDATE objects SET name=?, address=? WHERE id=?",
                    (entries['name'].get(), entries['address'].get(), object_id)
                )
                self.db.conn.commit()
                self.refresh_data()
                dialog.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", str(e))
        
        ttk.Button(dialog, text="Сохранить", command=save).grid(row=len(fields), columnspan=2, pady=10)

    ################## Методы для работы с контролем ################
    def load_constructions(self, filters=None):
        if not self.current_object_id:
            return
        
        self.construction_tree.delete(*self.construction_tree.get_children())

        cursor = self.db.conn.cursor()
        query = """
            SELECT id, pour_date, element, concrete_class, frost_resistance, water_resistance,
            supplier, concrete_passport, volume_concrete, cubes_count, cones_count,
            slump, temperature, temp_measurements, executor, act_number, request_number
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
            self.update_header_checkbox_state()
        
    def apply_filters(self):
        filters = {}
        for key, entry in self.filter_entries.items():
            if entry.get():
                filters[key] = entry.get()
        
        self.load_constructions(filters)
    
    def reset_filters(self):
        for entry in self.filter_entries.values():
            entry.delete(0, tk.END)
        self.load_constructions()
        self.update_header_checkbox_state()
    
    def refresh_data(self):
        self.load_organizations()
        if self.current_org_id:
            self.load_objects()
        if self.current_object_id:
            self.load_constructions()
        self.update_buttons_state()

    def add_construction(self):
        if not self.current_object_id:
            messagebox.showwarning("Ошибка", "Сначала выберите объект")
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("Добавить контроль")
        dialog.geometry("280x440")
        dialog.grab_set()

        saved_successfully = False
        
        fields = [
            ("Дата (ДД-ММ-ГГГГ):", "pour_date"),
            ("Конструктив:", "element"),
            ("Класс бетона:", "concrete_class"),
            ("Морозостойкость:", "frost_resistance"),
            ("Водопроницаемость:", "water_resistance"),
            ("Поставщик:", "supplier"),
            ("Паспорт:", "concrete_passport"),
            ("Объем бетона (м³):", "volume_concrete"),
            ("Кубики:", "cubes_count"),
            ("Конусы:", "cones_count"),
            ("Осадка (см):", "slump"),
            ("Температура (°C):", "temperature"),
            ("Замеры темп.:", "temp_measurements"),
            ("Исполнитель:", "executor"),
            ("№ Акта:", "act_number"),
            ("№ Заявки:", "request_number")
        ]
        
        entries = {}
        for i, (label, name) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=5, pady=2, sticky='e')
            entry = ttk.Entry(dialog)
            entry.grid(row=i, column=1, padx=5, pady=2, sticky='w')
            entries[name] = entry
        
        # Установка значений по умолчанию
        entries['pour_date'].insert(0, datetime.now().strftime("%d-%m-%Y"))
        entries['concrete_class'].insert(0, "B")
        entries['frost_resistance'].insert(0, "F")
        entries['water_resistance'].insert(0, "W")
        
        def save():
            try:
                if not entries['pour_date'].get() or not entries['concrete_class'].get():
                    raise ValueError("Заполните обязательные поля (Дата и Класс бетона)")
            
                self.db.conn.execute(
                    """INSERT INTO constructions (
                        object_id, pour_date, element, concrete_class, frost_resistance,
                        water_resistance, supplier, concrete_passport, volume_concrete, cubes_count,
                        cones_count, slump, temperature, temp_measurements,
                        executor, act_number, request_number
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        self.current_object_id,
                        entries['pour_date'].get(),
                        entries['element'].get(),
                        entries['concrete_class'].get(),
                        entries['frost_resistance'].get(),
                        entries['water_resistance'].get(),
                        entries['supplier'].get(),
                        entries['concrete_passport'].get(),
                        float(entries['volume_concrete'].get() or 0),
                        int(entries['cubes_count'].get() or 0),
                        int(entries['cones_count'].get() or 0),
                        entries['slump'].get(),
                        entries['temperature'].get(),
                        int(entries['temp_measurements'].get() or 0),
                        entries['executor'].get(),
                        entries['act_number'].get(),
                        entries['request_number'].get()
                    )
                )
                self.db.conn.commit()
                saved_successfully = True
                dialog.destroy()
                self.refresh_data()
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e))
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка базы данных", str(e))
        
        ttk.Button(dialog, text="Сохранить", command=save).grid(row=len(fields), columnspan=2, pady=10)
    
        def on_close():
            if not saved_successfully:
                self.buttons_dict["+ Контроль"]['state'] = 'normal'
            dialog.destroy()
    
        dialog.protocol("WM_DELETE_WINDOW", on_close)

        ############ удаление данных контроля ############
    def delete_construction(self):
        selected = self.get_selected_constructions()  # Используем метод для получения выбранных записей
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите хотя бы один контроль для удаления")
            return
        
        # Подтверждение удаления
        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы действительно хотите удалить {len(selected)} выбранных записей?",
            parent=self
        )
        
        if not confirm:
            return
            
        try:
            cursor = self.db.conn.cursor()
            # Формируем параметризованный запрос для удаления нескольких записей
            placeholders = ','.join(['?'] * len(selected))
            query = f"DELETE FROM constructions WHERE id IN ({placeholders})"
            
            cursor.execute(query, selected)
            self.db.conn.commit()
            
            messagebox.showinfo(
                "Успех",
                f"Удалено {cursor.rowcount} записей",
                parent=self
            )
            
            self.refresh_data()
            
        except sqlite3.Error as e:
            messagebox.showerror(
                "Ошибка базы данных",
                f"Не удалось удалить записи:\n{str(e)}",
                parent=self
            )
            ######### конец удаления ###########

    def edit_construction(self):
        selected = self.construction_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите Контроль для редактирования")
            return
            
        constr_id = int(selected[0])
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT pour_date, element, concrete_class, frost_resistance, water_resistance,
                   supplier, concrete_passport, volume_concrete, cubes_count, cones_count,
                   slump, temperature, temp_measurements, executor, act_number, request_number
            FROM constructions WHERE id=?
        """, (constr_id,))
        constr_data = cursor.fetchone()
        
        dialog = tk.Toplevel(self)
        dialog.title("Редактировать контроль")
        dialog.geometry("280x440")
        dialog.grab_set()
        
        fields = [
            ("Дата (ДД-ММ-ГГГГ):", "pour_date", constr_data[0]),
            ("Конструктив:", "element", constr_data[1]),  
            ("Класс бетона:", "concrete_class", constr_data[2]),
            ("Морозостойкость:", "frost_resistance", constr_data[3]),
            ("Водопроницаемость:", "water_resistance", constr_data[4]),
            ("Поставщик:", "supplier", constr_data[5]),
            ("Паспорт:", "concrete_passport", constr_data[6]),
            ("Объем бетона (м³):", "volume_concrete", constr_data[7]),
            ("Кубики:", "cubes_count", constr_data[8]),
            ("Конусы:", "cones_count", constr_data[9]),
            ("Осадка (см):", "slump", constr_data[10]),
            ("Температура (°C):", "temperature", constr_data[11]),
            ("Замеры темп.:", "temp_measurements", constr_data[12]),
            ("Исполнитель:", "executor", constr_data[13]),
            ("№ Акта:", "act_number", constr_data[14]),
            ("№ Заявки:", "request_number", constr_data[15])
        ]
        
        entries = {}
        for i, (label, name, value) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=5, pady=2, sticky='e')
            entry = ttk.Entry(dialog)
            entry.insert(0, str(value) if value is not None else "")
            entry.grid(row=i, column=1, padx=5, pady=2, sticky='w')
            entries[name] = entry
        
        def save():
            try:
                self.db.conn.execute("""
                    UPDATE constructions SET
                        pour_date=?, element=?, concrete_class=?, frost_resistance=?,
                        water_resistance=?, supplier=?, concrete_passport=?,
                        volume_concrete=?, cubes_count=?, cones_count=?,
                        slump=?, temperature=?, temp_measurements=?,
                        executor=?, act_number=?, request_number=?
                    WHERE id=?
                """, (
                    entries['pour_date'].get(),
                    entries['element'].get(),
                    entries['concrete_class'].get(),
                    entries['frost_resistance'].get(),
                    entries['water_resistance'].get(),
                    entries['supplier'].get(),
                    entries['concrete_passport'].get(),
                    float(entries['volume_concrete'].get() or 0),
                    int(entries['cubes_count'].get() or 0),
                    int(entries['cones_count'].get() or 0),
                    entries['slump'].get(),
                    entries['temperature'].get(),
                    int(entries['temp_measurements'].get() or 0),
                    entries['executor'].get(),
                    entries['act_number'].get(),
                    entries['request_number'].get(),
                    constr_id
                ))
                self.db.conn.commit()
                self.refresh_data()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Некорректные данные: {str(e)}")
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка базы данных", str(e))
        
        ttk.Button(dialog, text="Сохранить", command=save).grid(row=len(fields), columnspan=2, pady=10)

    ################## Методы для работы с документами ##################
    def create_request(self):
        selected = self.get_selected_constructions()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите хотя бы один контроль")
            return

        for constr_id in selected:
            self.generate_document(constr_id, "request_template.docx", "Заявка")

    def create_act(self):
        selected = self.get_selected_constructions()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите хотя бы один контроль")
            return

        for constr_id in selected:
            self.generate_document(constr_id, "act_template.docx", "Акт")

    def generate_document(self, constr_id, template_name, doc_type):
        try:
            if not os.path.exists(template_name):
                messagebox.showerror("Ошибка", f"Шаблон {template_name} не найден")
                return
            
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT 
                    c.pour_date, c.element, c.concrete_class, c.frost_resistance, c.water_resistance,  
                    c.supplier, c.concrete_passport, c.volume_concrete, c.cubes_count, c.act_number, c.request_number,
                    o.name as object_name, o.address,
                    org.name as org_name, org.contact, org.phone
                FROM constructions c
                JOIN objects o ON c.object_id = o.id
                JOIN organizations org ON o.org_id = org.id
                WHERE c.id = ?
            """, (constr_id,))

            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("Ошибка", "Контроль не найден")
                return
            
            construction_data = dict(zip(columns, row))

            try:
                pour_date = datetime.strptime(construction_data['pour_date'], "%d-%m-%Y")
                file_date = pour_date.strftime("%d-%m-%Y")
                doc_date = pour_date.strftime("%d.%m.%Y")
            except ValueError:
                file_date = "без_даты"
                doc_date = construction_data['pour_date']
                
                ################ Индексы для замены слов ####################
            context = {
                'doc_type': doc_type,
                'current_date': datetime.now().strftime("%d.%m.%Y"),
                'construction': {
                    'object': construction_data.get('object_name', '') or '',
                    'address': construction_data.get('address', '') or '',
                    'date': construction_data.get('pour_date', '') or '',
                    'element': construction_data.get('element', '') or '',  
                    'concrete': construction_data.get('concrete_class', '') or '',
                    'frost': construction_data.get('frost_resistance', '') or '',
                    'water': construction_data.get('water_resistance', '') or '',
                    'supplier': construction_data.get('supplier', '') or '',
                    'passport': construction_data.get('concrete_passport', '') or '',
                    'volume': construction_data.get('volume_concrete', '') or '',
                    
                    'act': construction_data.get('act_number', '') or '',
                    'request': construction_data.get('request_number', '') or '' 
                },
                'organization': {
                    'name': construction_data.get('org_name', '') or '',
                    'contact': construction_data.get('contact', '') or '',
                    'phone': construction_data.get('phone', '') or ''
                }
            }
            
            object_name = construction_data.get('object_name', 'объект').replace(' ', '_')
            safe_filename = (
                f"{doc_type}_"
                f"{object_name[:30]}_"
                f"{file_date}.docx"
            )

            filepath = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Документ Word", "*.docx")],
                initialfile=safe_filename,
                title=f"Сохранить {doc_type.lower()}"
            )
        
            if filepath:
                doc = DocxTemplate(template_name)
                doc.render(context)
                doc.save(filepath)
                messagebox.showinfo("Готово", f"{doc_type} сохранен:\n{os.path.basename(filepath)}")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании документа:\n{str(e)}")

    ################## Методы для работы с Excel #######################
    def generate_import_template(self):
        """Создание шаблона для импорта"""
        template_type = simpledialog.askstring(
            "Шаблон импорта",
            "Для чего создать шаблон? (org/obj/con):",
            parent=self
        )

        wb = Workbook()
        ws = wb.active

        if template_type == "org":
            ws.append(["Название организации", "Контактное лицо", "Телефон"])
            filename = "template_org.xlsx"
        elif template_type == "obj":
            ws.append(["Название объекта", "Адрес"])
            filename = "template_obj.xlsx"
        elif template_type == "con":
            ws.append([
                "Дата (ДД-ММ-ГГГГ)", "Конструктив", "Класс бетона", "Морозостойкость", 
                "Водопроницаемость", "Поставщик", "Паспорт", "Объем бетона",
                "Кубики", "Конусы", "Осадка", "Температура", "Замеры темп.",
                "Исполнитель", "№ Акта", "№ Заявки"
            ])
            filename = "template_constr.xlsx"
        else:
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=filename,
            filetypes=[("Excel files", "*.xlsx")]
        )
        if filepath:
            wb.save(filepath)
            messagebox.showinfo("Успех", f"Шаблон сохранен как {filepath}")

    def import_from_excel(self):
        """Импорт данных из Excel файла"""
        filepath = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not filepath:
            return

        try:
            wb = load_workbook(filename=filepath)
            ws = wb.active

            import_type = simpledialog.askstring(
                "Тип импорта",
                "Что импортируем? (org - организации, obj - объекты, con - контроль):",
                parent=self
            )

            if import_type == "org":
                self._import_organizations(ws)
            elif import_type == "obj":
                self._import_objects(ws)
            elif import_type == "con":
                self._import_constructions(ws)
            else:
                messagebox.showwarning("Ошибка", "Неверный тип импорта")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при импорте:\n{str(e)}")
        finally:
            self.refresh_data()

    def _import_organizations(self, worksheet):
        """Импорт организаций из Excel"""
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            if row and row[0]:
                self.db.conn.execute(
                    """INSERT OR IGNORE INTO organizations 
                    (name, contact, phone) VALUES (?, ?, ?)""",
                    (row[0], row[1] if len(row) > 1 else None, row[2] if len(row) > 2 else None)
                )
        self.db.conn.commit()
        messagebox.showinfo("Успех", f"Импортировано {worksheet.max_row-1} организаций")

    def _import_objects(self, worksheet):
        """Импорт объектов из Excel"""
        if not self.current_org_id:
            raise ValueError("Сначала выберите организацию")

        for row in worksheet.iter_rows(min_row=2, values_only=True):
            if row and row[0]:
                self.db.conn.execute(
                    """INSERT OR IGNORE INTO objects 
                    (org_id, name, address) VALUES (?, ?, ?)""",
                    (self.current_org_id, row[0], row[1] if len(row) > 1 else None)
                )
        self.db.conn.commit()
        messagebox.showinfo("Успех", f"Импортировано {worksheet.max_row-1} объектов")

    def _import_constructions(self, worksheet):
        """Импорт конструктивов из Excel"""
        if not self.current_object_id:
            raise ValueError("Сначала выберите объект")

        headers = [cell.value for cell in worksheet[1]]
        imported_count = 0

        for row in worksheet.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue

            data = {
                'object_id': self.current_object_id,
                'pour_date': row[headers.index('Дата (ДД-ММ-ГГГГ)')] if 'Дата (ДД-ММ-ГГГГ)' in headers else None,
                'element': row[headers.index('Конструктив')] if 'Конструктив' in headers else None,
                'concrete_class': row[headers.index('Класс бетона')] if 'Класс бетона' in headers else None,
                'frost_resistance': row[headers.index('Морозостойкость')] if 'Морозостойкость' in headers else None,
                'water_resistance': row[headers.index('Водопроницаемость')] if 'Водопроницаемость' in headers else None,
                'supplier': row[headers.index('Поставщик')] if 'Поставщик' in headers else None,
                'concrete_passport': row[headers.index('Паспорт')] if 'Паспорт' in headers else None,
                'volume_concrete': row[headers.index('Объем бетона')] if 'Объем бетона' in headers else 0,
                'cubes_count': row[headers.index('Кубики')] if 'Кубики' in headers else 0,
                'cones_count': row[headers.index('Конусы')] if 'Конусы' in headers else 0,
                'slump': row[headers.index('Осадка')] if 'Осадка' in headers else None,
                'temperature': row[headers.index('Температура')] if 'Температура' in headers else None,
                'temp_measurements': row[headers.index('Замеры темп.')] if 'Замеры темп.' in headers else 0,
                'executor': row[headers.index('Исполнитель')] if 'Исполнитель' in headers else None,
                'act_number': row[headers.index('№ Акта')] if '№ Акта' in headers else None,
                'request_number': row[headers.index('№ Заявки')] if '№ Заявки' in headers else None
            }

            self.db.conn.execute("""
                INSERT INTO constructions (
                    object_id, pour_date, element, concrete_class, frost_resistance,
                    water_resistance, supplier, concrete_passport, volume_concrete, cubes_count,
                    cones_count, slump, temperature, temp_measurements,
                    executor, act_number, request_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(data.values()))

            imported_count += 1

        self.db.conn.commit()
        messagebox.showinfo("Успех", f"Импортировано {imported_count} контролей")

    def export_to_excel(self):
        if not self.current_object_id:
            messagebox.showwarning("Ошибка", "Сначала выберите объект")
            return
    
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT 
                    o.name as object_name, 
                    org.name as org_name
                FROM objects o
                JOIN organizations org ON o.org_id = org.id
                WHERE o.id = ?
            """, (self.current_object_id,))
            result = cursor.fetchone()
        
            if not result:
                messagebox.showwarning("Ошибка", "Не удалось получить данные объекта")
                return
            
            object_name = result[0]
            org_name = result[1]
    
            cursor.execute("""
                SELECT pour_date, element, concrete_class, frost_resistance, water_resistance,
                    supplier, concrete_passport, volume_concrete, cubes_count, cones_count,
                    slump, temperature, temp_measurements, executor, act_number, request_number
                FROM constructions 
                WHERE object_id = ?
                ORDER BY pour_date
            """, (self.current_object_id,))
            constructions = cursor.fetchall()
    
            if not constructions:
                messagebox.showwarning("Ошибка", "Нет данных для экспорта")
                return
    
            wb = Workbook()
            ws = wb.active
            ws.title = "Бетонные работы"
    
            safe_org_name = "".join(x for x in org_name if x.isalnum() or x in (" ", "_")).strip()[:30]
            safe_object_name = "".join(x for x in object_name if x.isalnum() or x in (" ", "_")).strip()[:30]
            default_filename = f"{safe_org_name}_{safe_object_name}_Контроль_бетона.xlsx"

            ws['A1'] = f"Организация: {org_name}"
            ws['A1'].font = Font(bold=True, size=12)
        
            ws['A2'] = f"Объект: {object_name}"
            ws['A2'].font = Font(bold=True, size=12)

            column_widths = {
                'A': 12, 'B': 14, 'C': 18, 'D': 20, 'E': 15, 
                'F': 15, 'G': 15, 'H': 10, 'I': 10, 'J': 10, 
                'K': 15, 'L': 15, 'M': 15, 'N': 10, 'O': 10
            }

            for col, width in column_widths.items():
                ws.column_dimensions[col].width = width

            headers = [
                "Дата", "Конструктив", "Класс бетона", "Морозостойкость", "Водопроницаемость",
                "Поставщик", "Паспорт", "Объем бетона", "Кубики", "Конусы",
                "Осадка", "Температура", "Замеры темп.", "Исполнитель", 
                "№ Акта", "№ Заявки"
            ]
            ws.append(headers)
    
            for cell in ws[3]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
    
            for row in constructions:
                ws.append(row)

            for row in ws.iter_rows(min_row=4, max_row=ws.max_row):
                for cell in row:
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    if isinstance(cell.value, (int, float)):
                        cell.number_format = '0'
    
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
            
                for cell in col[2:]:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column].width = adjusted_width
    
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=default_filename
            )
        
            if filename:
                wb.save(filename)
                messagebox.showinfo("Успех", f"Файл успешно сохранен как {filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при экспорте:\n{str(e)}")

    ################## Вспомогательные методы ###########################
    def update_buttons_state(self):
        """Обновляет состояние кнопок в зависимости от выбора"""
        states = {
            "+ Объект": 'normal' if self.current_org_id else 'disabled',
            "- Объект": 'normal' if self.current_org_id else 'disabled',
            "Ред. Объект": 'normal' if self.current_org_id else 'disabled',
            "+ Контроль": 'normal' if self.current_object_id else 'disabled',
            "- Контроль": 'normal' if self.current_object_id else 'disabled',
            "Ред. Контроль": 'normal' if self.current_object_id else 'disabled'
        }
        
        org_selected = bool(self.org_tree.selection())
        self.buttons_dict["- Организацию"]['state'] = 'normal' if org_selected else 'disabled'
        self.buttons_dict["Ред. Организацию"]['state'] = 'normal' if org_selected else 'disabled'
        
        for btn_text, state in states.items():
            if btn_text in self.buttons_dict:
                self.buttons_dict[btn_text]['state'] = state

if __name__ == "__main__":
    app = ConcreteApp()
    app.mainloop()