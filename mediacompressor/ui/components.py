import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable, Optional
from mediacompressor.ui.theme import Theme

class HeaderWidget(tk.Frame):
    """Clean section header banner with title and subtitle."""
    def __init__(self, parent, title: str, subtitle: str):
        super().__init__(parent, bg=Theme.BG_DARK)
        
        lbl_title = tk.Label(
            self, text=title, font=Theme.FONT_TITLE, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK, anchor="w"
        )
        lbl_title.pack(fill="x", pady=(0, 2))

        lbl_sub = tk.Label(
            self, text=subtitle, font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_DARK, anchor="w"
        )
        lbl_sub.pack(fill="x", pady=(0, 10))


class FilePickerWidget(tk.Frame):
    """File/Folder picker with Entry field and Browse button."""
    def __init__(
        self,
        parent,
        label_text: str,
        mode: str = "file",  # "file", "multi_file", "folder"
        file_types: Optional[list] = None,
        on_select_callback: Optional[Callable[[str], None]] = None
    ):
        super().__init__(parent, bg=Theme.BG_CARD)
        self.mode = mode
        self.file_types = file_types or [("All Files", "*.*")]
        self.on_select_callback = on_select_callback

        lbl = tk.Label(
            self, text=label_text, font=Theme.FONT_BODY, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD, anchor="w"
        )
        lbl.pack(fill="x", pady=(0, 4))

        input_frame = tk.Frame(self, bg=Theme.BG_CARD)
        input_frame.pack(fill="x")

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            input_frame,
            textvariable=self.entry_var,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_MAIN,
            insertbackground=Theme.TEXT_MAIN,
            relief="solid",
            bd=1
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)

        btn_browse = tk.Button(
            input_frame,
            text="Browse...",
            font=Theme.FONT_BODY,
            bg=Theme.PRIMARY,
            fg="#FFFFFF",
            activebackground=Theme.PRIMARY_HOVER,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._browse
        )
        btn_browse.pack(side="right", padx=(8, 0), ipadx=12, ipady=3)

    def _browse(self):
        if self.mode == "file":
            res = filedialog.askopenfilename(filetypes=self.file_types)
            if res:
                self.entry_var.set(res)
                if self.on_select_callback:
                    self.on_select_callback(res)
        elif self.mode == "multi_file":
            res = filedialog.askopenfilenames(filetypes=self.file_types)
            if res:
                joined = "; ".join(res)
                self.entry_var.set(joined)
                if self.on_select_callback:
                    self.on_select_callback(res)
        elif self.mode == "folder":
            res = filedialog.askdirectory()
            if res:
                self.entry_var.set(res)
                if self.on_select_callback:
                    self.on_select_callback(res)

    def get_value(self) -> str:
        return self.entry_var.get().strip()

    def set_value(self, val: str):
        self.entry_var.set(val)


class ProgressBarWidget(tk.Frame):
    """Custom progress bar with status text, percentage, speed, and ETA."""
    def __init__(self, parent):
        super().__init__(parent, bg=Theme.BG_CARD)

        info_frame = tk.Frame(self, bg=Theme.BG_CARD)
        info_frame.pack(fill="x", pady=(0, 4))

        self.lbl_status = tk.Label(
            info_frame, text="Ready", font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, anchor="w"
        )
        self.lbl_status.pack(side="left", fill="x", expand=True)

        self.lbl_pct = tk.Label(
            info_frame, text="0%", font=Theme.FONT_SUBTITLE, fg=Theme.PRIMARY, bg=Theme.BG_CARD, anchor="e"
        )
        self.lbl_pct.pack(side="right")

        # Canvas progress bar for custom dark theme look
        self.canvas = tk.Canvas(
            self, height=14, bg=Theme.BG_INPUT, highlightthickness=0, bd=0
        )
        self.canvas.pack(fill="x", expand=True)

        # Bottom metrics (Speed, ETA)
        metrics_frame = tk.Frame(self, bg=Theme.BG_CARD)
        metrics_frame.pack(fill="x", pady=(4, 0))

        self.lbl_speed = tk.Label(
            metrics_frame, text="Speed: --", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD
        )
        self.lbl_speed.pack(side="left")

        self.lbl_eta = tk.Label(
            metrics_frame, text="ETA: --:--", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD
        )
        self.lbl_eta.pack(side="right")

    def update_progress(self, percent: float, status_msg: str = "", speed: str = "", eta: str = ""):
        pct = max(0.0, min(100.0, percent))
        self.lbl_pct.config(text=f"{pct:.1f}%")
        
        if status_msg:
            self.lbl_status.config(text=status_msg)
        if speed:
            self.lbl_speed.config(text=f"Speed: {speed}")
        if eta:
            self.lbl_eta.config(text=f"ETA: {eta}")

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        self.canvas.delete("all")

        if w > 1:
            fill_w = (pct / 100.0) * w
            self.canvas.create_rectangle(0, 0, fill_w, h, fill=Theme.PRIMARY, width=0)

    def reset(self):
        self.update_progress(0.0, "Ready", "--", "--:--")


class LogConsoleWidget(tk.Frame):
    """Scrolled logging console."""
    def __init__(self, parent, height: int = 6):
        super().__init__(parent, bg=Theme.BG_CARD)

        lbl = tk.Label(
            self, text="Activity Log Console", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, anchor="w"
        )
        lbl.pack(fill="x", pady=(0, 4))

        text_frame = tk.Frame(self, bg=Theme.BG_INPUT)
        text_frame.pack(fill="both", expand=True)

        self.text_widget = tk.Text(
            text_frame,
            height=height,
            font=Theme.FONT_MONO,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_MUTED,
            insertbackground=Theme.TEXT_MAIN,
            relief="solid",
            bd=1,
            state="disabled",
            wrap="word"
        )
        self.text_widget.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, command=self.text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_widget.config(yscrollcommand=scrollbar.set)

    def log(self, message: str):
        self.text_widget.config(state="normal")
        self.text_widget.insert("end", message + "\n")
        self.text_widget.see("end")
        self.text_widget.config(state="disabled")

    def clear(self):
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.config(state="disabled")
