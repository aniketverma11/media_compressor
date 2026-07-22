# MediaCompressor - Installable Cross-Platform Desktop Utility

A lightweight, modern desktop application built using **Python Tkinter** for fast video and image compression.

---

## Installation via Pip

Install locally in editable mode or as a package:

```bash
cd D:\aniket\compressor
pip install -e .
```

Or standard pip install:

```bash
pip install D:\aniket\compressor
```

---

## How to Run

Once installed, launch the application from **any terminal or command prompt** using:

```bash
mediacompressor
```

or:

```bash
media-compressor
```

or via python module:

```bash
python -m mediacompressor
```

---

## Key Features

1. **Video Compression**:
   - Accepts MP4, MKV, MOV, AVI, WebM, and FLV files.
   - Enter target file size (e.g. 5 MB) or percentage reduction (e.g. 60% smaller).
   - Feasibility & bitrate estimation engine (warns if target size will cause severe degradation and suggests realistic alternatives).
   - Codec selection: H.264 (`libx264`), H.265 (`libx265`), AV1 (`libsvtav1`).
   - Resolution scaling (1080p, 720p, 480p, 360p) and FPS controls.
   - Real-time FFmpeg progress tracking (percentage, speed, ETA).

2. **Image Compression**:
   - Single and batch image processing (JPEG, PNG, WebP).
   - Quality slider (1-100), dimension resizing, and smart target size fitting (binary search quality fitting).
   - Shows space saved, compression ratios, and image metadata.

3. **Auto Dependency & FFmpeg Management**:
   - Automatically detects missing Python packages (`Pillow`, `imageio-ffmpeg`) and installs them.
   - Auto-detects local or system FFmpeg binary; downloads static build if missing.

4. **100% Responsive UI**:
   - Thread-safe background execution (`threading.Thread` + `queue.Queue`).
   - Modern Dark Slate theme built entirely with native Tkinter & ttk widgets.

---

## Package Directory Structure

```text
D:\aniket\compressor\
│
├── pyproject.toml              # Build metadata & dependency declaration
├── setup.py                    # Pip setup installer script & console scripts
├── README.md                   # Project documentation
│
└── mediacompressor/            # Main Python Package
    ├── __init__.py
    ├── __main__.py             # Python -m launcher
    ├── cli.py                  # Entry point for console script (mediacompressor)
    ├── app.py                  # Direct script entry point
    │
    ├── ui/                     # User Interface Layer
    │   ├── main_window.py      # Main layout & thread-safe polling loop
    │   ├── video_page.py       # Video compressor view
    │   ├── image_page.py       # Image compressor view
    │   ├── components.py       # Reusable widgets
    │   └── theme.py            # Color palette & fonts
    │
    ├── core/                   # Core Engines
    │   ├── dependency_manager.py
    │   ├── ffmpeg_manager.py
    │   ├── video_compressor.py
    │   └── image_compressor.py
    │
    └── utils/                  # Utilities
        ├── logger.py
        ├── file_utils.py
        └── validators.py
```
