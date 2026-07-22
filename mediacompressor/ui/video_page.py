import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from mediacompressor.ui.theme import Theme
from mediacompressor.ui.components import HeaderWidget, FilePickerWidget, ProgressBarWidget, LogConsoleWidget
from mediacompressor.core.video_compressor import VideoCompressor, VideoInfo, CompressionOptions, CompressionResult
from mediacompressor.utils.file_utils import format_size

class VideoPage(tk.Frame):
    """Video Compression module view tab."""

    def __init__(self, parent, video_compressor: VideoCompressor, log_queue):
        super().__init__(parent, bg=Theme.BG_DARK)
        self.compressor = video_compressor
        self.log_queue = log_queue

        self.current_video_info: Optional[VideoInfo] = None
        self.is_processing = False
        self.cancel_requested = False

        self._build_ui()

    def _build_ui(self):
        # Container frame
        container = tk.Frame(self, bg=Theme.BG_DARK)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        header = HeaderWidget(
            container,
            title="Video Compression",
            subtitle="Compress MP4, MKV, MOV videos with target filesize estimation & FFmpeg hardware/software codecs."
        )
        header.pack(fill="x")

        # Scrollable / Grid Main Layout
        content_frame = tk.Frame(container, bg=Theme.BG_DARK)
        content_frame.pack(fill="both", expand=True)

        # Left Column: File selection & Video Information Card
        left_col = tk.Frame(content_frame, bg=Theme.BG_CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)

        # File Picker
        self.file_picker = FilePickerWidget(
            left_col,
            label_text="Select Video File:",
            mode="file",
            file_types=[("Video Files", "*.mp4 *.mkv *.mov *.avi *.webm *.flv *.wmv"), ("All Files", "*.*")],
            on_select_callback=self._on_video_selected
        )
        self.file_picker.pack(fill="x", padx=12, pady=12)

        # Video Info Card
        info_card = tk.LabelFrame(
            left_col,
            text=" Selected Video Metadata ",
            font=Theme.FONT_SUBTITLE,
            fg=Theme.PRIMARY,
            bg=Theme.BG_CARD,
            bd=1,
            relief="solid",
            highlightthickness=0
        )
        info_card.pack(fill="x", padx=12, pady=(0, 12))

        self.lbl_info_name = tk.Label(info_card, text="File Name: --", font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, anchor="w")
        self.lbl_info_name.pack(fill="x", padx=8, pady=2)

        self.lbl_info_size = tk.Label(info_card, text="File Size: --", font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, anchor="w")
        self.lbl_info_size.pack(fill="x", padx=8, pady=2)

        self.lbl_info_res = tk.Label(info_card, text="Resolution: --", font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, anchor="w")
        self.lbl_info_res.pack(fill="x", padx=8, pady=2)

        self.lbl_info_dur = tk.Label(info_card, text="Duration: --", font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, anchor="w")
        self.lbl_info_dur.pack(fill="x", padx=8, pady=2)

        self.lbl_info_br = tk.Label(info_card, text="Bitrate: --", font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, anchor="w")
        self.lbl_info_br.pack(fill="x", padx=8, pady=(2, 8))

        # Output Folder Picker
        default_out_dir = os.path.abspath(os.path.join("downloads", "compressed_videos"))
        os.makedirs(default_out_dir, exist_ok=True)

        self.out_picker = FilePickerWidget(
            left_col,
            label_text="Output Destination Folder:",
            mode="folder",
            on_select_callback=None
        )
        self.out_picker.set_value(default_out_dir)
        self.out_picker.pack(fill="x", padx=12, pady=(0, 12))

        # Right Column: Compression Options & Estimation Card
        right_col = tk.Frame(content_frame, bg=Theme.BG_CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        right_col.pack(side="right", fill="both", expand=True, padx=(8, 0), pady=4)

        opts_card = tk.LabelFrame(
            right_col,
            text=" Compression Settings ",
            font=Theme.FONT_SUBTITLE,
            fg=Theme.PRIMARY,
            bg=Theme.BG_CARD,
            bd=1,
            relief="solid",
            highlightthickness=0
        )
        opts_card.pack(fill="x", padx=12, pady=12)

        # Target Size Mode Selection
        self.target_mode_var = tk.StringVar(value="size")
        
        radio_frame = tk.Frame(opts_card, bg=Theme.BG_CARD)
        radio_frame.pack(fill="x", padx=8, pady=4)

        r1 = tk.Radiobutton(
            radio_frame,
            text="Target Size (MB)",
            variable=self.target_mode_var,
            value="size",
            font=Theme.FONT_BODY,
            fg=Theme.TEXT_MAIN,
            bg=Theme.BG_CARD,
            selectcolor=Theme.BG_DARK,
            activebackground=Theme.BG_CARD,
            activeforeground=Theme.TEXT_MAIN,
            command=self._on_options_changed
        )
        r1.pack(side="left", padx=(0, 16))

        r2 = tk.Radiobutton(
            radio_frame,
            text="Compression % (Smaller)",
            variable=self.target_mode_var,
            value="pct",
            font=Theme.FONT_BODY,
            fg=Theme.TEXT_MAIN,
            bg=Theme.BG_CARD,
            selectcolor=Theme.BG_DARK,
            activebackground=Theme.BG_CARD,
            activeforeground=Theme.TEXT_MAIN,
            command=self._on_options_changed
        )
        r2.pack(side="left")

        # Entry for Target Value
        val_frame = tk.Frame(opts_card, bg=Theme.BG_CARD)
        val_frame.pack(fill="x", padx=8, pady=4)

        self.lbl_target_prompt = tk.Label(
            val_frame, text="Desired Size (MB):", font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD
        )
        self.lbl_target_prompt.pack(side="left", padx=(0, 8))

        self.entry_target_val = tk.Entry(
            val_frame, font=Theme.FONT_BODY, width=12, bg=Theme.BG_INPUT, fg=Theme.TEXT_MAIN, insertbackground=Theme.TEXT_MAIN
        )
        self.entry_target_val.insert(0, "10.0")
        self.entry_target_val.pack(side="left", ipady=2)
        self.entry_target_val.bind("<KeyRelease>", lambda e: self._on_options_changed())

        btn_est = tk.Button(
            val_frame, text="Estimate", font=Theme.FONT_SMALL, bg=Theme.PRIMARY, fg="#FFFFFF", relief="flat", bd=0, command=self._on_options_changed
        )
        btn_est.pack(side="left", padx=(8, 0), ipadx=8, ipady=2)

        # Resolution, FPS, Codec dropdowns
        dd_frame = tk.Frame(opts_card, bg=Theme.BG_CARD)
        dd_frame.pack(fill="x", padx=8, pady=8)

        # Resolution
        tk.Label(dd_frame, text="Resolution:", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).grid(row=0, column=0, sticky="w", pady=2)
        self.cbo_res = ttk.Combobox(dd_frame, values=["Original", "1080p", "720p", "480p", "360p"], state="readonly", width=12)
        self.cbo_res.set("Original")
        self.cbo_res.grid(row=0, column=1, padx=(4, 16), pady=2)
        self.cbo_res.bind("<<ComboboxSelected>>", lambda e: self._on_options_changed())

        # FPS
        tk.Label(dd_frame, text="FPS:", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).grid(row=0, column=2, sticky="w", pady=2)
        self.cbo_fps = ttk.Combobox(dd_frame, values=["Original", "60", "30", "24", "15"], state="readonly", width=12)
        self.cbo_fps.set("Original")
        self.cbo_fps.grid(row=0, column=3, padx=(4, 0), pady=2)
        self.cbo_fps.bind("<<ComboboxSelected>>", lambda e: self._on_options_changed())

        # Codec
        tk.Label(dd_frame, text="Codec:", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).grid(row=1, column=0, sticky="w", pady=4)
        self.cbo_codec = ttk.Combobox(dd_frame, values=["H.264", "H.265", "AV1"], state="readonly", width=12)
        self.cbo_codec.set("H.264")
        self.cbo_codec.grid(row=1, column=1, padx=(4, 16), pady=4)
        self.cbo_codec.bind("<<ComboboxSelected>>", lambda e: self._on_options_changed())

        # Estimation / Achievability Warning Box
        self.est_box = tk.LabelFrame(
            right_col, text=" Estimation & Feasibility ", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD
        )
        self.est_box.pack(fill="x", padx=12, pady=(0, 12))

        self.lbl_est_bitrate = tk.Label(self.est_box, text="Est. Video Bitrate: --", font=Theme.FONT_BODY, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD, anchor="w")
        self.lbl_est_bitrate.pack(fill="x", padx=8, pady=2)

        self.lbl_est_status = tk.Label(
            self.est_box, text="Select a video file to run estimation.", font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, anchor="w", justify="left", wrap=350
        )
        self.lbl_est_status.pack(fill="x", padx=8, pady=(2, 6))

        # Bottom Progress Bar & Action Buttons
        bot_frame = tk.Frame(container, bg=Theme.BG_DARK)
        bot_frame.pack(fill="x", pady=(8, 0))

        self.progress_bar = ProgressBarWidget(bot_frame)
        self.progress_bar.pack(fill="x", pady=(0, 8))

        btn_bar = tk.Frame(bot_frame, bg=Theme.BG_DARK)
        btn_bar.pack(fill="x")

        self.btn_start = tk.Button(
            btn_bar, text="Start Video Compression", font=Theme.FONT_SUBTITLE, bg=Theme.PRIMARY, fg="#FFFFFF", activebackground=Theme.PRIMARY_HOVER, relief="flat", bd=0, cursor="hand2", command=self._start_compression
        )
        self.btn_start.pack(side="left", ipadx=16, ipady=6)

        self.btn_cancel = tk.Button(
            btn_bar, text="Cancel", font=Theme.FONT_SUBTITLE, bg=Theme.DANGER, fg="#FFFFFF", relief="flat", bd=0, cursor="hand2", state="disabled", command=self._cancel_compression
        )
        self.btn_cancel.pack(side="left", padx=8, ipadx=16, ipady=6)

        self.btn_clear = tk.Button(
            btn_bar, text="Clear", font=Theme.FONT_SUBTITLE, bg=Theme.BORDER, fg=Theme.TEXT_MAIN, relief="flat", bd=0, cursor="hand2", command=self._clear_all
        )
        self.btn_clear.pack(side="right", ipadx=16, ipady=6)

        # Log Console
        self.log_console = LogConsoleWidget(container, height=4)
        self.log_console.pack(fill="x", pady=(8, 0))

    def _on_video_selected(self, file_path: str):
        if not file_path or not os.path.exists(file_path):
            return

        self.log_console.log(f"Probing metadata for: {os.path.basename(file_path)}...")
        ok, info, err = self.compressor.probe_video(file_path)
        if not ok or not info:
            messagebox.showerror("Probe Error", f"Failed to probe video file:\n{err}")
            self.log_console.log(f"Error probing video: {err}")
            return

        self.current_video_info = info
        self.lbl_info_name.config(text=f"File Name: {info.file_name}")
        self.lbl_info_size.config(text=f"File Size: {info.file_size_str}")
        self.lbl_info_res.config(text=f"Resolution: {info.width} x {info.height}")
        dur_m, dur_s = int(info.duration_sec // 60), int(info.duration_sec % 60)
        self.lbl_info_dur.config(text=f"Duration: {dur_m:02d}:{dur_s:02d} ({info.duration_sec:.1f}s)")
        self.lbl_info_br.config(text=f"Bitrate: {info.bitrate_kbps:.1f} kbps ({info.codec_name})")

        self.log_console.log(f"Loaded {info.file_name} ({info.width}x{info.height}, {info.file_size_str})")
        self._on_options_changed()

    def _on_options_changed(self):
        mode = self.target_mode_var.get()
        if mode == "size":
            self.lbl_target_prompt.config(text="Desired Size (MB):")
        else:
            self.lbl_target_prompt.config(text="Compression %:")

        if not self.current_video_info:
            return

        opts = self._build_options()
        if not opts:
            return

        achievable, video_br, target_mb, msg, suggested_mb = self.compressor.estimate_bitrate_and_feasibility(
            self.current_video_info, opts
        )

        self.lbl_est_bitrate.config(text=f"Est. Video Bitrate: {video_br:.1f} kbps | Target Output: {target_mb:.2f} MB")

        if achievable:
            self.lbl_est_status.config(text=f"Target size achievable. Quality expected to be good.", fg=Theme.SUCCESS)
        else:
            self.lbl_est_status.config(
                text=f"{msg}\nSuggested realistic target size: {suggested_mb:.2f} MB", fg=Theme.WARNING
            )

    def _build_options(self) -> Optional[CompressionOptions]:
        if not self.current_video_info:
            return None

        in_path = self.current_video_info.file_path
        out_dir = self.out_picker.get_value()
        if not out_dir:
            out_dir = os.path.dirname(in_path)

        fname_base = os.path.splitext(self.current_video_info.file_name)[0]
        out_path = os.path.join(out_dir, f"{fname_base}_compressed.mp4")

        target_mode = self.target_mode_var.get()
        val_str = self.entry_target_val.get().strip()

        target_mb = None
        target_pct = None

        try:
            val = float(val_str)
            if target_mode == "size":
                target_mb = val
            else:
                target_pct = val
        except ValueError:
            return None

        return CompressionOptions(
            input_path=in_path,
            output_path=out_path,
            target_size_mb=target_mb,
            target_percentage=target_pct,
            resolution_scale=self.cbo_res.get(),
            fps_choice=self.cbo_fps.get(),
            video_codec=self.cbo_codec.get()
        )

    def _start_compression(self):
        if self.is_processing:
            return

        if not self.current_video_info:
            messagebox.showwarning("No Video Selected", "Please select a video file first.")
            return

        opts = self._build_options()
        if not opts:
            messagebox.showerror("Invalid Input", "Please enter a valid target size (MB) or percentage (%).")
            return

        self.is_processing = True
        self.cancel_requested = False
        self.btn_start.config(state="disabled")
        self.btn_cancel.config(state="normal")
        self.btn_clear.config(state="disabled")

        self.log_console.log(f"Starting video compression: {opts.input_path} -> {opts.output_path}")

        def _worker():
            def _prog(pct, speed, eta):
                self.log_queue.put(("VIDEO_PROGRESS", (pct, speed, eta)))

            def _check_cancel():
                return self.cancel_requested

            res = self.compressor.compress_video(
                self.current_video_info, opts, progress_callback=_prog, cancel_check=_check_cancel
            )
            self.log_queue.put(("VIDEO_COMPLETE", res))

        threading.Thread(target=_worker, daemon=True).start()

    def _cancel_compression(self):
        if self.is_processing:
            self.cancel_requested = True
            self.log_console.log("Cancelling compression request...")
            self.btn_cancel.config(state="disabled")

    def handle_queue_event(self, event_type: str, data):
        """Called safely on main Tkinter UI thread."""
        if event_type == "VIDEO_PROGRESS":
            pct, speed, eta = data
            self.progress_bar.update_progress(pct, f"Compressing video...", speed, eta)
        elif event_type == "VIDEO_COMPLETE":
            res: CompressionResult = data
            self.is_processing = False
            self.btn_start.config(state="normal")
            self.btn_cancel.config(state="disabled")
            self.btn_clear.config(state="normal")

            if res.success:
                self.progress_bar.update_progress(100.0, "Compression Complete!", "--", "00:00")
                saved_bytes = max(0, res.original_size_bytes - res.compressed_size_bytes)
                msg = (
                    f"Video compressed successfully in {res.time_taken_sec:.1f} seconds!\n\n"
                    f"Original Size: {format_size(res.original_size_bytes)}\n"
                    f"Compressed Size: {format_size(res.compressed_size_bytes)}\n"
                    f"Space Saved: {format_size(saved_bytes)} ({res.compression_ratio_pct:.1f}% reduction)"
                )
                log_msg = msg.replace('\n\n', ' | ').replace('\n', ' | ')
                self.log_console.log(f"SUCCESS: {log_msg}")
                messagebox.showinfo("Compression Finished", msg)
            else:
                self.progress_bar.update_progress(0.0, "Compression Failed", "--", "--:--")
                self.log_console.log(f"FAILED: {res.error_message}")
                if not self.cancel_requested:
                    messagebox.showerror("Compression Failed", f"An error occurred:\n{res.error_message}")

    def _clear_all(self):
        if self.is_processing:
            return
        self.current_video_info = None
        self.file_picker.set_value("")
        self.lbl_info_name.config(text="File Name: --")
        self.lbl_info_size.config(text="File Size: --")
        self.lbl_info_res.config(text="Resolution: --")
        self.lbl_info_dur.config(text="Duration: --")
        self.lbl_info_br.config(text="Bitrate: --")
        self.lbl_est_bitrate.config(text="Est. Video Bitrate: --")
        self.lbl_est_status.config(text="Select a video file to run estimation.", fg=Theme.TEXT_MUTED)
        self.progress_bar.reset()
        self.log_console.clear()
