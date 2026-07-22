# MediaCompressor - Cross-Platform Desktop Compression Utility

A lightweight, modern desktop application built using **Python Tkinter** for fast video and image compression.

---

## 📦 Direct Installation via GitHub & Pip

Anyone can install the application directly from GitHub using `pip`:

```bash
pip install git+https://github.com/aniketverma11/media_compressor.git
```

### Upgrading to Latest Version from GitHub
```bash
pip install --upgrade git+https://github.com/aniketverma11/media_compressor.git
```

---

## 🚀 How to Run

Once installed, launch the application from **any command prompt or terminal window**:

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

## 💻 Local Development Setup

If you have cloned the repository locally:

```bash
git clone https://github.com/aniketverma11/media_compressor.git
cd media_compressor
pip install -e .
```

---

## ✨ Key Features

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

## 📁 Repository Structure

```text
media_compressor/
│
├── pyproject.toml              # Build metadata & dependency declaration
├── setup.py                    # Pip installer script & console scripts
├── README.md                   # Installation & usage documentation
├── .gitignore                  # Git ignore patterns
│
└── mediacompressor/            # Main Python Package
    ├── __init__.py             # Package version
    ├── __main__.py             # Python -m launcher
    ├── cli.py                  # Entry point for console script (mediacompressor)
    ├── app.py                  # Direct script entry point
    │
    ├── ui/                     # User Interface Layer
    │   ├── main_window.py      # Main layout & thread-safe polling loop
    │   ├── video_page.py       # Video compressor view
    │   ├── image_page.py       # Image compressor view
    │   ├── components.py       # Reusable widgets
    │   └── theme.py            # Dark slate color palette
    │
    ├── core/                   # Processing Engines
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
