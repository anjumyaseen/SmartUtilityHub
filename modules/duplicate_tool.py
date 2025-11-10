import os
import hashlib
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
        self.folder = None
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="🧩 Duplicate Finder", font=("Segoe UI", 12, "bold")).pack(pady=10)

        frm_top = ttk.Frame(self)
        frm_top.pack(pady=5)

        self.btn_choose = ttk.Button(frm_top, text="Choose Folder", command=self.choose_folder)
        self.btn_choose.pack(side=LEFT, padx=5)

        self.btn_scan = ttk.Button(frm_top, text="Scan for Duplicates", bootstyle="warning", command=self.start_scan)
        self.btn_scan.pack(side=LEFT, padx=5)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill=X, padx=10, pady=5)

        self.result_list = tk.Listbox(self, font=("Consolas", 10))
        self.result_list.pack(fill=BOTH, expand=True, padx=10, pady=5)

        ttk.Button(self, text="Open File", command=self.open_file).pack(side=LEFT, padx=10, pady=5)
        ttk.Button(self, text="Delete File", command=self.delete_file).pack(side=LEFT, padx=10, pady=5)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Scan")
        if folder:
            self.folder = folder
            messagebox.showinfo("Folder Selected", f"Selected: {folder}")

    def start_scan(self):
        if not self.folder:
            messagebox.showwarning("Select Folder", "Please choose a folder first.")
            return
        threading.Thread(target=self.scan_duplicates, daemon=True).start()

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
        self.progress.start()
        seen = {}
        duplicates = []

        for root, _, files in os.walk(self.folder):
            for f in files:
                full_path = os.path.join(root, f)
                h = self.hash_file(full_path)
                if h:
                    if h in seen:
                        duplicates.append(full_path)
                    else:
                        seen[h] = full_path

        self.progress.stop()
        if duplicates:
            for dup in duplicates:
                self.result_list.insert(tk.END, dup)
            messagebox.showinfo("Scan Complete", f"Found {len(duplicates)} duplicate files.")
        else:
            messagebox.showinfo("Scan Complete", "No duplicates found.")

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
