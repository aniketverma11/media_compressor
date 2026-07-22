# MediaCompressor - Cross-Platform Desktop Compression Utility

A lightweight, modern desktop application built using **Python Tkinter** for fast video and image compression.

🌐 **Official PyPI Package**: [https://pypi.org/project/mediacompressor/](https://pypi.org/project/mediacompressor/)

---

## 📦 Official Installation via Pip

Install directly from PyPI on any computer:

```bash
pip install mediacompressor
```

### Upgrading to Latest Version
```bash
pip install --upgrade mediacompressor
```

---

## 🚀 How to Run

Once installed, launch the application from **any terminal or command prompt**:

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

## 💻 Alternative Installation via GitHub

```bash
pip install git+https://github.com/aniketverma11/media_compressor.git
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
