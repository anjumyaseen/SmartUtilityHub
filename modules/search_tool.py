import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import threading
import subprocess
import platform
import darkdetect


class SearchTool(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.folder_paths = []
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="🔍 File Search", font=("Segoe UI", 12, "bold")).pack(pady=10)

        frm_top = ttk.Frame(self)
        frm_top.pack(pady=5)

        self.btn_choose = ttk.Button(frm_top, text="Choose Folder(s)", command=self.choose_folder)
        self.btn_choose.pack(side=LEFT, padx=5)

        self.entry_query = ttk.Entry(frm_top, width=40)
        self.entry_query.pack(side=LEFT, padx=5)
        self.entry_query.insert(0, "Enter filename or keyword")

        self.btn_search = ttk.Button(frm_top, text="Search", bootstyle="success", command=self.start_search)
        self.btn_search.pack(side=LEFT, padx=5)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill=X, padx=10, pady=5)

        self.result_list = tk.Listbox(self, font=("Consolas", 10))
        self.result_list.pack(fill=BOTH, expand=True, padx=10, pady=5)

        ttk.Button(self, text="Open Selected File", command=self.open_file).pack(side=LEFT, padx=10, pady=5)
        ttk.Button(self, text="Open Folder Location", command=self.open_folder).pack(side=LEFT, padx=10, pady=5)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.folder_paths.append(folder)
            messagebox.showinfo("Folder Added", f"Added: {folder}")

    def start_search(self):
        query = self.entry_query.get().strip()
        if not self.folder_paths or not query:
            messagebox.showwarning("Input Missing", "Please select folder(s) and enter search term.")
            return
        threading.Thread(target=self.search_files, args=(query,), daemon=True).start()

    def search_files(self, query):
        self.result_list.delete(0, tk.END)
        self.progress.start()
        count = 0
        for folder in self.folder_paths:
            for root, _, files in os.walk(folder):
                for f in files:
                    if query.lower() in f.lower():
                        full_path = os.path.join(root, f)
                        self.result_list.insert(tk.END, full_path)
                        count += 1
        self.progress.stop()
        messagebox.showinfo("Search Complete", f"Found {count} matching files.")

    def open_file(self):
        try:
            path = self.result_list.get(self.result_list.curselection())
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.call(["open", path])
        except:
            messagebox.showwarning("Select File", "Please select a file from the list.")

    def open_folder(self):
        try:
            path = self.result_list.get(self.result_list.curselection())
            folder = os.path.dirname(path)
            if platform.system() == "Windows":
                os.startfile(folder)
            else:
                subprocess.call(["open", folder])
        except:
            messagebox.showwarning("Select File", "Please select a file from the list.")
