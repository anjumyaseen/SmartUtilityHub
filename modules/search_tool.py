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
        self.results = []
        self.result_display_count = 0
        self.folder_nodes = {}
        self.page_size = 50
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
        ttk.Label(frm_limits, text="(contains match, e.g. .git, logs, docker)").pack(side=LEFT, padx=5)

        self.lbl_selected = ttk.Label(self, text="No folders selected", bootstyle="secondary")
        self.lbl_selected.pack(fill=X, padx=10, pady=5)

        self.lbl_status = ttk.Label(self, text="Ready", bootstyle="secondary")
        self.lbl_status.pack(fill=X, padx=10)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill=X, padx=10, pady=5)

        result_frame = ttk.Frame(self)
        result_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(result_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.result_tree = ttk.Treeview(
            result_frame,
            columns=("full_path",),
            show="tree",
            yscrollcommand=scrollbar.set,
            selectmode="browse",
        )
        self.result_tree.column("#0", stretch=True, anchor="w")
        self.result_tree.heading("#0", text="Results")
        self.result_tree.column("full_path", width=0, stretch=False)
        self.result_tree.pack(fill=BOTH, expand=True)
        scrollbar.configure(command=self.result_tree.yview)
        self.result_tree.bind("<Double-1>", lambda _event: self.open_file())

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=X, padx=10, pady=5)

        ttk.Button(controls_frame, text="Open Selected File", command=self.open_file).pack(side=LEFT, padx=5)
        ttk.Button(controls_frame, text="Open Folder Location", command=self.open_folder).pack(side=LEFT, padx=5)
        self.btn_show_more = ttk.Button(
            controls_frame, text="Show More", command=lambda: self._render_results(reset=False), state=DISABLED
        )
        self.btn_show_more.pack(side=RIGHT)

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
        self._reset_results_view()
        threading.Thread(target=self.search_files, args=(query,), daemon=True).start()

    def search_files(self, query):
        self.progress.start()
        count = 0
        selected_ext = self.file_type.get().lower()
        has_wildcard = any(ch in query for ch in "*?")
        lowered_query = query.lower()
        max_depth = self._get_max_depth()
        excluded_terms = self._get_excluded_terms()
        if excluded_terms:
            self.lbl_status.config(text=f"Searching... Excluding: {', '.join(excluded_terms)}")
        collected = []

        for folder in self.folder_paths:
            if self.var_recursive.get():
                walker = self._limited_walk(folder, max_depth, excluded_terms)
            else:
                files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
                walker = [(folder, [], files)]

            for root, _, files in walker:
                for f in files:
                    file_lower = f.lower()
                    full_path = os.path.join(root, f)
                    if excluded_terms and self._contains_excluded(full_path, excluded_terms):
                        continue
                    if has_wildcard:
                        match = fnmatch.fnmatch(file_lower, lowered_query)
                    else:
                        match = lowered_query in file_lower
                    if not match:
                        continue
                    if selected_ext != "all" and not file_lower.endswith(selected_ext):
                        continue
                    collected.append((root, f, full_path))
                    count += 1

        self.progress.stop()
        self.lbl_status.config(text=f"Completed search in {len(self.folder_paths)} folder(s).")
        self._update_selected_label()
        collected.sort(key=lambda item: (item[0], item[1]))
        self.results = collected
        self._render_results(reset=True)
        messagebox.showinfo("Search Complete", f"Found {count} matching files.")

    def _limited_walk(self, root_folder, max_depth, excluded_terms):
        for current_root, dirs, files in os.walk(root_folder):
            rel = os.path.relpath(current_root, root_folder)
            depth = 0 if rel == "." else rel.count(os.sep)

            if excluded_terms:
                dirs[:] = [
                    d for d in dirs if not self._contains_excluded(os.path.join(current_root, d), excluded_terms)
                ]

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

    def _get_excluded_terms(self):
        excluded = []
        if self.var_exclude_git.get():
            excluded.append("git")
        if self.var_exclude_node.get():
            excluded.append("node_modules")
        raw = self.exclude_dirs_var.get().strip()
        if raw:
            excluded.extend(part.strip().lstrip(".").lower() for part in raw.split(",") if part.strip())
        return [pattern for pattern in excluded if pattern]

    def _contains_excluded(self, path, patterns):
        path_lower = os.path.normpath(path).lower()
        for pattern in patterns:
            if fnmatch.fnmatch(path_lower, f"*{pattern}*") or pattern in path_lower:
                return True
        return False

    def open_file(self):
        selection = self.result_tree.selection()
        if not selection:
            messagebox.showwarning("Select File", "Please select a file from the list.")
            return
        item_id = selection[0]
        if self.result_tree.get_children(item_id):
            messagebox.showinfo("Select File", "Expand a folder and choose a file.")
            return
        path = self.result_tree.set(item_id, "full_path")
        if not path:
            messagebox.showwarning("Select File", "Please select a file from the list.")
            return
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.call(["open", path])
        except Exception as exc:
            messagebox.showerror("Open File", f"Unable to open file.\n{exc}")

    def open_folder(self):
        selection = self.result_tree.selection()
        if not selection:
            messagebox.showwarning("Select Folder", "Please select an entry from the list.")
            return
        item_id = selection[0]
        path = self.result_tree.set(item_id, "full_path")
        if not path:
            path = self.result_tree.item(item_id, "text")
        else:
            path = os.path.dirname(path)

        if not path:
            messagebox.showwarning("Select Folder", "Please select a file or folder.")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.call(["open", path])
        except Exception as exc:
            messagebox.showerror("Open Folder", f"Unable to open folder.\n{exc}")

    def _reset_results_view(self):
        self.result_tree.delete(*self.result_tree.get_children())
        self.folder_nodes = {}
        self.results = []
        self.result_display_count = 0
        self.btn_show_more.config(state=DISABLED)

    def _render_results(self, reset):
        if reset:
            self.result_tree.delete(*self.result_tree.get_children())
            self.folder_nodes = {}
            self.result_display_count = 0

        target = min(len(self.results), self.result_display_count + self.page_size)
        for idx in range(self.result_display_count, target):
            folder, file_name, full_path = self.results[idx]
            folder = os.path.normpath(folder)
            node = self.folder_nodes.get(folder)
            if not node:
                node = self.result_tree.insert("", tk.END, text=folder, open=False)
                self.folder_nodes[folder] = node
            self.result_tree.insert(node, tk.END, text=file_name, values=(full_path,))

        self.result_display_count = target
        if self.result_display_count >= len(self.results):
            self.btn_show_more.config(state=DISABLED)
        else:
            self.btn_show_more.config(state=NORMAL)
