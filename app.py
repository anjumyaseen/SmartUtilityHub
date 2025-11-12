import os
import sys
import tkinter as tk

import darkdetect
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from modules.search_tool import SearchTool
from modules.duplicate_tool import DuplicateTool



class SmartUtilityHub(ttk.Window):
    def __init__(self):
        #super().__init__(themename="auto")
        theme = "darkly" if darkdetect.isDark() else "flatly"
        super().__init__(themename=theme)
        self.title("Smart Utility Hub v1.0")
        self.geometry("900x600")
        self.minsize(800, 500)
        self._set_window_icon()

        self._setup_ui()

    def _resource_path(self, *parts):
        """Locate resource paths both in development and PyInstaller bundles."""
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
        return os.path.join(base_path, *parts)

    def _set_window_icon(self):
        icon_path = self._resource_path("assets", "icons", "smartutilityhub.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as exc:
                print(f"Warning: unable to load window icon ({exc})")

    def _setup_ui(self):
        # Sidebar frame
        self.sidebar = ttk.Frame(self, bootstyle="secondary", width=200)
        self.sidebar.pack(side=LEFT, fill=Y)

        # Main content frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        # Sidebar buttons
        ttk.Label(self.sidebar, text="Smart Utility Hub", font=("Segoe UI", 14, "bold"), bootstyle="inverse-secondary").pack(
            pady=10, fill=X)

        self.btn_search = ttk.Button(self.sidebar, text="🔍  Search Files", bootstyle="secondary-outline",
                                     command=self.show_search)
        self.btn_search.pack(fill=X, padx=10, pady=5)

        self.btn_duplicates = ttk.Button(self.sidebar, text="🧩  Duplicate Finder", bootstyle="secondary-outline",
                                         command=self.show_duplicates)
        self.btn_duplicates.pack(fill=X, padx=10, pady=5)

        ttk.Label(self.sidebar, text="⚙️  More Tools Coming...", bootstyle="secondary").pack(side=BOTTOM, pady=10)

        # Default view
        self.current_view = None
        self.show_search()

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_search(self):
        self.clear_main_frame()
        self.current_view = SearchTool(self.main_frame)
        self.current_view.pack(fill=BOTH, expand=True)

    def show_duplicates(self):
        self.clear_main_frame()
        self.current_view = DuplicateTool(self.main_frame)
        self.current_view.pack(fill=BOTH, expand=True)


if __name__ == "__main__":
    app = SmartUtilityHub()
    app.mainloop()
