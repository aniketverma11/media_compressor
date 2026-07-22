import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from mediacompressor.ui.theme import Theme
from mediacompressor.ui.components import HeaderWidget, FilePickerWidget, ProgressBarWidget, LogConsoleWidget
from mediacompressor.core.image_compressor import ImageCompressor, ImageInfo, ImageCompressionOptions, ImageBatchResult
from mediacompressor.utils.file_utils import format_size

class ImagePage(tk.Frame):
    """Image Compression module view tab."""

    def __init__(self, parent, image_compressor: ImageCompressor, log_queue):
        super().__init__(parent, bg=Theme.BG_DARK)
        self.compressor = image_compressor
        self.log_queue = log_queue

        self.selected_files: List[str] = []
        self.is_processing = False
        self.cancel_requested = False

        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=Theme.BG_DARK)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        header = HeaderWidget(
            container,
            title="Image Compression",
            subtitle="Compress single or batch images with quality adjustment, smart target sizing, and multi-format conversion."
        )
        header.pack(fill="x")

        # Content Frame
        content_frame = tk.Frame(container, bg=Theme.BG_DARK)
        content_frame.pack(fill="both", expand=True)

        # Left Column: File selection & Image Batch Table/List
        left_col = tk.Frame(content_frame, bg=Theme.BG_CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)

        # Multi-file Picker
        self.file_picker = FilePickerWidget(
            left_col,
            label_text="Select Image Files (Single or Batch):",
            mode="multi_file",
            file_types=[("Image Files", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.avif"), ("All Files", "*.*")],
            on_select_callback=self._on_images_selected
        )
        self.file_picker.pack(fill="x", padx=12, pady=12)

        # Selected Files Info Card / Treeview
        files_card = tk.LabelFrame(
            left_col,
            text=" Selected Image Queue ",
            font=Theme.FONT_SUBTITLE,
            fg=Theme.PRIMARY,
            bg=Theme.BG_CARD,
            bd=1,
            relief="solid",
            highlightthickness=0
        )
        files_card.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Listbox for files
        list_frame = tk.Frame(files_card, bg=Theme.BG_INPUT)
        list_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.file_listbox = tk.Listbox(
            list_frame,
            font=Theme.FONT_MONO,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_MAIN,
            selectbackground=Theme.PRIMARY,
            selectforeground="#FFFFFF",
            relief="flat",
            bd=0
        )
        self.file_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, command=self.file_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        self.lbl_batch_summary = tk.Label(
            files_card, text="Total Files: 0 | Total Size: 0 B", font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, anchor="w"
        )
        self.lbl_batch_summary.pack(fill="x", padx=8, pady=(0, 6))

        # Output Folder Picker
        default_out_dir = os.path.abspath(os.path.join("downloads", "compressed_images"))
        os.makedirs(default_out_dir, exist_ok=True)

        self.out_picker = FilePickerWidget(
            left_col,
            label_text="Output Destination Folder:",
            mode="folder",
            on_select_callback=None
        )
        self.out_picker.set_value(default_out_dir)
        self.out_picker.pack(fill="x", padx=12, pady=(0, 12))

        # Right Column: Compression Options & Settings Card
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

        # Quality Slider
        tk.Label(opts_card, text="Image Quality (1-100):", font=Theme.FONT_BODY, fg=Theme.TEXT_MAIN, bg=Theme.BG_CARD).pack(anchor="w", padx=8, pady=(8, 2))
        
        slider_frame = tk.Frame(opts_card, bg=Theme.BG_CARD)
        slider_frame.pack(fill="x", padx=8, pady=2)

        self.quality_var = tk.IntVar(value=80)
        self.slider_quality = tk.Scale(
            slider_frame,
            from_=5,
            to=100,
            orient="horizontal",
            variable=self.quality_var,
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MAIN,
            bg=Theme.BG_CARD,
            troughcolor=Theme.BG_INPUT,
            activebackground=Theme.PRIMARY,
            highlightthickness=0,
            command=lambda v: self._on_options_changed()
        )
        self.slider_quality.pack(side="left", fill="x", expand=True)

        self.lbl_quality_val = tk.Label(slider_frame, text="80%", font=Theme.FONT_SUBTITLE, fg=Theme.PRIMARY, bg=Theme.BG_CARD, width=6)
        self.lbl_quality_val.pack(side="right", padx=(8, 0))

        # Output Format & Resize Mode
        dd_frame = tk.Frame(opts_card, bg=Theme.BG_CARD)
        dd_frame.pack(fill="x", padx=8, pady=8)

        tk.Label(dd_frame, text="Output Format:", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).grid(row=0, column=0, sticky="w", pady=2)
        self.cbo_fmt = ttk.Combobox(dd_frame, values=["JPEG", "PNG", "WEBP"], state="readonly", width=12)
        self.cbo_fmt.set("JPEG")
        self.cbo_fmt.grid(row=0, column=1, padx=(4, 16), pady=2)
        self.cbo_fmt.bind("<<ComboboxSelected>>", lambda e: self._on_options_changed())

        tk.Label(dd_frame, text="Resize Dimension:", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).grid(row=0, column=2, sticky="w", pady=2)
        self.cbo_resize = ttk.Combobox(dd_frame, values=["Original", "75%", "50%", "Custom Max 1920px", "Custom Max 1080px"], state="readonly", width=16)
        self.cbo_resize.set("Original")
        self.cbo_resize.grid(row=0, column=3, padx=(4, 0), pady=2)
        self.cbo_resize.bind("<<ComboboxSelected>>", lambda e: self._on_options_changed())

        # Target Size (Optional)
        target_frame = tk.Frame(opts_card, bg=Theme.BG_CARD)
        target_frame.pack(fill="x", padx=8, pady=8)

        tk.Label(target_frame, text="Optional Target Size (KB per image):", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).pack(anchor="w", pady=(0, 2))
        
        target_in_frame = tk.Frame(target_frame, bg=Theme.BG_CARD)
        target_in_frame.pack(fill="x")

        self.entry_target_kb = tk.Entry(target_in_frame, font=Theme.FONT_BODY, width=14, bg=Theme.BG_INPUT, fg=Theme.TEXT_MAIN, insertbackground=Theme.TEXT_MAIN)
        self.entry_target_kb.pack(side="left", ipady=2)
        self.entry_target_kb.bind("<KeyRelease>", lambda e: self._on_options_changed())

        tk.Label(target_in_frame, text="(Leave blank for quality slider)", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD).pack(side="left", padx=(8, 0))

        # Estimation Box
        self.est_box = tk.LabelFrame(
            right_col, text=" Estimation & Feasibility ", font=Theme.FONT_SMALL, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD
        )
        self.est_box.pack(fill="x", padx=12, pady=(0, 12))

        self.lbl_est_status = tk.Label(
            self.est_box, text="Select image(s) to view size estimation.", font=Theme.FONT_BODY, fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD, anchor="w", justify="left", wrap=350
        )
        self.lbl_est_status.pack(fill="x", padx=8, pady=8)

        # Bottom Progress Bar & Buttons
        bot_frame = tk.Frame(container, bg=Theme.BG_DARK)
        bot_frame.pack(fill="x", pady=(8, 0))

        self.progress_bar = ProgressBarWidget(bot_frame)
        self.progress_bar.pack(fill="x", pady=(0, 8))

        btn_bar = tk.Frame(bot_frame, bg=Theme.BG_DARK)
        btn_bar.pack(fill="x")

        self.btn_start = tk.Button(
            btn_bar, text="Start Image Compression", font=Theme.FONT_SUBTITLE, bg=Theme.PRIMARY, fg="#FFFFFF", activebackground=Theme.PRIMARY_HOVER, relief="flat", bd=0, cursor="hand2", command=self._start_compression
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

    def _on_images_selected(self, paths):
        if not paths:
            return

        if isinstance(paths, str):
            paths = [paths]

        self.selected_files = [p for p in paths if os.path.exists(p)]
        self.file_listbox.delete(0, "end")

        total_bytes = 0
        for p in self.selected_files:
            fname = os.path.basename(p)
            size_b = os.path.getsize(p)
            total_bytes += size_b
            self.file_listbox.insert("end", f"{fname} ({format_size(size_b)})")

        self.lbl_batch_summary.config(
            text=f"Total Files: {len(self.selected_files)} | Total Size: {format_size(total_bytes)}"
        )
        self.log_console.log(f"Loaded {len(self.selected_files)} image file(s) ({format_size(total_bytes)})")
        self._on_options_changed()

    def _on_options_changed(self):
        q = self.quality_var.get()
        self.lbl_quality_val.config(text=f"{q}%")

        if not self.selected_files:
            return

        opts = self._build_options()
        if not opts or not self.selected_files:
            return

        # Estimate first image
        ok, info, _ = self.compressor.probe_image(self.selected_files[0])
        if ok and info:
            achievable, est_kb, msg = self.compressor.estimate_output_size(info, opts)
            if achievable:
                self.lbl_est_status.config(
                    text=f"Est. size per image: ~{est_kb:.1f} KB (Format: {opts.output_format}, Quality: {opts.quality}%).",
                    fg=Theme.SUCCESS
                )
            else:
                self.lbl_est_status.config(text=msg, fg=Theme.WARNING)

    def _build_options(self) -> Optional[ImageCompressionOptions]:
        if not self.selected_files:
            return None

        out_dir = self.out_picker.get_value()
        if not out_dir:
            out_dir = os.path.dirname(self.selected_files[0])

        target_kb = None
        kb_str = self.entry_target_kb.get().strip()
        if kb_str:
            try:
                target_kb = float(kb_str)
            except ValueError:
                pass

        resize_mode = self.cbo_resize.get()
        custom_max = None
        if "1920" in resize_mode:
            resize_mode = "Custom"
            custom_max = 1920
        elif "1080" in resize_mode:
            resize_mode = "Custom"
            custom_max = 1080

        return ImageCompressionOptions(
            input_paths=self.selected_files,
            output_dir=out_dir,
            output_format=self.cbo_fmt.get(),
            quality=self.quality_var.get(),
            target_size_kb=target_kb,
            resize_mode=resize_mode,
            custom_max_dim=custom_max
        )

    def _start_compression(self):
        if self.is_processing:
            return

        if not self.selected_files:
            messagebox.showwarning("No Images Selected", "Please select image file(s) first.")
            return

        opts = self._build_options()
        if not opts:
            return

        self.is_processing = True
        self.cancel_requested = False
        self.btn_start.config(state="disabled")
        self.btn_cancel.config(state="normal")
        self.btn_clear.config(state="disabled")

        self.log_console.log(f"Starting batch compression of {len(self.selected_files)} images...")

        def _worker():
            def _prog(curr, total, status_msg):
                pct = (curr / total) * 100.0
                self.log_queue.put(("IMAGE_PROGRESS", (pct, status_msg, f"{curr}/{total} files")))

            def _check_cancel():
                return self.cancel_requested

            res = self.compressor.compress_batch(opts, progress_callback=_prog, cancel_check=_check_cancel)
            self.log_queue.put(("IMAGE_COMPLETE", res))

        threading.Thread(target=_worker, daemon=True).start()

    def _cancel_compression(self):
        if self.is_processing:
            self.cancel_requested = True
            self.log_console.log("Cancelling image compression batch...")
            self.btn_cancel.config(state="disabled")

    def handle_queue_event(self, event_type: str, data):
        if event_type == "IMAGE_PROGRESS":
            pct, msg, speed = data
            self.progress_bar.update_progress(pct, msg, speed, "--:--")
        elif event_type == "IMAGE_COMPLETE":
            res: ImageBatchResult = data
            self.is_processing = False
            self.btn_start.config(state="normal")
            self.btn_cancel.config(state="disabled")
            self.btn_clear.config(state="normal")

            self.progress_bar.update_progress(100.0, "Batch Compression Complete!", "--", "00:00")
            msg = (
                f"Batch compression complete in {res.time_taken_sec:.1f} seconds!\n\n"
                f"Processed: {res.success_count} succeeded, {res.failed_count} failed\n"
                f"Original Total: {format_size(res.total_original_bytes)}\n"
                f"Compressed Total: {format_size(res.total_compressed_bytes)}\n"
                f"Total Space Saved: {format_size(res.space_saved_bytes)} ({res.overall_ratio_pct:.1f}% reduction)"
            )
            log_msg = msg.replace('\n\n', ' | ').replace('\n', ' | ')
            self.log_console.log(f"SUCCESS: {log_msg}")
            messagebox.showinfo("Image Batch Complete", msg)

    def _clear_all(self):
        if self.is_processing:
            return
        self.selected_files = []
        self.file_picker.set_value("")
        self.file_listbox.delete(0, "end")
        self.lbl_batch_summary.config(text="Total Files: 0 | Total Size: 0 B")
        self.lbl_est_status.config(text="Select image(s) to view size estimation.", fg=Theme.TEXT_MUTED)
        self.progress_bar.reset()
        self.log_console.clear()
