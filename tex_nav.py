import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os
import datetime
import shutil
import re
import ctypes
import subprocess
 
ctypes.windll.shcore.SetProcessDpiAwareness(1)

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("TEX-NAV")
        self.root.geometry("1200x600")
        
        # Set the window icon
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(application_path, 'tex_nav_icon.ico')
        self.root.iconbitmap(icon_path)

        # Configure dark mode colors
        self.bg_color = "#2E2E2E"  # Dark grey
        self.fg_color = "white"
        self.highlight_bg = "#4A4A4A"  # Lighter grey for highlights

        # Default font sizes
        self.font_size = 12
        self.query_font_size = 12
        
        self.line_numbers_enabled = True
        self.line_numbers = None
        self.text_area = None
        
        self.editor_font = ('Courier', self.font_size)

        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TNotebook', background=self.bg_color)
        self.style.configure('TNotebook.Tab', background=self.bg_color, foreground=self.fg_color)
        self.style.map('TNotebook.Tab', background=[('selected', self.highlight_bg)])
        self.style.configure('TButton', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        
        # Main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left frame for directory listing and suggestions
        left_frame = ttk.Frame(main_frame, width=200)
        left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        left_frame.grid_propagate(False)  # Prevent the frame from changing size
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_rowconfigure(2, weight=1)

        # Directory listing
        dir_frame = ttk.Frame(left_frame)
        dir_frame.grid(row=0, column=0, sticky="nsew")
        dir_frame.grid_columnconfigure(0, weight=1)
        dir_frame.grid_rowconfigure(0, weight=1)

        self.dir_listbox = tk.Listbox(dir_frame, bg=self.bg_color, fg=self.fg_color)
        self.dir_listbox.grid(row=0, column=0, sticky="nsew")
        self.dir_listbox.bind('<Double-1>', self.open_selected_file)

        # Scrollbar for directory listing
        dir_scrollbar = ttk.Scrollbar(dir_frame, orient="vertical", command=self.dir_listbox.yview)
        dir_scrollbar.grid(row=0, column=1, sticky="ns")
        self.dir_listbox.config(yscrollcommand=dir_scrollbar.set)

        # Small gap
        ttk.Frame(left_frame, height=10).grid(row=1, column=0)

        # Suggestions
        suggestion_frame = ttk.Frame(left_frame)
        suggestion_frame.grid(row=2, column=0, sticky="nsew")
        suggestion_frame.grid_columnconfigure(0, weight=1)
        suggestion_frame.grid_rowconfigure(1, weight=1)

        ttk.Label(suggestion_frame, text="Top 10 matches", font=('Courier', 10, 'bold')).grid(row=0, column=0, pady=(0, 5), sticky="nw")
        self.suggestion_listbox = tk.Listbox(suggestion_frame, bg=self.bg_color, fg=self.fg_color)
        self.suggestion_listbox.grid(row=1, column=0, sticky="nsew")
        self.suggestion_listbox.bind('<Double-1>', self.use_suggestion)

        # Scrollbar for suggestions
        suggestion_scrollbar = ttk.Scrollbar(suggestion_frame, orient="vertical", command=self.suggestion_listbox.yview)
        suggestion_scrollbar.grid(row=1, column=1, sticky="ns")
        self.suggestion_listbox.config(yscrollcommand=suggestion_scrollbar.set)

        # Editor frame
        editor_frame = ttk.Frame(main_frame)
        editor_frame.grid(row=0, column=1, sticky="nsew")
        editor_frame.grid_propagate(False)  # Prevent the frame from changing size
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(0, weight=1)

        # Notebook (tabbed interface)
        self.notebook = ttk.Notebook(editor_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Query frame
        query_frame = ttk.Frame(main_frame)
        query_frame.grid(row=1, column=1, sticky="ew", pady=(5, 0))
        query_frame.grid_columnconfigure(1, weight=1)

        # Query label
        ttk.Label(query_frame, text="Query:", font=('Courier', self.query_font_size)).grid(row=0, column=0, padx=(0, 5))

        # Query entry
        self.query_entry = ttk.Entry(query_frame, font=('Courier', self.query_font_size), style='TEntry')
        self.query_entry.grid(row=0, column=1, sticky="ew")
        self.query_entry.bind('<Return>', self.process_query)
        self.query_entry.bind('<KeyRelease>', self.update_suggestions)
        self.query_entry.bind('<Tab>', self.autofill_suggestion)

        # Execute button
        execute_button = ttk.Button(query_frame, text="Execute", command=self.process_query, style='TButton')
        execute_button.grid(row=0, column=2, padx=(5, 0))

        # Set initial directory
        self.current_dir = os.path.expanduser('~')
        self.update_dir_listing()
        
        self.unsaved_changes = {}  # Dictionary to track unsaved changes for each tab

        # Create the first tab
        self.open_file("Untitled-1")
        
        # Maximize the window
        self.root.state('zoomed')

        # Initialize search position
        self.current_search_position = '1.0'
        self.word_to_find = ""
        
        # Store find next window
        self.find_window = None
        
        # Initialize find and replace variables
        self.find_replace_window = None
        self.current_search_position = '1.0'
        self.word_to_find = ""
        self.highlight_tag = 'highlight'
        self.current_highlight_tag = 'current_highlight'
        self.case_sensitive_var = tk.BooleanVar()
        self.case_sensitive_var.set(True)
        
        self.use_spaces = tk.BooleanVar(value=True)  # Default to spaces
        self.tab_width = tk.IntVar(value=4)  # Default to 4 spaces/tab width
        self.bind_auto_indent()
        self.create_indent_settings()
        
        self.suggestions = []
        self.suggestion_index = 0
        self.current_word = ""
        self.completing = False
        
    def open_command_prompt(self):
        subprocess.Popen(f'start cmd /K "cd /d {self.current_dir}"', shell=True)
        
    def handle_autocomplete(self, event):
        current_word = self.get_current_word()
        if not self.completing or current_word != self.current_word:
            self.current_word = current_word
            self.suggestions = self.generate_suggestions(self.current_word)
            self.suggestion_index = 0
            self.completing = True
        else:
            self.suggestion_index = (self.suggestion_index + 1) % len(self.suggestions)
        
        if self.suggestions:
            self.insert_suggestion()
        else:
            self.completing = False
        
        return 'break'
        
    def get_current_word(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if not text_widget:
            return ""

        current_pos = text_widget.index(tk.INSERT)
        line, col = current_pos.split('.')
        line_start = f"{line}.0"
        line_content = text_widget.get(line_start, current_pos)
        
        word_match = re.search(r'\w+$', line_content)
        
        return word_match.group() if word_match else ""
        
    def generate_suggestions(self, prefix):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if not text_widget:
            return []

        content = text_widget.get("1.0", tk.END)
        words = re.findall(r'\b\w+\b', content)
        unique_words = sorted(set(words))
        return [word for word in unique_words if word.lower().startswith(prefix.lower()) and word.lower() != prefix.lower()]
        
    def insert_suggestion(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if not text_widget:
            return

        suggestion = self.suggestions[self.suggestion_index]
        current_pos = text_widget.index(tk.INSERT)
        line, col = current_pos.split('.')
        
        # Find the start of the current word
        line_start = f"{line}.0"
        line_content = text_widget.get(line_start, current_pos)
        word_start_match = re.search(r'\w+$', line_content)
        
        if word_start_match:
            word_start = f"{line}.{int(col) - len(word_start_match.group())}"
        else:
            word_start = current_pos
        
        # Delete the part of the word before the cursor
        text_widget.delete(word_start, current_pos)
        
        # Insert the suggestion
        text_widget.insert(word_start, suggestion)
        
        # Move the cursor to the end of the inserted suggestion
        text_widget.mark_set(tk.INSERT, f"{line}.{int(col) - len(self.current_word) + len(suggestion)}")
        
        # Update current_word to the full suggestion for subsequent cycles
        self.current_word = suggestion
        
    def on_key_release(self, event):
        if event.keysym not in ('Control_L', 'Control_R'):
            self.completing = False
            self.current_word = ""
            self.suggestions = []
            self.suggestion_index = 0
        
    def create_indent_settings(self):
        # Create a frame for indent settings
        indent_frame = ttk.Frame(self.root)
        indent_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Checkbox for using spaces
        use_spaces_cb = ttk.Checkbutton(indent_frame, text="Use Spaces", variable=self.use_spaces)
        use_spaces_cb.pack(side=tk.LEFT, padx=5)

        # Label and entry for tab width
        ttk.Label(indent_frame, text="Tab Width:").pack(side=tk.LEFT, padx=(10, 0))
        tab_width_entry = ttk.Entry(indent_frame, textvariable=self.tab_width, width=3)
        tab_width_entry.pack(side=tk.LEFT, padx=5)

        # Button to apply tab width changes
        apply_button = ttk.Button(indent_frame, text="Apply", command=self.apply_tab_width)
        apply_button.pack(side=tk.LEFT, padx=5)

    def apply_tab_width(self):
        try:
            new_width = int(self.tab_width.get())
            if 1 <= new_width <= 8:
                # Tab width is valid, no need to do anything else
                pass
            else:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Tab width must be an integer between 1 and 8.")
            self.tab_width.set(4)  # Reset to default if invalid

    def get_indent_string(self):
        if self.use_spaces.get():
            return ' ' * self.tab_width.get()
        else:
            return '\t'
            
    def bind_auto_indent(self):
        for tab in self.notebook.tabs():
            text_widget = self.get_text_widget(self.notebook.nametowidget(tab))
            if text_widget:
                text_widget.bind('<Return>', self.auto_indent)
                text_widget.bind('<Tab>', self.handle_tab)
                text_widget.bind('<Shift-Tab>', self.handle_shift_tab)
                
    def auto_indent(self, event):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if not text_widget:
            return 'break'
        
        cursor_pos = text_widget.index(tk.INSERT)
        line_num = int(cursor_pos.split('.')[0])
        line = text_widget.get(f"{line_num}.0", f"{line_num}.end")
        
        # Get the indentation of the current line
        indentation = re.match(r'^(\s*)', line).group(1)
        
        # Insert the new line with the same indentation
        text_widget.insert(tk.INSERT, f"\n{indentation}")
        
        self.update_line_numbers()  # Update line numbers after auto-indent
        return 'break'  # Prevent the default behavior
        
    def handle_tab(self, event):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if not text_widget:
            return None
        
        try:
            sel_start = text_widget.index("sel.first")
            sel_end = text_widget.index("sel.last")
            selected = True
        except tk.TclError:
            selected = False

        if selected:
            result = self.indent_selected_lines(text_widget, sel_start, sel_end)
            self.update_line_numbers()  # Update line numbers after indentation
            return result
        else:
            # Existing behavior for when there's no selection
            cursor_pos = text_widget.index(tk.INSERT)
            line_num, col_num = map(int, cursor_pos.split('.'))
            line = text_widget.get(f"{line_num}.0", f"{line_num}.end")
            
            if col_num == 0 or line[:col_num].isspace():
                text_widget.insert(tk.INSERT, self.get_indent_string())
                self.update_line_numbers()  # Update line numbers after adding indentation
                return 'break'
            
            return None  # Allow default tab behavior elsewhere
    
    def handle_shift_tab(self, event):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if not text_widget:
            return None
        
        try:
            sel_start = text_widget.index("sel.first")
            sel_end = text_widget.index("sel.last")
            selected = True
        except tk.TclError:
            selected = False

        if selected:
            result = self.unindent_selected_lines(text_widget, sel_start, sel_end)
        else:
            # Unindent current line if no selection
            cursor_pos = text_widget.index(tk.INSERT)
            line_num = int(cursor_pos.split('.')[0])
            result = self.unindent_selected_lines(text_widget, f"{line_num}.0", f"{line_num}.end")
        
        self.update_line_numbers()  # Update line numbers after unindentation
        return result
            
    def indent_selected_lines(self, text_widget, sel_start, sel_end):
        start_line = int(sel_start.split('.')[0])
        end_line = int(sel_end.split('.')[0])
        
        text_widget.tag_remove("sel", "1.0", "end")
        
        for line in range(start_line, end_line + 1):
            text_widget.insert(f"{line}.0", self.get_indent_string())
        
        text_widget.tag_add("sel", f"{start_line}.0", f"{end_line + 1}.0")
        return 'break'

    def unindent_selected_lines(self, text_widget, sel_start, sel_end):
        start_line = int(sel_start.split('.')[0])
        end_line = int(sel_end.split('.')[0])
        
        text_widget.tag_remove("sel", "1.0", "end")
        
        for line in range(start_line, end_line + 1):
            line_content = text_widget.get(f"{line}.0", f"{line}.end")
            if line_content.startswith(self.get_indent_string()):
                text_widget.delete(f"{line}.0", f"{line}.{len(self.get_indent_string())}")
            elif line_content.startswith('\t'):
                text_widget.delete(f"{line}.0", f"{line}.1")
            elif line_content.startswith(' '):
                # Remove up to 4 spaces (or whatever the tab width is)
                spaces_to_remove = min(len(line_content) - len(line_content.lstrip()), self.tab_width.get())
                text_widget.delete(f"{line}.0", f"{line}.{spaces_to_remove}")
        
        text_widget.tag_add("sel", f"{start_line}.0", f"{end_line + 1}.0")
        return 'break'

    def update_dir_listing(self):
        self.dir_listbox.delete(0, tk.END)
        self.dir_listbox.insert(tk.END, '..')
        for item in sorted(os.listdir(self.current_dir)):
            self.dir_listbox.insert(tk.END, item)

    def process_query(self, event=None):
        query = self.query_entry.get().strip()
        
        if query.startswith(':'):
            command = query[1:].lower().split()
            
            if not command:
                messagebox.showerror("Error", "Please enter a command after ':'.")
                return
            
            if command[0] == 'q':
                self.close_current_tab()
            elif command[0] == 's':
                self.save_current_file()
            elif command[0] == 'sq':
                self.save_current_file()
                self.close_current_tab()
            elif command[0] == 'new' and len(command) > 1:
                self.create_new_file(' '.join(command[1:]))
            elif command[0] == 'newd' and len(command) > 1:
                self.create_new_directory(' '.join(command[1:]))
            elif command[0] == 'del' and len(command) > 1:
                self.delete_item(' '.join(command[1:]))
            elif command[0] == 're' and len(command) > 1:
                self.rename_item(' '.join(command[1:]))
            elif command[0] == 'copy' and len(command) > 1:
                self.copy_item(' '.join(command[1:]))
            elif command[0] == 'move' and len(command) > 1:
                self.move_item(' '.join(command[1:]))
            elif command[0] == 'info' and len(command) > 1:
                self.show_item_info(' '.join(command[1:]))
            elif command[0] == 'f' and len(command) > 1:
                self.word_to_find = ' '.join(command[1:])
                self.current_search_position = '1.0'
                self.highlight_occurrences()
            elif command[0] == 'fr':
                self.find_and_replace()
            elif command[0] == 'fs' and len(command) > 1:
                self.change_font_size(command[1])
            elif command[0] == 'cmd':
                self.open_command_prompt()
            else:
                messagebox.showerror("Error", f"Unknown command: {query}")
        else:
            self.navigate_or_open(query)
        self.query_entry.delete(0, tk.END)

    def change_font_size(self, size):
        try:
            new_size = int(size)
            if new_size < 8 or new_size > 72:
                messagebox.showerror("Error", "Font size must be between 8 and 72.")
                return
            self.font_size = new_size
            self.editor_font = ('Courier', self.font_size)
            self.update_all_text_widgets()
            messagebox.showinfo("Font Size", f"Font size changed to {new_size}.")
        except ValueError:
            messagebox.showerror("Error", "Invalid font size. Please enter a number between 8 and 72.")

    def update_all_text_widgets(self):
        for tab in self.notebook.tabs():
            tab_widget = self.notebook.nametowidget(tab)
            text_frame = tab_widget.winfo_children()[0]
            for child in text_frame.winfo_children():
                if isinstance(child, tk.Text):
                    child.configure(font=self.editor_font)
        self.update_line_numbers()  # Ensure line numbers are updated with new font

    def show_find_dialog(self, count):
        if self.find_window:
            self.find_window.destroy()  # Destroy existing window if it exists
        
        self.find_window = tk.Toplevel(self.root)
        self.find_window.title("Find")
        self.find_window.geometry("300x100")
        self.find_window.resizable(False, False)
        
        label = tk.Label(self.find_window, text=f"Found {count} occurrences of '{self.word_to_find}'.")
        label.pack(pady=10)

        find_next_button = tk.Button(self.find_window, text="Find Next", command=self.simple_find_next)
        find_next_button.pack(pady=10)

        # Bind the Enter key to the simple_find_next method
        self.find_window.bind('<Return>', lambda event: self.simple_find_next())

        # Keep the Find Next window on top
        self.find_window.attributes('-topmost', True)

        # Bind the closing of the window to remove highlights
        self.find_window.protocol("WM_DELETE_WINDOW", self.on_find_window_close)

    def on_find_window_close(self):
        self.remove_highlights()
        self.find_window.destroy()
        self.find_window = None

    def remove_highlights(self, text_widget=None):
        if text_widget is None:
            current_tab = self.notebook.nametowidget(self.notebook.select())
            text_widget = self.get_text_widget(current_tab)
            if text_widget is None:
                return

        text_widget.tag_remove(self.highlight_tag, '1.0', tk.END)
        text_widget.tag_remove(self.current_highlight_tag, '1.0', tk.END)

    def simple_find_next(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if text_widget is None:
            messagebox.showerror("Error", "Cannot find text widget in the current tab.")
            return

        # Remove previous current highlight
        text_widget.tag_remove(self.current_highlight_tag, '1.0', tk.END)

        start_pos = text_widget.search(self.word_to_find, self.current_search_position, stopindex=tk.END, nocase=True)
        
        if not start_pos:
            start_pos = text_widget.search(self.word_to_find, '1.0', stopindex=tk.END, nocase=True)
            if not start_pos:
                messagebox.showinfo("Find", f"Reached the end of the document. No more occurrences of '{self.word_to_find}' found.")
                self.current_search_position = '1.0'  # Reset to the beginning for the next search
                return

        end_pos = f"{start_pos}+{len(self.word_to_find)}c"
        
        # Highlight the current occurrence
        text_widget.tag_add(self.current_highlight_tag, start_pos, end_pos)
        text_widget.see(start_pos)

        # Update the current search position for the next search
        self.current_search_position = end_pos

        # Bring the Find Next window back to focus
        if self.find_window:
            self.find_window.focus_force()

    def find_and_replace(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if text_widget is None:
            messagebox.showerror("Error", "No file is currently open.")
            return

        # Create a new top-level window if it doesn't exist
        if not self.find_replace_window or not self.find_replace_window.winfo_exists():
            self.find_replace_window = tk.Toplevel(self.root)
            self.find_replace_window.title("Find and Replace")
            self.find_replace_window.geometry("600x200")

            # Find entry
            tk.Label(self.find_replace_window, text="Find:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.find_entry = tk.Entry(self.find_replace_window, width=30)
            self.find_entry.grid(row=0, column=1, padx=5, pady=5)
            self.find_entry.bind('<KeyRelease>', self.highlight_all_occurrences)

            # Replace entry
            tk.Label(self.find_replace_window, text="Replace with:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.replace_entry = tk.Entry(self.find_replace_window, width=30)
            self.replace_entry.grid(row=1, column=1, padx=5, pady=5)

            # Case sensitive checkbox
            self.case_sensitive_checkbox = tk.Checkbutton(self.find_replace_window, text="Case sensitive", 
                                                          variable=self.case_sensitive_var, 
                                                          command=self.highlight_all_occurrences)
            self.case_sensitive_checkbox.grid(row=2, column=0, columnspan=2, pady=5)

            # Buttons
            tk.Button(self.find_replace_window, text="Find Next", command=self.advanced_find_next).grid(row=3, column=0, padx=5, pady=5)
            tk.Button(self.find_replace_window, text="Replace", command=self.replace).grid(row=3, column=1, padx=5, pady=5)
            tk.Button(self.find_replace_window, text="Replace All", command=self.replace_all).grid(row=3, column=2, padx=5, pady=5)

            # Bind the closing of the window to remove highlights
            self.find_replace_window.protocol("WM_DELETE_WINDOW", self.on_find_replace_close)

    def highlight_all_occurrences(self, event=None):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if not text_widget:
            return

        find_text = self.find_entry.get()
        if not find_text:
            self.clear_all_highlights(text_widget)
            return

        # Remove any existing highlights
        self.clear_all_highlights(text_widget)

        # Configure tags for highlighting
        text_widget.tag_configure(self.highlight_tag, background='yellow', foreground='black')
        text_widget.tag_configure(self.current_highlight_tag, background='orange', foreground='black')

        # Find and highlight all occurrences
        start_pos = '1.0'
        while True:
            start_pos = text_widget.search(find_text, start_pos, stopindex=tk.END, 
                                           nocase=not self.case_sensitive_var.get())
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(find_text)}c"
            text_widget.tag_add(self.highlight_tag, start_pos, end_pos)
            start_pos = end_pos

        self.current_search_position = '1.0'
        self.word_to_find = find_text
        self.advanced_find_next()

    def advanced_find_next(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if text_widget is None:
            messagebox.showerror("Error", "Cannot find text widget in the current tab.")
            return

        # Remove previous current highlight
        text_widget.tag_remove(self.current_highlight_tag, '1.0', tk.END)

        start_pos = text_widget.search(self.word_to_find, self.current_search_position, 
                                       stopindex=tk.END, nocase=not self.case_sensitive_var.get())
        
        if not start_pos:
            start_pos = text_widget.search(self.word_to_find, '1.0', 
                                           stopindex=tk.END, nocase=not self.case_sensitive_var.get())
            if not start_pos:
                messagebox.showinfo("Find", f"Reached the end of the document. No more occurrences of '{self.word_to_find}' found.")
                self.current_search_position = '1.0'  # Reset to the beginning for the next search
                if self.find_replace_window:
                    self.find_replace_window.focus_force()
                    self.find_entry.focus_set()
                return

        end_pos = f"{start_pos}+{len(self.word_to_find)}c"
        
        # Highlight the current occurrence
        text_widget.tag_add(self.current_highlight_tag, start_pos, end_pos)
        text_widget.see(start_pos)

        # Update the current search position for the next search
        self.current_search_position = end_pos

        # Bring the Find Next window back to focus
        if self.find_replace_window:
            self.find_replace_window.focus_force()
            self.find_entry.focus_set()

    def replace(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if text_widget is None:
            return

        replace_text = self.replace_entry.get()

        # Check if there's a current highlight
        ranges = text_widget.tag_ranges(self.current_highlight_tag)
        if ranges:
            start, end = ranges[0], ranges[1]
            text_widget.delete(start, end)
            text_widget.insert(start, replace_text)
            
            # Remove only the current (orange) highlight
            text_widget.tag_remove(self.current_highlight_tag, start, text_widget.index(f"{start}+{len(replace_text)}c"))
            
            # Update the yellow highlight to cover the new replaced text
            text_widget.tag_add(self.highlight_tag, start, text_widget.index(f"{start}+{len(replace_text)}c"))
            
            self.current_search_position = text_widget.index(f"{start}+{len(replace_text)}c")
        
        # Find and highlight the next occurrence
        self.advanced_find_next()

        # If no more occurrences are found, remove all highlights
        if not text_widget.tag_ranges(self.current_highlight_tag):
            self.clear_all_highlights(text_widget)
            messagebox.showinfo("Find and Replace", "No more occurrences found. All highlights cleared.")
            if self.find_replace_window:
                self.find_replace_window.focus_force()
                self.find_entry.focus_set()

    def replace_all(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if text_widget is None:
            return

        find_text = self.find_entry.get()
        replace_text = self.replace_entry.get()

        content = text_widget.get('1.0', tk.END)
        if self.case_sensitive_var.get():
            new_content, count = re.subn(re.escape(find_text), replace_text, content)
        else:
            new_content, count = re.subn(re.escape(find_text), replace_text, content, flags=re.IGNORECASE)
        
        if count > 0:
            text_widget.delete('1.0', tk.END)
            text_widget.insert('1.0', new_content)
            self.clear_all_highlights(text_widget)
            messagebox.showinfo("Replace All", f"Replaced {count} occurrence(s).")
        else:
            messagebox.showinfo("Replace All", f"No occurrences of '{find_text}' found.")
        
        if self.find_replace_window:
            self.find_replace_window.focus_force()
            self.find_entry.focus_set()

    def on_find_replace_close(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if text_widget:
            self.clear_all_highlights(text_widget)
        self.find_replace_window.destroy()
        self.find_replace_window = None

    def clear_all_highlights(self, text_widget):
        text_widget.tag_remove(self.highlight_tag, '1.0', tk.END)
        text_widget.tag_remove(self.current_highlight_tag, '1.0', tk.END)

    def get_current_text_widget(self):
        current_tab = self.notebook.select()
        if not current_tab:
            messagebox.showerror("Error", "No file is currently open.")
            return None
        return self.get_text_widget(self.notebook.nametowidget(current_tab))

    def highlight_occurrences(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if text_widget is None:
            messagebox.showerror("Error", "Cannot find text widget in the current tab.")
            return
        
        # Remove any existing highlights
        self.remove_highlights(text_widget)

        # Configure tags for highlighting
        text_widget.tag_configure(self.highlight_tag, background='yellow', foreground='black')
        text_widget.tag_configure(self.current_highlight_tag, background='orange', foreground='black')

        count = 0
        start_pos = '1.0'
        while True:
            start_pos = text_widget.search(self.word_to_find, start_pos, stopindex=tk.END, nocase=True)
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(self.word_to_find)}c"
            text_widget.tag_add(self.highlight_tag, start_pos, end_pos)
            count += 1
            start_pos = end_pos

        if count > 0:
            self.current_search_position = '1.0'  # Reset search position
            self.show_find_dialog(count)
            self.simple_find_next()  # Highlight the first occurrence
        else:
            messagebox.showinfo("Find", f"No occurrences of '{self.word_to_find}' found.")



    def show_item_info(self, item_name):
        item_path = os.path.join(self.current_dir, item_name)
        if not os.path.exists(item_path):
            messagebox.showerror("Error", f"The file or directory '{item_name}' does not exist.")
            return

        try:
            stat_info = os.stat(item_path)
            
            # Get file/directory information
            name = os.path.basename(item_path)
            full_path = os.path.abspath(item_path)
            size_kb = stat_info.st_size / 1024  # Convert bytes to KB
            created = datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            modified = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            accessed = datetime.datetime.fromtimestamp(stat_info.st_atime).strftime("%Y-%m-%d %H:%M:%S")

            # Prepare info message
            info_message = f"Name: {name}\n"
            info_message += f"Type: {'Directory' if os.path.isdir(item_path) else 'File'}\n"
            info_message += f"Size: {size_kb:.2f} KB\n"
            info_message += f"Full Path: {full_path}\n"
            info_message += f"Created: {created}\n"
            info_message += f"Modified: {modified}\n"
            info_message += f"Last Accessed: {accessed}"

            # Show info in a message box
            messagebox.showinfo(f"Info: {name}", info_message)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to get info for '{item_name}': {str(e)}")

    def copy_item(self, command):
        try:
            source, destination = command.split(' -> ')
            source = source.strip()
            destination = destination.strip()
        except ValueError:
            messagebox.showerror("Error", "Invalid copy command. Use format: :copy source -> destination")
            return

        source_path = os.path.abspath(os.path.join(self.current_dir, source))
        dest_path = os.path.abspath(os.path.join(self.current_dir, destination))

        if not os.path.exists(source_path):
            messagebox.showerror("Error", f"The source '{source}' does not exist.")
            return

        if os.path.exists(dest_path):
            messagebox.showerror("Error", f"The destination '{destination}' already exists.")
            return

        try:
            if os.path.isfile(source_path):
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(source_path, dest_path)
                messagebox.showinfo("Success", f"File '{source}' has been copied to '{destination}'.")
            elif os.path.isdir(source_path):
                shutil.copytree(source_path, dest_path)
                messagebox.showinfo("Success", f"Directory '{source}' and its contents have been copied to '{destination}'.")

            self.update_dir_listing()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy '{source}' to '{destination}': {str(e)}")

    def move_item(self, command):
        try:
            source, destination = command.split(' -> ')
            source = source.strip()
            destination = destination.strip()
        except ValueError:
            messagebox.showerror("Error", "Invalid move command. Use format: :move source -> destination")
            return

        source_path = os.path.abspath(os.path.join(self.current_dir, source))
        dest_path = os.path.abspath(os.path.join(self.current_dir, destination))

        if not os.path.exists(source_path):
            messagebox.showerror("Error", f"The source '{source}' does not exist.")
            return

        if os.path.exists(dest_path) and not os.path.isdir(dest_path):
            messagebox.showerror("Error", f"The destination '{destination}' is not a directory.")
            return

        try:
            # If destination is a directory, we want to move the source into it
            if os.path.isdir(dest_path):
                dest_path = os.path.join(dest_path, os.path.basename(source_path))
            
            # Create the destination directory if it doesn't exist
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # Perform the move operation
            shutil.move(source_path, dest_path)
            
            messagebox.showinfo("Success", f"'{source}' has been moved to '{destination}'.")
            
            # Update any open tabs if the moved file is currently open
            for tab in self.notebook.tabs():
                if self.notebook.tab(tab, "text") == os.path.basename(source_path):
                    self.notebook.tab(tab, text=os.path.basename(dest_path))
                    # Update the file path in the text widget if you're storing it
                    text_widget = self.notebook.nametowidget(tab).winfo_children()[0]
                    if hasattr(text_widget, 'file_path'):
                        text_widget.file_path = dest_path
                    break
            
            self.update_dir_listing()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move '{source}' to '{destination}': {str(e)}")

    def rename_item(self, command):
        try:
            old_name, new_name = command.split(' -> ')
            old_name = old_name.strip()
            new_name = new_name.strip()
        except ValueError:
            messagebox.showerror("Error", "Invalid rename command. Use format: :re oldname -> newname")
            return

        old_path = os.path.join(self.current_dir, old_name)
        new_path = os.path.join(self.current_dir, new_name)

        if not os.path.exists(old_path):
            messagebox.showerror("Error", f"The file or directory '{old_name}' does not exist.")
            return

        if os.path.exists(new_path):
            messagebox.showerror("Error", f"A file or directory named '{new_name}' already exists.")
            return

        try:
            os.rename(old_path, new_path)
            messagebox.showinfo("Success", f"'{old_name}' has been renamed to '{new_name}'.")
            self.update_dir_listing()

            # If the renamed item is currently open in a tab, update the tab name
            for tab in self.notebook.tabs():
                if self.notebook.tab(tab, "text") == old_name:
                    self.notebook.tab(tab, text=new_name)
                    break

        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename '{old_name}': {str(e)}")
        
    def delete_item(self, item_name):
        item_path = os.path.join(self.current_dir, item_name)
        if not os.path.exists(item_path):
            messagebox.showerror("Error", f"The file or directory '{item_name}' does not exist.")
            return

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{item_name}'?")
        if confirm:
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    messagebox.showinfo("Success", f"File '{item_name}' has been deleted.")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    messagebox.showinfo("Success", f"Directory '{item_name}' and its contents have been deleted.")
                self.update_dir_listing()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete '{item_name}': {str(e)}")

    def navigate_or_open(self, path):
        if path == '..':
            self.current_dir = os.path.dirname(self.current_dir)
            self.update_dir_listing()
        else:
            full_path = os.path.join(self.current_dir, path)
            if os.path.isdir(full_path):
                self.current_dir = full_path
                self.update_dir_listing()
            elif os.path.isfile(full_path):
                self.open_file(path)
            else:
                messagebox.showerror("Error", f"The file or directory '{path}' does not exist.")

    def create_new_directory(self, dir_name):
        dir_path = os.path.join(self.current_dir, dir_name)
        if os.path.exists(dir_path):
            messagebox.showerror("Error", f"The directory '{dir_name}' already exists.")
        else:
            os.mkdir(dir_path)
            self.update_dir_listing()

    def open_file(self, file_name):
        file_path = os.path.join(self.current_dir, file_name)
        
        # Check if the file is already open in a tab
        for tab in self.notebook.tabs():
            tab_widget = self.notebook.nametowidget(tab)
            tab_text = self.notebook.tab(tab, "text")
            tab_path = getattr(tab_widget, 'file_path', None)
            
            if tab_path and os.path.exists(file_path) and os.path.exists(tab_path):
                try:
                    if os.path.samefile(tab_path, file_path):
                        self.notebook.select(tab)
                        return
                except FileNotFoundError:
                    # If either file doesn't exist, just compare the paths
                    if tab_path == file_path:
                        self.notebook.select(tab)
                        return
            elif tab_text == file_name:
                self.notebook.select(tab)
                return

        # If we're here, the file isn't already open, so create a new tab
        tab = ttk.Frame(self.notebook)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        # Create a frame to hold the text widget, line numbers, and scrollbars
        text_frame = ttk.Frame(tab)
        text_frame.grid(row=0, column=0, sticky="nsew")
        text_frame.grid_columnconfigure(1, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        # Create a text widget for line numbers
        line_numbers = tk.Text(text_frame, width=4, padx=4, takefocus=0, border=0,
                               background=self.bg_color, foreground='gray',
                               state='disabled', wrap='none', font=self.editor_font)
        line_numbers.grid(row=0, column=0, sticky="nsew")

        # Create the main text widget
        text_area = tk.Text(text_frame, bg=self.bg_color, fg=self.fg_color,
                            insertbackground=self.fg_color,
                            font=('Courier', self.font_size), wrap='none')
        text_area.grid(row=0, column=1, sticky="nsew")

        # Create vertical scrollbar for text widget
        v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.on_scrollbar_y)
        v_scrollbar.grid(row=0, column=2, sticky="ns")
        text_area.config(yscrollcommand=v_scrollbar.set)

        # Create horizontal scrollbar for text widget
        h_scrollbar = ttk.Scrollbar(tab, orient="horizontal", command=text_area.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        text_area.config(xscrollcommand=h_scrollbar.set)

        # If the file exists, read its contents
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
                    text_area.insert(tk.END, content)
            except:
                messagebox.showerror("Error", f"Error reading file.")
                return
            else:
                pass
        
        # Add the tab to the notebook
        self.notebook.add(tab, text=file_name)
    
        # Initialize saved state
        self.unsaved_changes[tab] = False

        # Store the full file path and widgets in the tab
        tab.file_path = file_path
        tab.text_area = text_area
        tab.line_numbers = line_numbers

        # Switch to the new tab
        self.notebook.select(tab)
        
        # Set focus to the text area and move cursor to the end
        text_area.focus_set()
        text_area.mark_set(tk.INSERT, tk.END)
        
        # Bind events
        text_area.bind('<KeyRelease>', self.on_text_change)
        text_area.bind('<Return>', lambda e: self.auto_indent(e))
        text_area.bind('<Tab>', self.handle_tab)
        text_area.bind('<Shift-Tab>', self.handle_shift_tab)
        text_area.bind('<Control-n>', self.handle_autocomplete)
        text_area.bind('<<Change>>', self.on_text_change)
        text_area.bind('<Configure>', self.on_text_change)

        self.update_line_numbers()

        # Ensure the text widget is editable
        text_area.config(state=tk.NORMAL)

    def on_scrollbar_y(self, *args):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_area = self.get_text_widget(current_tab)
        line_numbers = getattr(current_tab, 'line_numbers', None)
        
        if text_area and line_numbers:
            text_area.yview_moveto(args[1])
            line_numbers.yview_moveto(args[1])

    def on_text_change(self, event=None):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if text_widget:
            self.update_line_numbers()
            if not self.unsaved_changes.get(current_tab, False):
                self.unsaved_changes[current_tab] = True
                self.update_tab_title(current_tab)

    def update_tab_title(self, tab):
        current_title = self.notebook.tab(tab, "text")
        if self.unsaved_changes.get(tab, False) and not current_title.endswith('*'):
            self.notebook.tab(tab, text=current_title + '*')
        elif not self.unsaved_changes.get(tab, False) and current_title.endswith('*'):
            self.notebook.tab(tab, text=current_title[:-1])

    def update_line_numbers(self):
        if not self.line_numbers_enabled:
            return
        
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        line_numbers = getattr(current_tab, 'line_numbers', None)
        
        if not text_widget or not line_numbers:
            return

        # Get the total number of lines in the text widget
        total_lines = text_widget.get('1.0', tk.END).count('\n')

        # Generate line numbers
        line_numbers_text = '\n'.join(str(i) for i in range(1, total_lines + 1))

        # Update line numbers
        line_numbers.config(state='normal', font=self.editor_font)
        line_numbers.delete('1.0', tk.END)
        line_numbers.insert('1.0', line_numbers_text)
        line_numbers.config(state='disabled')

        # Update the width of line numbers widget based on the number of lines
        width = len(str(total_lines))
        line_numbers.config(width=width + 1)  # +1 for some padding

    def create_new_file(self, file_name):
        file_path = os.path.join(self.current_dir, file_name)
        if os.path.exists(file_path):
            messagebox.showerror("Error", f"The file '{file_name}' already exists.")
        else:
            # Don't create the file immediately, just open a new tab
            self.open_file(file_name)
            
        current_tab = self.notebook.nametowidget(self.notebook.select())
        text_widget = self.get_text_widget(current_tab)
        if text_widget:
            text_widget.bind('<Return>', lambda e: self.auto_indent(e))
            text_widget.bind('<Tab>', self.handle_tab)
            text_widget.bind('<Shift-Tab>', self.handle_shift_tab)
            text_widget.bind('<Control-n>', self.handle_autocomplete)
        
        self.unsaved_changes[current_tab] = False
        self.update_tab_title(current_tab)
            
    def get_text_widget(self, tab):
        return getattr(tab, 'text_area', None)

    def save_current_file(self):
        current_tab = self.notebook.nametowidget(self.notebook.select())
        tab_name = self.notebook.tab(current_tab, "text")
        text_widget = self.get_text_widget(current_tab)
        if text_widget is None:
            messagebox.showerror("Error", "Cannot find text widget in the current tab.")
            return
            
        content = text_widget.get("1.0", tk.END)

        if tab_name.startswith("Untitled"):
            file_name = simpledialog.askstring("Save As", "Enter file name:")
            if file_name:
                file_path = os.path.join(self.current_dir, file_name)
                with open(file_path, 'w') as file:
                    file.write(content)
                self.update_dir_listing()
                if self.notebook.index('end') > 1:
                    self.notebook.forget(current_tab)
                else:
                    self.notebook.tab(current_tab, text=file_name)
                    current_tab.file_path = file_path
                self.unsaved_changes[current_tab] = False
                self.update_tab_title(current_tab)
            else:
                return
        else:
            file_path = getattr(current_tab, 'file_path', os.path.join(self.current_dir, tab_name.rstrip('*')))
            with open(file_path, 'w') as file:
                file.write(content)
            self.update_dir_listing()
            self.unsaved_changes[current_tab] = False
            self.update_tab_title(current_tab)

    def close_current_tab(self):
        current_tab = self.notebook.select()
        if self.unsaved_changes.get(self.notebook.nametowidget(current_tab), False):
            if not messagebox.askyesno("Unsaved Changes", "There are unsaved changes. Do you want to close without saving?"):
                return
        
        if self.notebook.index('end') > 1:
            self.notebook.forget(current_tab)
            del self.unsaved_changes[self.notebook.nametowidget(current_tab)]
        else:
            current_tab = self.notebook.nametowidget(current_tab)
            text_widget = self.get_text_widget(current_tab)
            if text_widget is not None:
                text_widget.delete('1.0', tk.END)
            self.notebook.tab(current_tab, text="Untitled-1")
            current_tab.file_path = None
            self.unsaved_changes[current_tab] = False
            self.update_tab_title(current_tab)

    def open_selected_file(self, event):
        selection = self.dir_listbox.curselection()
        if selection:
            item = self.dir_listbox.get(selection[0])
            self.navigate_or_open(item)

    def update_suggestions(self, event=None):
        query = self.query_entry.get().strip()
        suggestions = []

        if query.startswith(':copy ') or query.startswith(':move '):
            parts = query.split()
            if len(parts) > 2 and parts[-2] == '->':
                # We're dealing with a destination path
                path = ' '.join(parts[3:])
                suggestions = self.get_path_suggestions(path)
            elif len(parts) == 2:
                # We're dealing with a source path
                suggestions = self.get_path_suggestions(parts[1])
        elif query.startswith(':del ') or query.startswith(':info ') or query.startswith(':re '):
            parts = query.split()
            if len(parts) == 2:
                # Suggest files and directories in the current directory
                partial_name = parts[1].lower()
                suggestions = [item for item in os.listdir(self.current_dir) 
                               if item.lower().startswith(partial_name)]
        else:
            # For all other cases, show suggestions from the current directory
            all_items = ['..' if item == '..' else item for item in os.listdir(self.current_dir)]
            suggestions = [item for item in all_items if item.lower().startswith(query.lower())]

        self.suggestion_listbox.delete(0, tk.END)
        for suggestion in suggestions[:10]:  # Limit to top 10 suggestions
            self.suggestion_listbox.insert(tk.END, suggestion)

    def get_path_suggestions(self, path):
        if os.path.isabs(path):
            base_path = os.path.dirname(path)
            prefix = os.path.basename(path)
        else:
            base_path = os.path.join(self.current_dir, os.path.dirname(path))
            prefix = os.path.basename(path)

        try:
            items = os.listdir(base_path)
        except FileNotFoundError:
            return []

        suggestions = [os.path.join(base_path, item) for item in items if item.startswith(prefix)]
        return suggestions

    def autofill_suggestion(self, event):
        query = self.query_entry.get().strip()
        if query.startswith(':copy ') or query.startswith(':move '):
            parts = query.split()
            if len(parts) > 2 and parts[-2] == '->':
                # We're dealing with a destination path
                path = ' '.join(parts[3:])
                suggestions = self.get_path_suggestions(path)
                if suggestions:
                    common_prefix = os.path.commonprefix(suggestions)
                    if common_prefix:
                        new_query = ' '.join(parts[:3] + [common_prefix])
                        self.query_entry.delete(0, tk.END)
                        self.query_entry.insert(0, new_query)
            elif len(parts) == 2:
                # We're dealing with a source path
                suggestions = self.get_path_suggestions(parts[1])
                if suggestions:
                    common_prefix = os.path.commonprefix(suggestions)
                    if common_prefix:
                        new_query = f"{parts[0]} {common_prefix}"
                        self.query_entry.delete(0, tk.END)
                        self.query_entry.insert(0, new_query)
        elif query.startswith(':del ') or query.startswith(':info ') or query.startswith(':re '):
            parts = query.split()
            if len(parts) == 2:
                partial_name = parts[1].lower()
                suggestions = [item for item in os.listdir(self.current_dir) 
                               if item.lower().startswith(partial_name)]
                if suggestions:
                    best_match = suggestions[0]  # Use the first match
                    new_query = f"{parts[0]} {best_match}"
                    self.query_entry.delete(0, tk.END)
                    self.query_entry.insert(0, new_query)
        else:
            # Handle other types of queries
            suggestions = self.suggestion_listbox.get(0, tk.END)
            if suggestions:
                best_match = next((s for s in suggestions if s.lower().startswith(query.lower())), None)
                if best_match:
                    self.query_entry.delete(0, tk.END)
                    self.query_entry.insert(0, best_match)
        
        self.query_entry.icursor(tk.END)  # Move cursor to end of entry
        self.query_entry.xview_moveto(1)  # Scroll to the end
        return 'break'  # Prevent default Tab behavior

    def use_suggestion(self, event):
        selection = self.suggestion_listbox.curselection()
        if selection:
            suggestion = self.suggestion_listbox.get(selection[0])
            self.query_entry.delete(0, tk.END)
            self.query_entry.insert(0, suggestion)
            self.process_query()

def main():
    root = tk.Tk()
    editor = TextEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
