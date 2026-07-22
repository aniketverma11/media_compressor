import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from mediacompressor.ui.theme import Theme
from mediacompressor.ui.video_page import VideoPage
from mediacompressor.ui.image_page import ImagePage
from mediacompressor.core.dependency_manager import install_missing_dependencies
from mediacompressor.core.ffmpeg_manager import FFmpegManager
from mediacompressor.core.video_compressor import VideoCompressor
from mediacompressor.core.image_compressor import ImageCompressor
from mediacompressor.utils.logger import setup_logger

class MainWindow(tk.Tk):
    """Main Application Window with sidebar navigation and thread-safe event loop."""

    def __init__(self):
        super().__init__()

        self.title("MediaCompressor Desktop Utility v1.0")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(bg=Theme.BG_DARK)

        # Thread-safe Communication Queue
        self.log_queue = queue.Queue()
        self.logger = setup_logger("logs", self.log_queue)

        # Core Managers
        self.ffmpeg_manager = FFmpegManager("downloads")
        self.video_compressor: Optional[VideoCompressor] = None
        self.image_compressor = ImageCompressor()

        # UI Page Registry
        self.pages: Dict[str, tk.Frame] = {}
        self.current_page_name: Optional[str] = None
        self.sidebar_buttons: Dict[str, tk.Button] = {}

        self._build_ui()
        self._start_queue_poller()
        self._boot_dependency_check()

    def _build_ui(self):
        # Top-level Split: Sidebar | Content Area
        self.main_container = tk.Frame(self, bg=Theme.BG_DARK)
        self.main_container.pack(fill="both", expand=True)

        # 1. Sidebar Navigation
        self.sidebar = tk.Frame(
            self.main_container, bg=Theme.BG_SIDEBAR, width=220, highlightbackground=Theme.BORDER, highlightthickness=1
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # App Brand Header
        brand_frame = tk.Frame(self.sidebar, bg=Theme.BG_SIDEBAR)
        brand_frame.pack(fill="x", padx=16, pady=20)

        lbl_brand = tk.Label(
            brand_frame, text="⚡ MediaCompressor", font=Theme.FONT_TITLE, fg=Theme.PRIMARY, bg=Theme.BG_SIDEBAR
        )
        lbl_brand.pack(anchor="w")

        lbl_ver = tk.Label(
            brand_frame, text="Cross-Platform v1.0", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_SIDEBAR
        )
        lbl_ver.pack(anchor="w")

        # Divider
        div = tk.Frame(self.sidebar, bg=Theme.BORDER, height=1)
        div.pack(fill="x", padx=12, pady=(0, 16))

        # Navigation Buttons
        nav_items = [
            ("video", "🎬  Video Compressor"),
            ("image", "🖼️  Image Compressor"),
        ]

        for page_key, label_text in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=label_text,
                font=Theme.FONT_BODY,
                fg=Theme.TEXT_SIDEBAR,
                bg=Theme.BG_SIDEBAR,
                activebackground=Theme.PRIMARY,
                activeforeground="#FFFFFF",
                relief="flat",
                bd=0,
                anchor="w",
                padx=16,
                cursor="hand2",
                command=lambda k=page_key: self.show_page(k)
            )
            btn.pack(fill="x", pady=2, ipady=8)
            self.sidebar_buttons[page_key] = btn

        # System Status at Bottom Sidebar
        status_frame = tk.Frame(self.sidebar, bg=Theme.BG_SIDEBAR)
        status_frame.pack(side="bottom", fill="x", padx=16, pady=16)

        self.lbl_sys_status = tk.Label(
            status_frame, text="Status: Initializing...", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_SIDEBAR, anchor="w", wrap=180
        )
        self.lbl_sys_status.pack(fill="x")

        # 2. Main Content Frame Area
        self.content_area = tk.Frame(self.main_container, bg=Theme.BG_DARK)
        self.content_area.pack(side="right", fill="both", expand=True)

        # Startup Splash Banner
        self.splash_frame = tk.Frame(self.content_area, bg=Theme.BG_DARK)
        self.splash_frame.pack(fill="both", expand=True)

        lbl_splash_title = tk.Label(
            self.splash_frame, text="Verifying Dependencies & FFmpeg...", font=Theme.FONT_TITLE, fg=Theme.TEXT_MAIN, bg=Theme.BG_DARK
        )
        lbl_splash_title.pack(expand=True)

    def _boot_dependency_check(self):
        """Runs dependency and FFmpeg checks in a background thread."""
        def _task():
            def _log_cb(msg: str):
                self.log_queue.put(("BOOT_LOG", msg))

            _log_cb("Checking Python dependencies...")
            install_missing_dependencies(_log_cb)

            _log_cb("Verifying FFmpeg binary availability...")
            ok = self.ffmpeg_manager.ensure_ffmpeg(_log_cb)

            ffmpeg_p, ffprobe_p = self.ffmpeg_manager.get_paths()
            if ok and ffmpeg_p:
                self.video_compressor = VideoCompressor(ffmpeg_p, ffprobe_p)
                self.log_queue.put(("BOOT_COMPLETE", True))
            else:
                self.log_queue.put(("BOOT_COMPLETE", False))

        threading.Thread(target=_task, daemon=True).start()

    def _start_queue_poller(self):
        """Thread-safe queue listener loop using root.after()."""
        def _poll():
            while not self.log_queue.empty():
                try:
                    event_type, data = self.log_queue.get_nowait()
                    self._dispatch_event(event_type, data)
                except queue.Empty:
                    break
            self.after(100, _poll)

        self.after(100, _poll)

    def _dispatch_event(self, event_type: str, data):
        """Routes background messages safely to UI components."""
        if event_type == "LOG":
            pass
        elif event_type == "BOOT_LOG":
            self.lbl_sys_status.config(text=f"Status: {data[:30]}...")
            self.logger.info(data)
        elif event_type == "BOOT_COMPLETE":
            is_ok = data
            if is_ok and self.video_compressor:
                self.lbl_sys_status.config(text="Status: Ready", fg=Theme.SUCCESS)
                self.logger.info("System dependencies & FFmpeg initialized successfully.")
                self._initialize_pages()
                self.show_page("video")
            else:
                self.lbl_sys_status.config(text="Status: FFmpeg missing!", fg=Theme.DANGER)
                messagebox.showerror(
                    "Startup Warning",
                    "Could not initialize FFmpeg. Video compression features will be disabled until FFmpeg is available."
                )
                self._initialize_pages()
                self.show_page("image")
        elif event_type.startswith("VIDEO_"):
            if "video" in self.pages:
                self.pages["video"].handle_queue_event(event_type, data)
        elif event_type.startswith("IMAGE_"):
            if "image" in self.pages:
                self.pages["image"].handle_queue_event(event_type, data)

    def _initialize_pages(self):
        """Lazy builds page views after boot completion."""
        if self.splash_frame:
            self.splash_frame.destroy()

        if self.video_compressor:
            self.pages["video"] = VideoPage(self.content_area, self.video_compressor, self.log_queue)

        self.pages["image"] = ImagePage(self.content_area, self.image_compressor, self.log_queue)

    def show_page(self, page_name: str):
        """Switches active view page frame."""
        if page_name not in self.pages:
            return

        if self.current_page_name and self.current_page_name in self.pages:
            self.pages[self.current_page_name].pack_forget()

        for key, btn in self.sidebar_buttons.items():
            if key == page_name:
                btn.config(bg=Theme.PRIMARY, fg="#FFFFFF")
            else:
                btn.config(bg=Theme.BG_SIDEBAR, fg=Theme.TEXT_SIDEBAR)

        self.pages[page_name].pack(fill="both", expand=True)
        self.current_page_name = page_name
