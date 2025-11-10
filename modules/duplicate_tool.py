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
        self.stop_event = threading.Event()
        self.scan_thread = None
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="🧩 Duplicate Finder", font=("Segoe UI", 12, "bold")).pack(pady=10)

        frm_top = ttk.Frame(self)
        frm_top.pack(pady=5)

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

        self.lbl_selected = ttk.Label(self, text="No folders selected", bootstyle="secondary")
        self.lbl_selected.pack(fill=X, padx=10, pady=5)

        frm_filter = ttk.Frame(self)
        frm_filter.pack(fill=X, padx=10, pady=5)
        ttk.Label(frm_filter, text="Filter (supports * and ?):").pack(side=LEFT)
        self.filter_entry = ttk.Entry(frm_filter, width=30)
        self.filter_entry.pack(side=LEFT, padx=5)

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

        self.lbl_status = ttk.Label(self, text="Ready", bootstyle="secondary")
        self.lbl_status.pack(fill=X, padx=10)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill=X, padx=10, pady=5)

        self.result_list = tk.Listbox(self, font=("Consolas", 10))
        self.result_list.pack(fill=BOTH, expand=True, padx=10, pady=5)

        ttk.Button(self, text="Open File", command=self.open_file).pack(side=LEFT, padx=10, pady=5)
        ttk.Button(self, text="Delete File", command=self.delete_file).pack(side=LEFT, padx=10, pady=5)

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
        self.stop_event.clear()
        self.btn_scan.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self._set_status("Scanning duplicates...")
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
        self.result_list.delete(0, tk.END)
        self._set_status("Indexing files...")
        self.progress.start()
        stopped = False

        pattern = self.filter_entry.get().strip().lower()
        pattern_has_wildcard = any(ch in pattern for ch in "*?") if pattern else False

        size_map = {}
        max_depth = self._get_max_depth()
        excluded_dirs = self._get_excluded_dirs()

        for folder in self.folder_paths:
            if self.stop_event.is_set():
                stopped = True
                break
            for root, dirs, files in self._limited_walk(folder, max_depth, excluded_dirs):
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
                    try:
                        size = os.path.getsize(full_path)
                    except (OSError, PermissionError):
                        continue
                    size_map.setdefault(size, []).append(full_path)
                if stopped:
                    break
            if stopped:
                break

        duplicates = []
        duplicate_set = set()
        if not stopped:
            self._set_status("Comparing candidates...")
            for paths in size_map.values():
                if len(paths) < 2:
                    continue
                hash_map = {}
                for path in paths:
                    self._set_status(f"Hashing: {path}")
                    if self.stop_event.is_set():
                        stopped = True
                        break
                    h = self.hash_file(path)
                    if not h:
                        continue
                    if h in hash_map:
                        original = hash_map[h]
                        if original not in duplicate_set:
                            duplicates.append(original)
                            duplicate_set.add(original)
                        if path not in duplicate_set:
                            duplicates.append(path)
                            duplicate_set.add(path)
                    else:
                        hash_map[h] = path
                if stopped:
                    break

        self.progress.stop()
        self.btn_scan.config(state=NORMAL)
        self.btn_stop.config(state=DISABLED)
        self.stop_event.clear()

        if stopped:
            self._set_status("Scan stopped.")
            messagebox.showinfo("Scan Stopped", "Duplicate scan was stopped before completion.")
            return

        if duplicates:
            for dup in duplicates:
                self.result_list.insert(tk.END, dup)
            messagebox.showinfo("Scan Complete", f"Found {len(duplicates)} duplicate files.")
            self._set_status(f"Found duplicates in {len(self.folder_paths)} folder(s).")
        else:
            messagebox.showinfo("Scan Complete", "No duplicates found.")
            self._set_status("No duplicates found.")

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

    def _limited_walk(self, root_folder, max_depth, excluded_dirs):
        for current_root, dirs, files in os.walk(root_folder):
            rel = os.path.relpath(current_root, root_folder)
            depth = 0 if rel == "." else rel.count(os.sep)

            if excluded_dirs:
                dirs[:] = [d for d in dirs if d.lower() not in excluded_dirs]

            if max_depth is not None and depth >= max_depth:
                dirs[:] = []

            yield current_root, dirs, files

    def open_file(self):
        try:
            path = self.result_list.get(self.result_list.curselection())
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.call(["open", path])
        except:
            messagebox.showwarning("Select File", "Please select a file from the list.")

    def delete_file(self):
        try:
            path = self.result_list.get(self.result_list.curselection())
            confirm = messagebox.askyesno("Confirm Delete", f"Delete this file?\n{path}")
            if confirm:
                os.remove(path)
                self.result_list.delete(tk.ANCHOR)
        except:
            messagebox.showwarning("Select File", "Please select a file from the list.")
