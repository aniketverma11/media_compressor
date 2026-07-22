import os
import sys
import shutil
import platform
import zipfile
import tarfile
import urllib.request
from typing import Callable, Tuple, Optional

FFMPEG_DOWNLOAD_URLS = {
    "Windows": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n6.1-latest-win64-gpl-6.1.zip",
    "Linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
    "Darwin": "https://evermeet.cx/ffmpeg/ffmpeg-6.1.zip"
}

class FFmpegManager:
    """Manages system and local FFmpeg / FFprobe binaries cross-platform."""

    def __init__(self, base_dir: str = "downloads"):
        self.base_dir = os.path.abspath(base_dir)
        self.local_ffmpeg_dir = os.path.join(self.base_dir, "ffmpeg")
        os.makedirs(self.local_ffmpeg_dir, exist_ok=True)
        self._ffmpeg_path: Optional[str] = None
        self._ffprobe_path: Optional[str] = None

    def get_paths(self) -> Tuple[Optional[str], Optional[str]]:
        """Returns tuple of (ffmpeg_path, ffprobe_path) if available."""
        if self._ffmpeg_path and self._ffprobe_path:
            return self._ffmpeg_path, self._ffprobe_path

        exe_suffix = ".exe" if platform.system() == "Windows" else ""

        # 1. Check local downloads directory
        local_ffmpeg = self._find_in_dir(self.local_ffmpeg_dir, f"ffmpeg{exe_suffix}")
        local_ffprobe = self._find_in_dir(self.local_ffmpeg_dir, f"ffprobe{exe_suffix}")

        if local_ffmpeg:
            self._ffmpeg_path = local_ffmpeg
            self._ffprobe_path = local_ffprobe or local_ffmpeg  # fallback to ffmpeg if probe missing

        # 2. Check system PATH
        if not self._ffmpeg_path:
            sys_ffmpeg = shutil.which("ffmpeg")
            sys_ffprobe = shutil.which("ffprobe")
            if sys_ffmpeg:
                self._ffmpeg_path = sys_ffmpeg
                self._ffprobe_path = sys_ffprobe or sys_ffmpeg

        # 3. Check imageio_ffmpeg module
        if not self._ffmpeg_path:
            try:
                import imageio_ffmpeg
                img_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
                if img_ffmpeg and os.path.exists(img_ffmpeg):
                    self._ffmpeg_path = img_ffmpeg
                    # Check for ffprobe alongside imageio_ffmpeg or system
                    probe_candidate = os.path.join(os.path.dirname(img_ffmpeg), f"ffprobe{exe_suffix}")
                    if os.path.exists(probe_candidate):
                        self._ffprobe_path = probe_candidate
                    else:
                        self._ffprobe_path = shutil.which("ffprobe") or img_ffmpeg
            except ImportError:
                pass

        return self._ffmpeg_path, self._ffprobe_path

    def _find_in_dir(self, directory: str, filename: str) -> Optional[str]:
        """Recursively searches for executable filename in directory."""
        for root, _, files in os.walk(directory):
            if filename.lower() in [f.lower() for f in files]:
                full_path = os.path.join(root, filename)
                # Make executable on Unix
                if platform.system() != "Windows":
                    try:
                        os.chmod(full_path, 0o755)
                    except OSError:
                        pass
                return full_path
        return None

    def ensure_ffmpeg(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Verifies FFmpeg exists, or downloads local binary if missing."""
        ffmpeg_p, ffprobe_p = self.get_paths()
        if ffmpeg_p:
            if progress_callback:
                progress_callback(f"FFmpeg located: {ffmpeg_p}")
            return True

        # Need to download FFmpeg
        system_name = platform.system()
        if system_name not in FFMPEG_DOWNLOAD_URLS:
            if progress_callback:
                progress_callback(f"Unsupported OS for automatic FFmpeg download: {system_name}")
            return False

        url = FFMPEG_DOWNLOAD_URLS[system_name]
        archive_name = os.path.basename(url)
        archive_path = os.path.join(self.base_dir, archive_name)

        if progress_callback:
            progress_callback(f"FFmpeg not found. Downloading static build for {system_name}...")

        try:
            # Download with progress feedback
            def _report(block_num, block_size, total_size):
                if total_size > 0 and progress_callback:
                    percent = min(100, int(block_num * block_size * 100 / total_size))
                    if block_num % 10 == 0:
                        progress_callback(f"Downloading FFmpeg... {percent}%")

            urllib.request.urlretrieve(url, archive_path, reporthook=_report)
            if progress_callback:
                progress_callback("Download complete. Extracting FFmpeg...")

            # Extract archive
            if archive_path.endswith(".zip"):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(self.local_ffmpeg_dir)
            elif archive_path.endswith((".tar.xz", ".tar.gz", ".tgz")):
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(self.local_ffmpeg_dir)

            # Clean archive
            if os.path.exists(archive_path):
                os.remove(archive_path)

            # Re-check paths
            self._ffmpeg_path = None
            self._ffprobe_path = None
            ffmpeg_p, _ = self.get_paths()

            if ffmpeg_p:
                if progress_callback:
                    progress_callback(f"FFmpeg successfully installed to {ffmpeg_p}")
                return True
            else:
                if progress_callback:
                    progress_callback("Failed to locate FFmpeg binary after extraction.")
                return False

        except Exception as e:
            if progress_callback:
                progress_callback(f"Failed to download/extract FFmpeg: {e}")
            return False
