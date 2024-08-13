import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os
import datetime
import shutil
import re

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("TEX-NAV")
        self.root.geometry("1200x600")

        # Configure dark mode colors
        self.bg_color = "#2E2E2E"  # Dark grey
        self.fg_color = "white"
        self.highlight_bg = "#4A4A4A"  # Lighter grey for highlights

        # Default font sizes
        self.editor_font_size = 12
        self.query_font_size = 12

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

        ttk.Label(suggestion_frame, text="Top 10 Suggestions", font=('Arial', 10, 'bold')).grid(row=0, column=0, pady=(0, 5), sticky="nw")
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
        ttk.Label(query_frame, text="Query:", font=('Arial', self.query_font_size)).grid(row=0, column=0, padx=(0, 5))

        # Query entry
        self.query_entry = ttk.Entry(query_frame, font=('Arial', self.query_font_size))
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
            self.update_all_text_widgets()
            messagebox.showinfo("Font Size", f"Font size changed to {new_size}.")
        except ValueError:
            messagebox.showerror("Error", "Invalid font size. Please enter a number between 8 and 72.")

    def update_all_text_widgets(self):
        for tab in self.notebook.tabs():
            text_frame = self.notebook.nametowidget(tab).winfo_children()[0]
            text_widget = [child for child in text_frame.winfo_children() if isinstance(child, tk.Text)][0]
            text_widget.configure(font=('Arial', self.font_size))

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
            current_tab = self.notebook.select()
            if not current_tab:
                return
            text_widget = self.get_text_widget(self.notebook.nametowidget(current_tab))
            if text_widget is None:
                return

        text_widget.tag_remove(self.highlight_tag, '1.0', tk.END)
        text_widget.tag_remove(self.current_highlight_tag, '1.0', tk.END)

    def simple_find_next(self):
        current_tab = self.notebook.select()
        if not current_tab:
            messagebox.showerror("Error", "No file is currently open.")
            return

        text_widget = self.get_text_widget(self.notebook.nametowidget(current_tab))
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
        current_tab = self.notebook.select()
        if not current_tab:
            messagebox.showerror("Error", "No file is currently open.")
            return

        text_widget = self.get_text_widget(self.notebook.nametowidget(current_tab))
        if text_widget is None:
            messagebox.showerror("Error", "Cannot find text widget in the current tab.")
            return

        # Create a new top-level window if it doesn't exist
        if not self.find_replace_window or not self.find_replace_window.winfo_exists():
            self.find_replace_window = tk.Toplevel(self.root)
            self.find_replace_window.title("Find and Replace")
            self.find_replace_window.geometry("300x180")

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
            tk.Button(self.find_replace_window, text="Replace All", command=self.replace_all).grid(row=4, column=0, columnspan=2, padx=5, pady=5)

            # Bind the closing of the window to remove highlights
            self.find_replace_window.protocol("WM_DELETE_WINDOW", self.on_find_replace_close)

    def highlight_all_occurrences(self, event=None):
        text_widget = self.get_current_text_widget()
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
        text_widget = self.get_current_text_widget()
        if not text_widget:
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
                    self.find_entry.delete(0, tk.END)
                return

        end_pos = f"{start_pos}+{len(self.word_to_find)}c"
        
        # Highlight the current occurrence
        text_widget.tag_add(self.current_highlight_tag, start_pos, end_pos)
        text_widget.see(start_pos)

        # Update the current search position for the next search
        self.current_search_position = end_pos

    def replace(self):
        text_widget = self.get_current_text_widget()
        if not text_widget:
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
            
            self.current_search_position = f"{start}+{len(replace_text)}c"
        
        # Find and highlight the next occurrence
        self.advanced_find_next()

        # If no more occurrences are found, remove all highlights
        if not text_widget.tag_ranges(self.current_highlight_tag):
            self.clear_all_highlights(text_widget)
            messagebox.showinfo("Find and Replace", "No more occurrences found. All highlights cleared.")
            if self.find_replace_window:
                self.find_replace_window.focus_force()
                self.find_entry.delete(0, tk.END)

    def replace_all(self):
        text_widget = self.get_current_text_widget()
        if not text_widget:
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
            self.find_entry.delete(0, tk.END)

    def on_find_replace_close(self):
        text_widget = self.get_current_text_widget()
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
        current_tab = self.notebook.select()
        if not current_tab:
            messagebox.showerror("Error", "No file is currently open.")
            return

        text_widget = self.get_text_widget(self.notebook.nametowidget(current_tab))
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
            
            if os.path.commonpath([self.current_dir, dest_path]) == self.current_dir:
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
            
            if os.path.commonpath([self.current_dir, source_path]) == self.current_dir or os.path.commonpath([self.current_dir, dest_path]) == self.current_dir:
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
            tab_text = self.notebook.tab(tab, "text")
            tab_path = os.path.join(self.current_dir, tab_text)
            if os.path.exists(file_path) and os.path.exists(tab_path):
                if os.path.samefile(file_path, tab_path):
                    # File is already open, just switch to that tab
                    self.notebook.select(tab)
                    return
            elif tab_text == file_name:
                # For new files, compare just the names
                self.notebook.select(tab)
                return

        # If we're here, the file isn't already open, so create a new tab
        tab = ttk.Frame(self.notebook)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        # Create a frame to hold the text widget and scrollbars
        text_frame = ttk.Frame(tab)
        text_frame.grid(row=0, column=0, sticky="nsew")
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        # Create a text widget in the tab with dark mode colors
        text_area = tk.Text(text_frame, bg=self.bg_color, fg=self.fg_color, insertbackground=self.fg_color, font=('Arial', self.editor_font_size), wrap='none')
        text_area.grid(row=0, column=0, sticky="nsew")

        # Create vertical scrollbar for text widget
        v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_area.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        text_area.config(yscrollcommand=v_scrollbar.set)

        # Create horizontal scrollbar for text widget
        h_scrollbar = ttk.Scrollbar(tab, orient="horizontal", command=text_area.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        text_area.config(xscrollcommand=h_scrollbar.set)

        # If the file exists, read its contents
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                text_area.insert(tk.END, content)
        
        # Add the tab to the notebook
        self.notebook.add(tab, text=file_name)

        # Store the full file path in the text widget
        text_area.file_path = file_path

        # Switch to the new tab
        self.notebook.select(tab)

    def create_new_file(self, file_name):
        file_path = os.path.join(self.current_dir, file_name)
        if os.path.exists(file_path):
            messagebox.showerror("Error", f"The file '{file_name}' already exists.")
        else:
            # Don't create the file immediately, just open a new tab
            self.open_file(file_name)
            
    def get_text_widget(self, tab):
        text_frame = tab.winfo_children()[0]
        for child in text_frame.winfo_children():
            if isinstance(child, tk.Text):
                return child
        return None

    def save_current_file(self):
        current_tab = self.notebook.select()
        tab_name = self.notebook.tab(current_tab, "text")
        text_widget = self.get_text_widget(self.notebook.nametowidget(current_tab))
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
            else:
                return
        else:
            file_path = os.path.join(self.current_dir, tab_name)
            with open(file_path, 'w') as file:
                file.write(content)
            self.update_dir_listing()

    def close_current_tab(self):
        if self.notebook.index('end') > 1:
            current_tab = self.notebook.select()
            self.notebook.forget(current_tab)
        else:
            current_tab = self.notebook.select()
            text_widget = self.get_text_widget(self.notebook.nametowidget(current_tab))
            if text_widget is not None:
                text_widget.delete('1.0', tk.END)
            self.notebook.tab(current_tab, text="Untitled-1")

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
