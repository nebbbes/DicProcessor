import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from charset_normalizer import detect
import os
import re
from itertools import product
import string
import time
import gc
import threading

class DictionaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dictionary Processor")
        self.root.geometry("600x600")
        
        self.bg_color = "#f0f0f0"
        self.root.config(bg=self.bg_color)
        
        # Инициализация переменных, всё по фен-шуй
        self.dict1_path = tk.StringVar()
        self.dict2_path = tk.StringVar()
        self.split_dict_path = tk.StringVar()
        self.edit_dict_path = tk.StringVar()
        self.merge_option = tk.StringVar(value="Объединить всё")
        self.split_option = tk.StringVar(value="По количеству слов")
        self.split_value = tk.StringVar(value="1000")
        self.min_length = tk.StringVar(value="8")
        self.mask_input = tk.StringVar()
        self.delete_duplicates_var = tk.BooleanVar()
        self.delete_short_var = tk.BooleanVar()
        self.is_running = False
        self.stop_generation = False  # Флаг для остановки генерации

        # Настраиваем интерфейс, лепим кнопки и поля
        self.create_widgets()
        self.bind_shortcuts()
        # Обрабатываем закрытие окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Фрейм для логов, чтоб видеть, что творится
        self.output_frame = tk.Frame(self.root, bg=self.bg_color)
        self.output_frame.pack(pady=5, fill="x", padx=5)
        
        self.output_text = tk.Text(self.output_frame, height=6, width=60, state='disabled', 
                                 bg="white", relief="sunken", wrap="word", font=("Courier", 8))
        self.output_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(self.output_frame, command=self.output_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        # Вкладки, чтобы всё красиво разложить
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Лепим все вкладки
        self.setup_merge_tab()
        self.setup_split_tab()
        self.setup_edit_tab()
        self.setup_mask_tab()

        # Контекстное меню для логов, чтобы копировать без гемора
        self.output_menu = tk.Menu(self.output_text, tearoff=0)
        self.output_menu.add_command(label="Копировать", command=lambda: self.copy_text(self.output_text))
        self.output_text.bind("<Button-3>", lambda e: self.show_text_menu(e, self.output_text, self.output_menu))

    def bind_shortcuts(self):
        # Биндим горячие клавиши, чтобы Ctrl+C и Ctrl+V работали как надо
        self.root.bind("<Control-c>", self.handle_copy)
        self.root.bind("<Control-v>", self.handle_paste)
        self.mask_entry.bind("<Control-v>", self.paste_entry)

    def on_closing(self):
        # Когда юзер закрывает окно, аккуратно всё сворачиваем
        self.stop_generation = True
        self.is_running = False
        self.root.destroy()

    def setup_merge_tab(self):
        # Вкладка для слияния словарей
        self.merge_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.merge_frame, text="Слияние")
        
        tk.Label(self.merge_frame, text="Словарь 1:", bg=self.bg_color).pack(anchor="w", padx=5, pady=2)
        tk.Entry(self.merge_frame, textvariable=self.dict1_path, state='readonly').pack(fill="x", padx=5)
        tk.Button(self.merge_frame, text="Выбрать...", command=self.select_dict1).pack(anchor="e", padx=5, pady=2)
        
        tk.Label(self.merge_frame, text="Словарь 2:", bg=self.bg_color).pack(anchor="w", padx=5, pady=2)
        tk.Entry(self.merge_frame, textvariable=self.dict2_path, state='readonly').pack(fill="x", padx=5)
        tk.Button(self.merge_frame, text="Выбрать...", command=self.select_dict2).pack(anchor="e", padx=5, pady=2)
        
        tk.Label(self.merge_frame, text="Опции слияния:", bg=self.bg_color).pack(anchor="w", padx=5, pady=2)
        tk.OptionMenu(self.merge_frame, self.merge_option, "Объединить всё", "Объединить без дубликатов").pack(fill="x", padx=5)
        
        self.merge_button = tk.Button(self.merge_frame, text="Выполнить слияние", command=self.merge_dictionaries)
        self.merge_button.pack(pady=10)

    def setup_split_tab(self):
        # Вкладка для разбивки словаря
        self.split_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.split_frame, text="Разбивка")
        
        tk.Label(self.split_frame, text="Словарь:", bg=self.bg_color).pack(anchor="w", padx=5, pady=2)
        tk.Entry(self.split_frame, textvariable=self.split_dict_path, state='readonly').pack(fill="x", padx=5)
        tk.Button(self.split_frame, text="Выбрать...", command=self.select_split_dict).pack(anchor="e", padx=5, pady=2)
        
        self.count_button = tk.Button(self.split_frame, text="Подсчитать слова", command=self.count_words)
        self.count_button.pack(pady=5)
        
        tk.Label(self.split_frame, text="Метод разбивки:", bg=self.bg_color).pack(anchor="w", padx=5, pady=2)
        tk.OptionMenu(self.split_frame, self.split_option, "По количеству слов", "По размеру (МБ)", "На равные части").pack(fill="x", padx=5)
        
        tk.Label(self.split_frame, text="Значение:", bg=self.bg_color).pack(anchor="w", padx=5, pady=2)
        tk.Entry(self.split_frame, textvariable=self.split_value).pack(fill="x", padx=5)
        
        self.split_button = tk.Button(self.split_frame, text="Выполнить разбивку", command=self.split_dictionary)
        self.split_button.pack(pady=10)

    def setup_edit_tab(self):
        # Вкладка для редактирования словаря
        self.edit_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.edit_frame, text="Редактор")
        
        tk.Label(self.edit_frame, text="Словарь:", bg=self.bg_color).pack(anchor="w", padx=5, pady=2)
        tk.Entry(self.edit_frame, textvariable=self.edit_dict_path, state='readonly').pack(fill="x", padx=5)
        tk.Button(self.edit_frame, text="Выбрать...", command=self.select_edit_dict).pack(anchor="e", padx=5, pady=2)
        
        tk.Checkbutton(self.edit_frame, text="Удалить дубликаты", variable=self.delete_duplicates_var, bg=self.bg_color).pack(anchor="w", padx=5, pady=2)
        
        edit_length_frame = tk.Frame(self.edit_frame, bg=self.bg_color)
        edit_length_frame.pack(fill="x", padx=5, pady=2)
        tk.Checkbutton(edit_length_frame, text="Удалить короче", variable=self.delete_short_var, bg=self.bg_color).pack(side="left")
        tk.Entry(edit_length_frame, textvariable=self.min_length, width=5).pack(side="left", padx=5)
        tk.Label(edit_length_frame, text="символов", bg=self.bg_color).pack(side="left")
        
        self.edit_button = tk.Button(self.edit_frame, text="Выполнить редактирование", command=self.edit_dictionary)
        self.edit_button.pack(pady=10)

    def setup_mask_tab(self):
        # Вкладка для генерации словаря по маске
        self.mask_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.mask_frame, text="Генератор")
        
        tk.Label(self.mask_frame, text="Маска:", bg=self.bg_color).pack(anchor="w", padx=5, pady=2)
        self.mask_entry = tk.Entry(self.mask_frame, textvariable=self.mask_input)
        self.mask_entry.pack(fill="x", padx=5)
        
        self.mask_menu = tk.Menu(self.mask_entry, tearoff=0)
        self.mask_menu.add_command(label="Копировать", command=self.copy_entry)
        self.mask_menu.add_command(label="Вставить", command=lambda: self.paste_entry())
        self.mask_entry.bind("<Button-3>", self.show_entry_menu)
        
        self.generate_button = tk.Button(self.mask_frame, text="Сгенерировать словарь", command=self.start_generate_mask_dictionary)
        self.generate_button.pack(pady=10)
        
        legend_frame = tk.LabelFrame(self.mask_frame, text="Легенда маски", bg=self.bg_color)
        legend_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.legend_text = tk.Text(legend_frame, height=6, width=50, state='normal', 
                                 bg="gold", relief="sunken", wrap="word", font=("Courier", 12))
        self.legend_text.insert(tk.END, """?1: цифры 0-9
?b: англ. строчные a-z
?B: англ. заглавные A-Z
?б: рус. строчные а-я
?Б: рус. заглавные А-Я
?$: спец. символы""")
        self.legend_text.config(state='disabled')
        self.legend_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.legend_menu = tk.Menu(self.legend_text, tearoff=0)
        self.legend_menu.add_command(label="Копировать", command=lambda: self.copy_text(self.legend_text))
        self.legend_text.bind("<Button-3>", lambda e: self.show_text_menu(e, self.legend_text, self.legend_menu))

    # ===== Основные методы, чтобы всё крутилось =====
    def log(self, message):
        # Пишем в лог, что происходит, если окно ещё живо
        if self.root.winfo_exists():
            self.output_text.config(state='normal')
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.output_text.config(state='disabled')
            self.root.update_idletasks()

    def disable_buttons(self):
        # Отрубаем кнопки, чтобы юзер не наклацал лишнего
        for btn in [self.merge_button, self.count_button, self.split_button, self.edit_button, self.generate_button]:
            if btn.winfo_exists():
                btn.config(state='disabled')

    def enable_buttons(self):
        # Включаем кнопки обратно, когда всё готово
        for btn in [self.merge_button, self.count_button, self.split_button, self.edit_button, self.generate_button]:
            if btn.winfo_exists():
                btn.config(state='normal')

    # ===== Работа с файлами =====
    def select_dict1(self):
        # Выбираем первый словарь
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.dict1_path.set(path)
            self.log(f"Забрали словарь 1: {path}")

    def select_dict2(self):
        # Выбираем второй словарь
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.dict2_path.set(path)
            self.log(f"Забрали словарь 2: {path}")

    def select_split_dict(self):
        # Выбираем словарь для разбивки
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.split_dict_path.set(path)
            self.log(f"Словарь для разбивки выбран: {path}")

    def select_edit_dict(self):
        # Выбираем словарь для редактирования
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.edit_dict_path.set(path)
            self.log(f"Словарь для редактирования выбран: {path}")

    # ===== Работа с текстом =====
    def copy_text(self, widget):
        # Копируем текст из виджета
        try:
            widget.config(state='normal')
            if widget.tag_ranges(tk.SEL):
                selected = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                selected = widget.get("1.0", tk.END).strip()
            
            if selected:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected)
                self.log(f"Скопировали из {widget.__class__.__name__}")
        except tk.TclError as e:
            self.log(f"Копирование накрылось: {e}")
        finally:
            if widget.winfo_exists():
                widget.config(state='disabled')

    def show_text_menu(self, event, widget, menu):
        # Показываем контекстное меню для текста
        try:
            widget.config(state='normal')
            if not widget.tag_ranges(tk.SEL):
                widget.tag_add(tk.SEL, f"@{event.x},{event.y}", tk.INSERT)
            menu.post(event.x_root, event.y_root)
        except tk.TclError as e:
            self.log(f"Меню не открылось, беда: {e}")
        finally:
            if widget.winfo_exists():
                widget.config(state='disabled')

    def copy_entry(self):
        # Копируем из поля маски
        try:
            if self.mask_entry.selection_present():
                selected = self.mask_entry.selection_get()
            else:
                selected = self.mask_entry.get()
            
            if selected:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected)
                self.log("Скопировали из поля маски")
        except tk.TclError as e:
            self.log(f"Копирование из маски накрылось: {e}")

    def paste_entry(self, event=None):
        # Вставляем в поле маски
        try:
            self.mask_entry.focus_set()
            clipboard = self.root.clipboard_get()
            if not clipboard.strip():
                self.log("Буфер пустой, нечего вставлять")
                return "break"
            
            # Чистим выделенный текст, если есть
            if self.mask_entry.selection_present():
                self.mask_entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
            
            self.mask_entry.insert(tk.INSERT, clipboard)
            self.log("Текст вставили, всё ок")
            return "break"  # Блокируем стандартную вставку
        except tk.TclError:
            self.log("Буфер пустой, ничего не вставили")
            return "break"
        except Exception as e:
            self.log(f"Вставка накрылась: {e}")
            return "break"

    def show_entry_menu(self, event):
        # Показываем контекстное меню для поля маски
        try:
            self.mask_menu.post(event.x_root, event.y_root)
        except tk.TclError as e:
            self.log(f"Меню не открылось: {e}")

    # ===== Операции со словарями =====
    def merge_dictionaries(self):
        # Сливаем словари
        if self.is_running:
            self.log("Чувак, уже что-то крутится, подожди...")
            return
            
        if not self.dict1_path.get() or not self.dict2_path.get():
            messagebox.showerror("Ошибка", "Выбери оба словаря, братан!")
            return
            
        self.is_running = True
        self.disable_buttons()
        self.log("Запускаем слияние словарей...")
        
        try:
            # Читаем словари
            dict1_path = self.dict1_path.get()
            dict2_path = self.dict2_path.get()
            if not (os.path.exists(dict1_path) and os.path.exists(dict2_path)):
                raise FileNotFoundError("Один из словарей не найден!")
            
            words = []
            total_lines = sum(1 for _ in open(dict1_path, 'r', encoding='utf-8')) + sum(1 for _ in open(dict2_path, 'r', encoding='utf-8'))
            processed = 0
            
            # Читаем первый словарь
            with open(dict1_path, 'r', encoding='utf-8') as f1:
                for line in f1:
                    if not self.root.winfo_exists():
                        self.log("Слияние остановлено, окно закрыто")
                        return
                    words.append(line.strip())
                    processed += 1
                    if processed % 1000 == 0:
                        self.log(f"Обработано {processed}/{total_lines} строк...")
                        self.root.update_idletasks()
            
            # Читаем второй словарь
            with open(dict2_path, 'r', encoding='utf-8') as f2:
                for line in f2:
                    if not self.root.winfo_exists():
                        self.log("Слияние остановлено, окно закрыто")
                        return
                    words.append(line.strip())
                    processed += 1
                    if processed % 1000 == 0:
                        self.log(f"Обработано {processed}/{total_lines} строк...")
                        self.root.update_idletasks()
            
            # Удаляем дубли, если надо
            if self.merge_option.get() == "Объединить без дубликатов":
                self.log("Убираем дубли, ща...")
                words = list(dict.fromkeys(words))  # Сохраняем порядок
                self.log(f"После чистки осталось {len(words)} строк")
            
            # Сохраняем результат
            output_path = 'merged_dict.txt'
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, word in enumerate(words):
                    if not self.root.winfo_exists():
                        self.log("Слияние остановлено, окно закрыто")
                        return
                    f.write(word + '\n')
                    if (i + 1) % 1000 == 0:
                        self.log(f"Записано {i + 1} строк в {output_path}...")
                        self.root.update_idletasks()
            
            self.log(f"Слияние готово, чекни {output_path}")
        except Exception as e:
            self.log(f"Слияние накрылось: {str(e)}")
        finally:
            self.is_running = False
            self.enable_buttons()

    def count_words(self):
        # Считаем слова в словаре
        if self.is_running:
            self.log("Чувак, уже что-то крутится, подожди...")
            return
            
        if not self.split_dict_path.get():
            messagebox.showerror("Ошибка", "Выбери словарь, бро!")
            return
            
        self.is_running = True
        self.disable_buttons()
        self.log("Считаем слова...")
        
        try:
            dict_path = self.split_dict_path.get()
            if not os.path.exists(dict_path):
                raise FileNotFoundError("Словарь не найден!")
            
            word_count = 0
            with open(dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not self.root.winfo_exists():
                        self.log("Подсчет остановлен, окно закрыто")
                        return
                    if line.strip():
                        word_count += 1
                    if word_count % 1000 == 0:
                        self.log(f"Посчитали {word_count} слов...")
                        self.root.update_idletasks()
            
            self.log(f"Подсчет закончен, всего слов: {word_count}")
        except Exception as e:
            self.log(f"Подсчет накрылся: {str(e)}")
        finally:
            self.is_running = False
            self.enable_buttons()

    def split_dictionary(self):
        # Разбиваем словарь на куски
        if self.is_running:
            self.log("Чувак, уже что-то крутится, подожди...")
            return
            
        if not self.split_dict_path.get():
            messagebox.showerror("Ошибка", "Выбери словарь, бро!")
            return
            
        try:
            value = float(self.split_value.get())
            if value <= 0:
                raise ValueError("Значение должно быть больше нуля!")
        except ValueError:
            messagebox.showerror("Ошибка", "Введи нормальное число, а не фигню!")
            return
            
        self.is_running = True
        self.disable_buttons()
        self.log("Запускаем разбивку словаря...")
        
        try:
            dict_path = self.split_dict_path.get()
            if not os.path.exists(dict_path):
                raise FileNotFoundError("Словарь не найден!")
            
            words = []
            with open(dict_path, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
            
            total_words = len(words)
            self.log(f"Всего слов в словаре: {total_words}")
            
            if total_words == 0:
                raise ValueError("Словарь пустой, нечего разбивать!")
            
            output_files = []
            split_option = self.split_option.get()
            
            if split_option == "По количеству слов":
                chunk_size = int(value)
                for i in range(0, total_words, chunk_size):
                    if not self.root.winfo_exists():
                        self.log("Разбивка остановлена, окно закрыто")
                        return
                    chunk = words[i:i + chunk_size]
                    output_path = f"split_dict_{i//chunk_size + 1}.txt"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        for word in chunk:
                            f.write(word + '\n')
                    output_files.append(output_path)
                    self.log(f"Сохранили кусок {output_path} ({len(chunk)} слов)")
                    self.root.update_idletasks()
            
            elif split_option == "По размеру (МБ)":
                target_size = value * 1024 * 1024  # Переводим МБ в байты
                current_size = 0
                current_chunk = []
                chunk_number = 1
                for word in words:
                    if not self.root.winfo_exists():
                        self.log("Разбивка остановлена, окно закрыто")
                        return
                    word_size = len(word.encode('utf-8')) + 1  # +1 для '\n'
                    if current_size + word_size > target_size and current_chunk:
                        output_path = f"split_dict_{chunk_number}.txt"
                        with open(output_path, 'w', encoding='utf-8') as f:
                            for w in current_chunk:
                                f.write(w + '\n')
                        output_files.append(output_path)
                        self.log(f"Сохранили кусок {output_path} ({len(current_chunk)} слов)")
                        self.root.update_idletasks()
                        current_chunk = []
                        current_size = 0
                        chunk_number += 1
                    current_chunk.append(word)
                    current_size += word_size
                if current_chunk:
                    output_path = f"split_dict_{chunk_number}.txt"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        for w in current_chunk:
                            f.write(w + '\n')
                    output_files.append(output_path)
                    self.log(f"Сохранили кусок {output_path} ({len(current_chunk)} слов)")
                    self.root.update_idletasks()
            
            elif split_option == "На равные части":
                num_parts = int(value)
                if num_parts <= 0:
                    raise ValueError("Количество частей должно быть больше нуля!")
                chunk_size = (total_words + num_parts - 1) // num_parts
                for i in range(0, total_words, chunk_size):
                    if not self.root.winfo_exists():
                        self.log("Разбивка остановлена, окно закрыто")
                        return
                    chunk = words[i:i + chunk_size]
                    output_path = f"split_dict_{i//chunk_size + 1}.txt"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        for word in chunk:
                            f.write(word + '\n')
                    output_files.append(output_path)
                    self.log(f"Сохранили кусок {output_path} ({len(chunk)} слов)")
                    self.root.update_idletasks()
            
            self.log(f"Разбивка готова, создали {len(output_files)} файлов: {', '.join(output_files)}")
        except Exception as e:
            self.log(f"Разбивка накрылась: {str(e)}")
        finally:
            self.is_running = False
            self.enable_buttons()

    def edit_dictionary(self):
        # Редактируем словарь
        if self.is_running:
            self.log("Чувак, уже что-то крутится, подожди...")
            return
            
        if not self.edit_dict_path.get():
            messagebox.showerror("Ошибка", "Выбери словарь, бро!")
            return
            
        try:
            min_len = int(self.min_length.get())
            if min_len < 1:
                raise ValueError("Длина должна быть больше нуля!")
        except ValueError:
            messagebox.showerror("Ошибка", "Введи нормальную длину, а не фигню!")
            return
            
        self.is_running = True
        self.disable_buttons()
        self.log("Запускаем редактирование словаря...")
        
        try:
            dict_path = self.edit_dict_path.get()
            if not os.path.exists(dict_path):
                raise FileNotFoundError("Словарь не найден!")
            
            words = []
            total_lines = sum(1 for _ in open(dict_path, 'r', encoding='utf-8'))
            processed = 0
            
            # Читаем словарь
            with open(dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not self.root.winfo_exists():
                        self.log("Редактирование остановлено, окно закрыто")
                        return
                    word = line.strip()
                    if word:
                        words.append(word)
                    processed += 1
                    if processed % 1000 == 0:
                        self.log(f"Обработано {processed}/{total_lines} строк...")
                        self.root.update_idletasks()
            
            # Удаляем короткие строки, если надо
            if self.delete_short_var.get():
                self.log(f"Убираем строки короче {min_len} символов...")
                words = [w for w in words if len(w) >= min_len]
                self.log(f"Осталось {len(words)} строк после фильтрации по длине")
                self.root.update_idletasks()
            
            # Удаляем дубли, если надо
            if self.delete_duplicates_var.get():
                self.log("Убираем дубли, ща...")
                words = list(dict.fromkeys(words))  # Сохраняем порядок
                self.log(f"После чистки дублей осталось {len(words)} строк")
                self.root.update_idletasks()
            
            # Сохраняем результат
            output_path = 'edited_dict.txt'
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, word in enumerate(words):
                    if not self.root.winfo_exists():
                        self.log("Редактирование остановлено, окно закрыто")
                        return
                    f.write(word + '\n')
                    if (i + 1) % 1000 == 0:
                        self.log(f"Записано {i + 1} строк в {output_path}...")
                        self.root.update_idletasks()
            
            self.log(f"Редактирование готово, чекни {output_path}")
        except Exception as e:
            self.log(f"Редактирование накрылось: {str(e)}")
        finally:
            self.is_running = False
            self.enable_buttons()

    def start_generate_mask_dictionary(self):
        # Запускаем генерацию в отдельном потоке
        if self.is_running:
            self.log("Чувак, уже что-то крутится, подожди...")
            return
            
        mask = self.mask_input.get()
        if not mask:
            messagebox.showerror("Ошибка", "Введи маску, бро!")
            return
            
        # Предупреждаем, если маска длинная
        if len(mask) > 5:
            if not messagebox.askokcancel("Предупреждение", "Маска длинная, может занять кучу времени! Продолжить?"):
                return
            
        self.is_running = True
        self.stop_generation = False
        self.disable_buttons()
        self.log(f"Запускаем генерацию по маске: {mask}")

        # Запускаем генерацию в отдельном потоке
        threading.Thread(target=self.generate_mask_dictionary, daemon=True).start()

    def generate_mask_dictionary(self):
        # Генерим словарь по маске
        try:
            char_sets = {
                '?1': string.digits,
                '?b': string.ascii_lowercase,
                '?B': string.ascii_uppercase,
                '?б': 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
                '?Б': 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ',
                '?$': '.,?!;:\'"*/)(+-&_₽#@$%^=[]{}|\\'
            }
            
            parts = []
            i = 0
            mask = self.mask_input.get()
            while i < len(mask):
                if self.stop_generation:
                    self.log("Генерация остановлена, юзер закрыл окно")
                    break
                if mask[i] == '?' and i+1 < len(mask) and mask[i:i+2] in char_sets:
                    parts.append(char_sets[mask[i:i+2]])
                    i += 2
                else:
                    parts.append([mask[i]])
                    i += 1
            
            if not self.stop_generation:
                with open('generated_dict.txt', 'w', encoding='utf-8') as f:
                    for i, combo in enumerate(product(*parts)):
                        if self.stop_generation:
                            self.log("Генерация остановлена, юзер закрыл окно")
                            break
                        word = ''.join(combo)
                        f.write(word + '\n')
                        if (i + 1) % 1000 == 0:
                            self.log(f"Сгенерировано {i + 1} комбинаций...")
                            if self.root.winfo_exists():
                                self.root.update_idletasks()
                
                if not self.stop_generation:
                    self.log("Генерация готова, чекни generated_dict.txt")
            
        except Exception as e:
            if self.root.winfo_exists():
                self.log(f"Генерация накрылась: {str(e)}")
        finally:
            self.is_running = False
            if self.root.winfo_exists():
                self.enable_buttons()

    # ===== Обработчики событий =====
    def handle_copy(self, event):
        # Копируем, если юзер тыкнул Ctrl+C
        widget = self.root.focus_get()
        if widget == self.mask_entry:
            self.copy_entry()
        elif widget in (self.output_text, self.legend_text):
            self.copy_text(widget)
        return "break"

    def handle_paste(self, event):
        # Вставляем, если юзер тыкнул Ctrl+V
        widget = self.root.focus_get()
        if widget == self.mask_entry:
            self.paste_entry()
        return "break"

if __name__ == "__main__":
    root = tk.Tk()
    try:
        # Пытаемся подрубить тему, если есть
        root.tk.call("source", "awthemes.tcl")
        root.tk.call("set_theme", "awlight")
    except:
        # Если не вышло, пох, идём дальше
        pass
        
    app = DictionaryApp(root)
    root.mainloop()