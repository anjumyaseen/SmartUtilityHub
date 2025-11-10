import os
import fnmatch
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import threading
import subprocess
import platform



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

        ttk.Button(frm_top, text="Clear Folders", bootstyle="secondary-outline", command=self.clear_folders).pack(
            side=LEFT, padx=5
        )

        self.entry_query = ttk.Entry(frm_top, width=40)
        self.entry_query.pack(side=LEFT, padx=5)
        self.entry_query.insert(0, "Enter filename or keyword")

        self.btn_search = ttk.Button(frm_top, text="Search", bootstyle="success", command=self.start_search)
        self.btn_search.pack(side=LEFT, padx=5)

        frm_filters = ttk.Frame(self)
        frm_filters.pack(pady=5)

        ttk.Label(frm_filters, text="Filter by type:").pack(side=LEFT, padx=5)
        self.file_type = ttk.Combobox(
            frm_filters,
            values=["All", ".pdf", ".docx", ".xlsx", ".txt", ".png", ".jpg"],
            state="readonly",
            width=10,
        )
        self.file_type.set("All")
        self.file_type.pack(side=LEFT, padx=5)

        self.var_recursive = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm_filters, text="Search subfolders", variable=self.var_recursive).pack(side=LEFT, padx=10)

        frm_limits = ttk.Frame(self)
        frm_limits.pack(fill=X, padx=10, pady=5)

        ttk.Label(frm_limits, text="Max depth:").pack(side=LEFT)
        self.max_depth_var = tk.StringVar(value="")
        ttk.Entry(frm_limits, textvariable=self.max_depth_var, width=6).pack(side=LEFT, padx=5)

        ttk.Label(frm_limits, text="Exclude:").pack(side=LEFT, padx=5)
        self.var_exclude_git = tk.BooleanVar(value=True)
        self.var_exclude_node = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm_limits, text=".git", variable=self.var_exclude_git).pack(side=LEFT)
        ttk.Checkbutton(frm_limits, text="node_modules", variable=self.var_exclude_node).pack(side=LEFT, padx=5)

        self.exclude_dirs_var = tk.StringVar(value="")
        ttk.Entry(frm_limits, textvariable=self.exclude_dirs_var, width=25).pack(side=LEFT, padx=5)

        self.lbl_selected = ttk.Label(self, text="No folders selected", bootstyle="secondary")
        self.lbl_selected.pack(fill=X, padx=10, pady=5)

        self.lbl_status = ttk.Label(self, text="Ready", bootstyle="secondary")
        self.lbl_status.pack(fill=X, padx=10)

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
            self._update_selected_label()

    def clear_folders(self):
        if self.folder_paths:
            self.folder_paths.clear()
            self._update_selected_label()
            self.lbl_status.config(text="Cleared selected folders.")

    def _update_selected_label(self):
        if not self.folder_paths:
            text = "No folders selected"
        else:
            text = "Folders: " + "; ".join(self.folder_paths)
        self.lbl_selected.config(text=text)

    def start_search(self):
        query = self.entry_query.get().strip()
        if not self.folder_paths or not query:
            messagebox.showwarning("Input Missing", "Please select folder(s) and enter search term.")
            return
        self.lbl_status.config(text="Searching...")
        threading.Thread(target=self.search_files, args=(query,), daemon=True).start()

    def search_files(self, query):
        self.result_list.delete(0, tk.END)
        self.progress.start()
        count = 0
        selected_ext = self.file_type.get().lower()
        has_wildcard = any(ch in query for ch in "*?")
        lowered_query = query.lower()
        max_depth = self._get_max_depth()
        excluded_dirs = self._get_excluded_dirs()

        for folder in self.folder_paths:
            if self.var_recursive.get():
                walker = self._limited_walk(folder, max_depth, excluded_dirs)
            else:
                files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
                walker = [(folder, [], files)]

            for root, _, files in walker:
                for f in files:
                    file_lower = f.lower()
                    if has_wildcard:
                        match = fnmatch.fnmatch(file_lower, lowered_query)
                    else:
                        match = lowered_query in file_lower
                    if not match:
                        continue
                    if selected_ext != "all" and not file_lower.endswith(selected_ext):
                        continue
                    full_path = os.path.join(root, f)
                    self.result_list.insert(tk.END, full_path)
                    count += 1

        self.progress.stop()
        self.lbl_status.config(text=f"Completed search in {len(self.folder_paths)} folder(s).")
        self._update_selected_label()
        messagebox.showinfo("Search Complete", f"Found {count} matching files.")

    def _limited_walk(self, root_folder, max_depth, excluded_dirs):
        for current_root, dirs, files in os.walk(root_folder):
            rel = os.path.relpath(current_root, root_folder)
            depth = 0 if rel == "." else rel.count(os.sep)

            if excluded_dirs:
                dirs[:] = [d for d in dirs if d.lower() not in excluded_dirs]

            if max_depth is not None and depth >= max_depth:
                dirs[:] = []

            yield current_root, dirs, files

    def _get_max_depth(self):
        value = self.max_depth_var.get().strip()
        if not value:
            return None
        try:
            depth = int(value)
            return depth if depth >= 0 else None
        except ValueError:
            return None

    def _get_excluded_dirs(self):
        excluded = set()
        if self.var_exclude_git.get():
            excluded.add(".git")
        if self.var_exclude_node.get():
            excluded.add("node_modules")
        raw = self.exclude_dirs_var.get().strip()
        if raw:
            excluded.update(part.strip().lower() for part in raw.split(",") if part.strip())
        return excluded

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
