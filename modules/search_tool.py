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
    PAGE_SIZE = 50

    def __init__(self, master):
        super().__init__(master)
        self.folder_paths = []
        self.exclusions = {"folders": set(), "names": set()}
        self.include_exts = set()
        self.folder_preset_vars = {}
        self._all_results = []
        self._render_index = 0
        self.folder_nodes = {}
        self._create_widgets()

    # ------------------------------------------------------------------ UI SETUP
    def _create_widgets(self):
        ttk.Label(self, text="🔍 File Search", font=("Segoe UI", 12, "bold")).pack(pady=10)

        self.var_filters_open = tk.BooleanVar(value=False)

        top = ttk.Frame(self)
        top.pack(pady=5, fill=X)
        self.btn_choose = ttk.Button(top, text="Choose Folder(s)", command=self.choose_folder)
        self.btn_choose.pack(side=LEFT, padx=5)
        ttk.Button(top, text="Clear", bootstyle="secondary-outline", command=self.clear_folders).pack(side=LEFT, padx=5)

        self.entry_query = ttk.Entry(top, width=36)
        self.entry_query.pack(side=LEFT, padx=5)
        self._set_placeholder(self.entry_query, "Search files, folders, settings…")

        depth_row = ttk.Frame(top)
        depth_row.pack(side=LEFT, padx=6)
        ttk.Label(depth_row, text="Max depth:").pack(side=LEFT)
        self.max_depth_var = tk.StringVar(value="")
        ttk.Entry(depth_row, textvariable=self.max_depth_var, width=6).pack(side=LEFT, padx=4)

        ttk.Checkbutton(
            top,
            text="Show filters",
            variable=self.var_filters_open,
            bootstyle="round-toggle",
            command=self._toggle_filters,
        ).pack(side=LEFT, padx=5)

        self.btn_search = ttk.Button(top, text="Search", bootstyle="success", command=self.start_search)
        self.btn_search.pack(side=LEFT, padx=5)

        self.lbl_selected = ttk.Label(self, text="No folders selected", bootstyle="secondary")
        self.lbl_selected.pack(fill=X, padx=10, pady=4)

        header = ttk.Frame(self)
        header.pack(fill=X, padx=10, pady=(2, 0))
        ttk.Label(header, text="Filters & Exclusions", font=("Segoe UI", 10, "bold")).pack(side=LEFT)
        self.lbl_filters_title = ttk.Label(header, text="(0 applied)", bootstyle="secondary")
        self.lbl_filters_title.pack(side=LEFT, padx=6)

        self.filters_frame = ttk.Frame(self)
        self.filters_frame.pack_forget()

        ttk.Label(
            self.filters_frame,
            text="Include only these file types (leave empty for all).",
            bootstyle="secondary",
        ).pack(anchor="w", padx=10, pady=(4, 0))

        include_row = ttk.Frame(self.filters_frame)
        include_row.pack(fill=X, pady=4, padx=10)
        self.include_exts = set()
        self.include_preset_vars = {}
        for ext in [".pdf", ".docx", ".xlsx", ".zip", ".log", ".txt"]:
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(
                include_row, text=ext, variable=var, command=lambda v=var, e=ext: self._toggle_include_ext(v, e)
            )
            chk.pack(side=LEFT, padx=4)
            self.include_preset_vars[ext] = var

        include_entry_row = ttk.Frame(self.filters_frame)
        include_entry_row.pack(fill=X, pady=4, padx=10)
        ttk.Label(include_entry_row, text="Add file type:").pack(side=LEFT, padx=(0, 6))
        self.include_entry = ttk.Entry(include_entry_row, width=16)
        self.include_entry.pack(side=LEFT)
        self._set_placeholder(self.include_entry, ".csv or *.report")
        ttk.Button(include_entry_row, text="Add", command=self._add_include_ext).pack(side=LEFT, padx=6)



        self.chips_frame = ttk.Frame(self.filters_frame)
        self.chips_frame.pack(fill=X, padx=10, pady=(2, 8))

        self.lbl_status = ttk.Label(self, text="Ready", bootstyle="secondary")
        self.lbl_status.pack(fill=X, padx=10)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill=X, padx=10, pady=5)

        cols = ("Folder", "Ext", "Size", "Location", "FullPath")

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        yscroll = ttk.Scrollbar(tree_frame, orient=VERTICAL)
        yscroll.pack(side=RIGHT, fill=Y)

        xscroll = ttk.Scrollbar(tree_frame, orient=HORIZONTAL)
        xscroll.pack(side=BOTTOM, fill=X)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=cols,
            show="tree",
            selectmode="browse",
            height=18,
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set,
        )
        self.tree.heading("#0", text="Name")
        self.tree.column("#0", width=240, stretch=True, anchor="w")
        self.tree.heading("Folder", text="Folder")
        self.tree.column("Folder", width=420, anchor="w", stretch=True)
        self.tree.heading("Ext", text="")
        self.tree.column("Ext", width=60, anchor="w")
        self.tree.heading("Size", text="")
        self.tree.column("Size", width=80, anchor="e")
        self.tree.heading("Location", text="")
        self.tree.column("Location", width=200, anchor="w")
        self.tree.heading("FullPath", text="")
        self.tree.column("FullPath", width=0, stretch=False)
        self.tree["displaycolumns"] = ("Folder", "Ext", "Size", "Location")
        self.tree.pack(fill=BOTH, expand=True)
        yscroll.config(command=self.tree.yview)
        xscroll.config(command=self.tree.xview)
        self.tree.bind("<Double-1>", lambda _e: self.open_file())

        btnrow = ttk.Frame(self)
        btnrow.pack(fill=X, padx=10, pady=(0, 8))
        ttk.Button(btnrow, text="Open File", command=self.open_file).pack(side=LEFT, padx=4)
        ttk.Button(btnrow, text="Open Folder", command=self.open_folder).pack(side=LEFT, padx=4)
        self.btn_show_more = ttk.Button(btnrow, text="Show 50 more", bootstyle="secondary", command=self._show_more)
        self.btn_show_more.pack(side=RIGHT)
        self.btn_show_more.config(state=DISABLED)

    # ------------------------------------------------------------------ PLACEHOLDER
    def _set_placeholder(self, entry, text):
        entry.placeholder_text = text

        def on_focus_in(_):
            if entry.get() == text:
                entry.delete(0, tk.END)

        def on_focus_out(_):
            if not entry.get():
                entry.insert(0, text)

        entry.insert(0, text)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    # ------------------------------------------------------------------ FILTERS
    def _toggle_filters(self):
        if self.var_filters_open.get():
            self.filters_frame.pack(fill=X, padx=0, pady=(0, 6))
        else:
            self.filters_frame.pack_forget()

    def _add_preset_folder(self):
        val = self.cmb_presets.get().strip().lstrip(".").lower()
        if val:
            self.exclusions["folders"].add(val)
            self._refresh_chips()

    def _toggle_folder_chip(self, var, token):
        if var.get():
            self.exclusions["folders"].add(token)
        else:
            self.exclusions["folders"].discard(token)
        self._refresh_chips()

    def _toggle_include_ext(self, var, token):
        ext = token if token.startswith(".") else f".{token}"
        if var.get():
            self.include_exts.add(ext)
        else:
            self.include_exts.discard(ext)
        self._refresh_chips()

    def _add_include_ext(self):
        value = self.include_entry.get().strip().lower()
        placeholder = getattr(self.include_entry, "placeholder_text", "")
        if not value or value == placeholder.lower():
            return
        if not value.startswith(".") and not value.startswith("*"):
            value = "." + value
        self.include_exts.add(value)
        self.include_entry.delete(0, tk.END)
        self._refresh_chips()

    def _add_name(self):
        name = self.entry_name.get().strip().lower()
        placeholder = getattr(self.entry_name, "placeholder_text", "")
        if not name or name == placeholder.lower():
            return
        self.exclusions["names"].add(name)
        self.entry_name.delete(0, tk.END)
        self._refresh_chips()

    def _refresh_chips(self):
        for child in self.chips_frame.winfo_children():
            child.destroy()

        count = 0

        def make_chip(label, bucket, value):
            nonlocal count
            count += 1
            frame = ttk.Frame(self.chips_frame, bootstyle="secondary")
            ttk.Label(frame, text=label).pack(side=LEFT, padx=6)
            ttk.Button(frame, text="x", width=2, command=lambda b=bucket, v=value: self._remove_chip(b, v)).pack(
                side=LEFT
            )
            frame.pack(side=LEFT, padx=4, pady=2)

        for ext in sorted(self.include_exts):
            make_chip(ext, "includes", ext)

        for token in sorted(self.exclusions["folders"]):
            make_chip(f"folder: {token}", "folders", token)

        for pattern in sorted(self.exclusions["names"]):
            make_chip(f"name: {pattern}", "names", pattern)

        self.lbl_filters_title.config(text=f"({count} applied)")

    def _remove_chip(self, bucket, value):
        if bucket == "includes":
            self.include_exts.discard(value)
            for label, var in getattr(self, "include_preset_vars", {}).items():
                if label.lower() == value.lower():
                    var.set(False)
        else:
            self.exclusions[bucket].discard(value)
            if bucket == "folders":
                for label, var in getattr(self, "folder_preset_vars", {}).items():
                    if value == label.lstrip(".").lower():
                        var.set(False)
        self._refresh_chips()

    # ------------------------------------------------------------------ FOLDERS
    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder and folder not in self.folder_paths:
            self.folder_paths.append(folder)
            self.lbl_selected.config(text="Folders: " + "; ".join(self.folder_paths))

    def clear_folders(self):
        if self.folder_paths:
            self.folder_paths.clear()
            self.lbl_selected.config(text="No folders selected")

    # ------------------------------------------------------------------ SEARCH
    def start_search(self):
        query = self.entry_query.get().strip()
        placeholder = getattr(self.entry_query, "placeholder_text", "")
        if not self.folder_paths or not query or query == placeholder:
            messagebox.showwarning("Input Missing", "Please select folder(s) and enter search term.")
            return

        lowered_query = query.lower()
        use_wildcards = any(ch in lowered_query for ch in "*?")

        self.lbl_status.config(text="Searching…")
        self.progress.start()
        self._all_results.clear()
        self._render_index = 0
        self.folder_nodes.clear()
        for child in self.tree.get_children():
            self.tree.delete(child)

        threading.Thread(
            target=self._search_files_thread, args=(lowered_query, use_wildcards), daemon=True
        ).start()

    def _search_files_thread(self, lowered_query, use_wildcards):
        results = []

        max_depth = self._get_max_depth()

        include_filters = self._normalize_include_filters()

        for base in self.folder_paths:
            for root, dirs, files in os.walk(base):
                self.after(0, lambda path=root: self.lbl_status.config(text=f"Searching… {path}"))
                if max_depth is not None:
                    rel = os.path.relpath(root, base)
                    depth = 0 if rel == "." else rel.count(os.sep)
                    if depth >= max_depth:
                        dirs[:] = []

                if self.exclusions["folders"]:
                    dirs[:] = [
                        d
                        for d in dirs
                        if not any(tok in os.path.join(root, d).lower() for tok in self.exclusions["folders"])
                    ]
                for fname in files:
                    if not self._query_matches(fname, lowered_query, use_wildcards):
                        continue
                    if self._path_excluded(root, fname):
                        continue
                    if include_filters and not self._matches_includes(fname, include_filters):
                        continue
                    full_path = os.path.join(root, fname)
                    try:
                        size = os.path.getsize(full_path)
                    except OSError:
                        size = 0
                    results.append(
                        {
                            "folder": root,
                            "parent": os.path.basename(root),
                            "name": fname,
                            "ext": os.path.splitext(fname)[1].lower(),
                            "size": size,
                            "path": full_path,
                        }
                    )

        results.sort(key=lambda item: (item["folder"].lower(), item["name"].lower()))
        self.after(0, lambda: self._on_search_complete(results))

    def _on_search_complete(self, results):
        self.progress.stop()
        self._all_results = results
        self._render_index = 0
        self.folder_nodes.clear()
        self._render_next_batch()
        count = len(results)
        self.lbl_status.config(text=f"Found {count} matching file(s).")
        messagebox.showinfo("Search Complete", f"Found {count} matching file(s).")

    # ------------------------------------------------------------------ RESULTS RENDERING
    def _render_next_batch(self, batch=PAGE_SIZE):
        if not self._all_results:
            self.btn_show_more.config(state=DISABLED)
            return

        end = min(self._render_index + batch, len(self._all_results))
        for item in self._all_results[self._render_index : end]:
            folder = item["folder"]
            node = self.folder_nodes.get(folder)
            if not node:
                basename = os.path.basename(folder) or folder
                node = self.tree.insert(
                    "",
                    tk.END,
                    text=basename,
                    open=False,
                    values=(folder, "", "", "", folder),
                )
                self.folder_nodes[folder] = node

            size_str = self._format_size(item["size"])
            self.tree.insert(
                node,
                tk.END,
                text=item["name"],
                values=(item["folder"], item["ext"], size_str, item["parent"], item["path"]),
            )

        self._render_index = end
        if self._render_index >= len(self._all_results):
            self.btn_show_more.config(state=DISABLED)
        else:
            self.btn_show_more.config(state=NORMAL)

    def _show_more(self):
        if self._render_index < len(self._all_results):
            self._render_next_batch()
        else:
            messagebox.showinfo("Results", "All results are already displayed.")

    # ------------------------------------------------------------------ EXCLUSIONS
    def _path_excluded(self, folder, name):
        full_lower = os.path.join(folder, name).lower()
        lname = name.lower()

        for tok in self.exclusions["folders"]:
            if tok in full_lower:
                return True

        for pattern in self.exclusions["names"]:
            if fnmatch.fnmatch(lname, pattern):
                return True

        return False

    def _query_matches(self, filename, lowered_query, use_wildcards):
        lname = filename.lower()
        if use_wildcards:
            return fnmatch.fnmatch(lname, lowered_query)
        return lowered_query in lname

    def _normalize_include_filters(self):
        if not self.include_exts:
            return []

        filters = []
        for token in self.include_exts:
            if token.startswith("*") or any(ch in token for ch in "*?"):
                filters.append(("pattern", token.lower()))
            elif token.startswith("."):
                filters.append(("ext", token.lower()))
            else:
                filters.append(("ext", f".{token.lower()}"))
        return filters

    def _matches_includes(self, filename, filters):
        lname = filename.lower()
        ext = os.path.splitext(lname)[1]
        for ftype, value in filters:
            if ftype == "ext" and ext == value:
                return True
            if ftype == "pattern" and fnmatch.fnmatch(lname, value):
                return True
        return False

    # ------------------------------------------------------------------ UTILITIES
    def _format_size(self, num_bytes):
        try:
            num = int(num_bytes)
        except (TypeError, ValueError):
            return ""

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if num < 1024:
                return f"{num:.0f} {unit}"
            num /= 1024
        return f"{num:.0f} PB"

    def _selected_path(self):
        selection = self.tree.selection()
        if not selection:
            return None
        node = selection[0]
        # If a folder row is selected, use the folder path stored on the row.
        path = self.tree.set(node, "FullPath")
        if path:
            return path
        # Otherwise fall back to the parent folder path plus the file name.
        parent = self.tree.parent(node)
        if not parent:
            return None
        folder = self.tree.set(parent, "FullPath")
        name = self.tree.item(node, "text")
        return os.path.join(folder, name)

    def open_file(self):
        path = self._selected_path()
        if not path:
            messagebox.showwarning("Select File", "Please select a file row.")
            return
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.call(["open", path])
        except Exception as exc:
            messagebox.showerror("Open File", f"Unable to open file.\n{exc}")

    def open_folder(self):
        path = self._selected_path()
        if not path:
            messagebox.showwarning("Select File", "Please select a file row.")
            return
        folder = os.path.dirname(path)
        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            else:
                subprocess.call(["open", folder])
        except Exception as exc:
            messagebox.showerror("Open Folder", f"Unable to open folder.\n{exc}")
    def _get_max_depth(self):
        value = self.max_depth_var.get().strip()
        if not value:
            return None
        try:
            depth = int(value)
            return depth if depth >= 0 else None
        except ValueError:
            return None
