import os
import hashlib
import fnmatch
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import threading
import subprocess
import platform


class DuplicateTool(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.folder_paths = []
        self.exclusions = {"folders": {"git", "node_modules"}, "names": set()}
        self.stop_event = threading.Event()
        self.scan_thread = None
        self.duplicate_groups = []
        self.group_display_count = 0
        self.group_nodes = {}
        self.page_size = 50
        self.system_skip_tokens = {
            "\\windows",
            "\\program files",
            "\\program files (x86)",
            "\\programdata",
            "\\appdata",
            "\\$recycle.bin",
            "\\system volume information",
        }
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="🧩 Duplicate Finder", font=("Segoe UI", 12, "bold")).pack(pady=10)

        self.var_filters_open = tk.BooleanVar(value=False)

        frm_top = ttk.Frame(self)
        frm_top.pack(pady=5, fill=X)

        self.btn_choose = ttk.Button(frm_top, text="Choose Folder", command=self.choose_folder)
        self.btn_choose.pack(side=LEFT, padx=5)

        self.btn_scan = ttk.Button(frm_top, text="Scan for Duplicates", bootstyle="warning", command=self.start_scan)
        self.btn_scan.pack(side=LEFT, padx=5)

        self.btn_stop = ttk.Button(
            frm_top,
            text="Stop",
            bootstyle="danger-outline",
            command=self.stop_scan,
            state=DISABLED,
        )
        self.btn_stop.pack(side=LEFT, padx=5)

        ttk.Button(frm_top, text="Clear Folders", bootstyle="secondary-outline", command=self.clear_folders).pack(
            side=LEFT, padx=5
        )

        ttk.Checkbutton(
            frm_top,
            text="Show filters",
            variable=self.var_filters_open,
            bootstyle="round-toggle",
            command=self._toggle_filters,
        ).pack(side=LEFT, padx=5)

        quick_row = ttk.Frame(self)
        quick_row.pack(fill=X, padx=10, pady=(0, 6))
        ttk.Label(quick_row, text="Max depth:").pack(side=LEFT)
        self.max_depth_var = tk.StringVar(value="")
        ttk.Entry(quick_row, textvariable=self.max_depth_var, width=6).pack(side=LEFT, padx=5)

        ttk.Label(quick_row, text="File name filter (supports * and ?):").pack(side=LEFT, padx=(12, 5))
        self.filter_entry = ttk.Entry(quick_row, width=24)
        self.filter_entry.pack(side=LEFT, padx=5)
        self._set_placeholder(self.filter_entry, "optional pattern")

        self.lbl_selected = ttk.Label(self, text="No folders selected", bootstyle="secondary")
        self.lbl_selected.pack(fill=X, padx=10, pady=5)

        header = ttk.Frame(self)
        header.pack(fill=X, padx=10, pady=(0, 2))
        ttk.Label(header, text="Filters & Exclusions", font=("Segoe UI", 10, "bold")).pack(side=LEFT)
        self.lbl_filters = ttk.Label(header, text="(0 applied)", bootstyle="secondary")
        self.lbl_filters.pack(side=LEFT, padx=6)

        self.filters_frame = ttk.Frame(self)
        self.filters_frame.pack_forget()

        ttk.Label(
            self.filters_frame,
            text="Exclude anything containing these names or extensions (like a .gitignore).",
            bootstyle="secondary",
        ).pack(anchor="w", padx=10, pady=(4, 0))

        folder_row = ttk.Frame(self.filters_frame)
        folder_row.pack(fill=X, pady=6, padx=10)
        ttk.Label(folder_row, text="Common folders:").pack(anchor="w")
        self.folder_preset_vars = {}
        for label in [".git", "node_modules"]:
            token = label.lstrip(".").lower()
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(
                folder_row, text=label, variable=var, command=lambda v=var, name=token: self._toggle_folder_chip(v, name)
            )
            chk.pack(side=LEFT, padx=4)
            self.folder_preset_vars[label] = var
            self.exclusions["folders"].add(token)

        name_row = ttk.Frame(self.filters_frame)
        name_row.pack(fill=X, pady=6, padx=10)
        ttk.Label(name_row, text="Exclude names:").pack(side=LEFT, padx=(0, 6))
        self.entry_name = ttk.Entry(name_row, width=24)
        self.entry_name.pack(side=LEFT)
        self._set_placeholder(self.entry_name, "e.g., Thumbs.db or *.tmp")
        ttk.Button(name_row, text="Add", command=self._add_name).pack(side=LEFT, padx=6)

        self.chips_frame = ttk.Frame(self.filters_frame)
        self.chips_frame.pack(fill=X, padx=10, pady=(2, 8))

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
        self.result_tree.heading("#0", text="Duplicates")
        self.result_tree.column("full_path", width=0, stretch=False)
        self.result_tree.pack(fill=BOTH, expand=True)
        scrollbar.configure(command=self.result_tree.yview)
        self.result_tree.bind("<Double-1>", lambda _event: self.open_file())

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=X, padx=10, pady=5)

        ttk.Button(controls_frame, text="Open File", command=self.open_file).pack(side=LEFT, padx=5)
        ttk.Button(controls_frame, text="Delete File", command=self.delete_file).pack(side=LEFT, padx=5)
        self.btn_dup_show_more = ttk.Button(
            controls_frame, text="Show More", command=lambda: self._render_duplicate_groups(reset=False), state=DISABLED
        )
        self.btn_dup_show_more.pack(side=RIGHT)

        self._refresh_chips()

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

    def _toggle_filters(self):
        if self.var_filters_open.get():
            self.filters_frame.pack(fill=X, padx=0, pady=(0, 6))
        else:
            self.filters_frame.pack_forget()

    def _add_name(self):
        name = self.entry_name.get().strip().lower()
        placeholder = getattr(self.entry_name, "placeholder_text", "")
        if not name or name == placeholder.lower():
            return
        self.exclusions["names"].add(name)
        self.entry_name.delete(0, tk.END)
        self._refresh_chips()

    def _toggle_folder_chip(self, var, token):
        if var.get():
            self.exclusions["folders"].add(token)
        else:
            self.exclusions["folders"].discard(token)
        self._refresh_chips()

    def _refresh_chips(self):
        if not hasattr(self, "chips_frame"):
            return
        for child in self.chips_frame.winfo_children():
            child.destroy()

        count = 0

        def make_chip(label, bucket, value):
            nonlocal count
            count += 1
            frame = ttk.Frame(self.chips_frame, bootstyle="secondary")
            ttk.Label(frame, text=label).pack(side=LEFT, padx=6)
            ttk.Button(frame, text="x", width=2, command=lambda: self._remove_chip(bucket, value)).pack(side=LEFT)
            frame.pack(side=LEFT, padx=4, pady=2)

        for val in sorted(self.exclusions["folders"]):
            make_chip(f"folder:{val}", "folders", val)
        for val in sorted(self.exclusions["names"]):
            make_chip(f"name:{val}", "names", val)

        if hasattr(self, "lbl_filters"):
            self.lbl_filters.config(text=f"({count} applied)")

    def _remove_chip(self, bucket, value):
        self.exclusions[bucket].discard(value)
        if bucket == "folders":
            for label, var in self.folder_preset_vars.items():
                if value == label.lstrip(".").lower():
                    var.set(False)
        self._refresh_chips()

    def _path_excluded(self, folder, name):
        full_lower = os.path.join(folder, name).lower()
        base = name.lower()
        for tok in self.exclusions["folders"]:
            if tok in full_lower:
                return True
        for pattern in self.exclusions["names"]:
            if fnmatch.fnmatch(base, pattern):
                return True
        return False

    def _exclusion_summary(self):
        items = list(self.exclusions["folders"]) + list(self.exclusions["names"])
        return ", ".join(sorted(items))

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Scan")
        if folder:
            self.folder_paths.append(folder)
            self._update_selected_label()

    def _update_selected_label(self):
        if not self.folder_paths:
            text = "No folders selected"
        else:
            text = "Folders: " + "; ".join(self.folder_paths)
        self.lbl_selected.config(text=text)

    def clear_folders(self):
        if self.scan_thread and self.scan_thread.is_alive():
            messagebox.showwarning("Scan Running", "Stop the current scan before clearing folders.")
            return
        if self.folder_paths:
            self.folder_paths.clear()
            self._update_selected_label()
            self._set_status("Cleared selected folders.")

    def _set_status(self, text):
        self.lbl_status.config(text=text)
        self.lbl_status.update_idletasks()

    def start_scan(self):
        if not self.folder_paths:
            messagebox.showwarning("Select Folder", "Please choose at least one folder first.")
            return
        if self.scan_thread and self.scan_thread.is_alive():
            messagebox.showinfo("Scan Running", "Please wait for the current scan to finish or stop it first.")
            return
        self._reset_duplicate_view()
        self.stop_event.clear()
        summary = self._exclusion_summary()
        if summary:
            self._set_status(f"Scanning duplicates... Excluding: {summary}")
        else:
            self._set_status("Scanning duplicates...")
        self.btn_scan.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self.scan_thread = threading.Thread(target=self.scan_duplicates, daemon=True)
        self.scan_thread.start()

    def stop_scan(self):
        if self.scan_thread and self.scan_thread.is_alive():
            self.stop_event.set()
            self._set_status("Stopping scan...")

    def hash_file(self, path):
        try:
            sha = hashlib.sha1()
            with open(path, "rb") as f:
                while chunk := f.read(8192):
                    sha.update(chunk)
            return sha.hexdigest()
        except Exception:
            return None

    def scan_duplicates(self):
        self._set_status("Indexing files...")
        self.progress.start()
        stopped = False

        pattern = ""
        if hasattr(self, "filter_entry"):
            value = self.filter_entry.get().strip().lower()
            placeholder = getattr(self.filter_entry, "placeholder_text", "")
            if value and value != placeholder.lower():
                pattern = value
        pattern_has_wildcard = any(ch in pattern for ch in "*?") if pattern else False

        size_map = {}
        max_depth = self._get_max_depth()
        folder_tokens = set(self.exclusions["folders"])

        for folder in self.folder_paths:
            if self.stop_event.is_set():
                stopped = True
                break
            for root, dirs, files in self._limited_walk(folder, max_depth, folder_tokens | self.system_skip_tokens):
                self._set_status(f"Indexing: {root}")
                if self.stop_event.is_set():
                    stopped = True
                    break
                for f in files:
                    if self.stop_event.is_set():
                        stopped = True
                        break
                    full_path = os.path.join(root, f)
                    if pattern and not self._matches_filter(full_path, f, pattern, pattern_has_wildcard):
                        continue
                    if self._path_excluded(root, f):
                        continue
                    try:
                        size = os.path.getsize(full_path)
                    except (OSError, PermissionError):
                        continue
                    size_map.setdefault(size, []).append(full_path)
                if stopped:
                    break
            if stopped:
                break

        groups_map = {}
        if not stopped:
            self._set_status("Comparing candidates...")
            for size_paths in size_map.values():
                if len(size_paths) < 2:
                    continue
                hash_map = {}
                for path in size_paths:
                    self._set_status(f"Hashing: {path}")
                    if self.stop_event.is_set():
                        stopped = True
                        break
                    h = self.hash_file(path)
                    if not h:
                        continue
                    hash_map.setdefault(h, []).append(path)
                if stopped:
                    break
                for h, same_paths in hash_map.items():
                    if len(same_paths) > 1:
                        groups_map.setdefault(h, set()).update(same_paths)

        self.progress.stop()
        self.btn_scan.config(state=NORMAL)
        self.btn_stop.config(state=DISABLED)
        self.stop_event.clear()

        if stopped:
            self._set_status("Scan stopped.")
            messagebox.showinfo("Scan Stopped", "Duplicate scan was stopped before completion.")
            return

        if groups_map:
            duplicate_groups = []
            for h, paths_set in groups_map.items():
                paths = sorted(paths_set)
                duplicate_groups.append(
                    {
                        "hash": h,
                        "name": os.path.basename(paths[0]) or "(unknown file)",
                        "paths": paths,
                    }
                )
            duplicate_groups.sort(key=lambda g: g["name"].lower())
            self.duplicate_groups = duplicate_groups
            self._render_duplicate_groups(reset=True)
            total_files = sum(len(g["paths"]) for g in duplicate_groups)
            messagebox.showinfo(
                "Scan Complete",
                f"Found {len(duplicate_groups)} duplicate set(s) covering {total_files} files.",
            )
            self._set_status(f"{len(duplicate_groups)} duplicate set(s) found.")
        else:
            messagebox.showinfo("Scan Complete", "No duplicates found.")
            self._set_status("No duplicates found.")

    def _reset_duplicate_view(self):
        self.result_tree.delete(*self.result_tree.get_children())
        self.group_nodes = {}
        self.duplicate_groups = []
        self.group_display_count = 0
        self.btn_dup_show_more.config(state=DISABLED)

    def _render_duplicate_groups(self, reset):
        if reset:
            self.result_tree.delete(*self.result_tree.get_children())
            self.group_nodes = {}
            self.group_display_count = 0

        target = min(len(self.duplicate_groups), self.group_display_count + self.page_size)
        for idx in range(self.group_display_count, target):
            group = self.duplicate_groups[idx]
            label = self._group_label(group)
            node = self.result_tree.insert("", tk.END, text=label, open=False)
            group["node"] = node
            self.group_nodes[node] = group
            for path in group["paths"]:
                self.result_tree.insert(node, tk.END, text=path, values=(path,))

        self.group_display_count = target
        if self.group_display_count >= len(self.duplicate_groups):
            self.btn_dup_show_more.config(state=DISABLED)
        else:
            self.btn_dup_show_more.config(state=NORMAL)

    def _group_label(self, group):
        name = group.get("name") or "(unknown)"
        count = len(group.get("paths", []))
        return f"{name} ({count} copies)"

    def _update_group_label(self, group):
        if group.get("node"):
            self.result_tree.item(group["node"], text=self._group_label(group))

    def _matches_filter(self, full_path, filename, pattern, has_wildcard):
        if not pattern:
            return True
        full_lower = full_path.lower()
        file_lower = filename.lower()
        if has_wildcard:
            return fnmatch.fnmatch(file_lower, pattern) or fnmatch.fnmatch(full_lower, pattern)
        return pattern in file_lower or pattern in full_lower

    def _get_max_depth(self):
        value = self.max_depth_var.get().strip()
        if not value:
            return None
        try:
            depth = int(value)
            return depth if depth >= 0 else None
        except ValueError:
            return None

    def _limited_walk(self, root_folder, max_depth, tokens):
        for current_root, dirs, files in os.walk(root_folder):
            rel = os.path.relpath(current_root, root_folder)
            depth = 0 if rel == "." else rel.count(os.sep)

            if tokens:
                dirs[:] = [
                    d for d in dirs if not any(tok in os.path.join(current_root, d).lower() for tok in tokens)
                ]

            if max_depth is not None and depth >= max_depth:
                dirs[:] = []

            yield current_root, dirs, files

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

    def delete_file(self):
        selection = self.result_tree.selection()
        if not selection:
            messagebox.showwarning("Select File", "Please select a file from the list.")
            return
        item_id = selection[0]
        if self.result_tree.get_children(item_id):
            messagebox.showwarning("Select File", "Please select a file (not a folder).")
            return
        path = self.result_tree.set(item_id, "full_path")
        if not path:
            messagebox.showwarning("Select File", "Please select a file from the list.")
            return
        parent = self.result_tree.parent(item_id)
        group = self.group_nodes.get(parent)
        if not group:
            messagebox.showwarning("Delete File", "Unable to determine duplicate group.")
            return
        confirm = messagebox.askyesno("Confirm Delete", f"Delete this file?\n{path}")
        if not confirm:
            return
        try:
            os.remove(path)
            self.result_tree.delete(item_id)
            if parent and not self.result_tree.get_children(parent):
                self.result_tree.delete(parent)
                self.group_nodes.pop(parent, None)
                group["paths"] = []
            else:
                group["paths"] = [p for p in group["paths"] if p != path]
                self._update_group_label(group)
        except Exception as exc:
            messagebox.showerror("Delete File", f"Unable to delete file.\n{exc}")
