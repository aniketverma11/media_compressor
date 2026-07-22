import os

def format_size(bytes_size: float) -> str:
    """Converts bytes into human-readable size string (KB, MB, GB)."""
    if bytes_size <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(bytes_size)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.2f} {units[i]}"

def get_file_size_bytes(file_path: str) -> int:
    """Returns size of file in bytes, or 0 if invalid."""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def is_video_file(file_path: str) -> bool:
    """Basic extension check for video files."""
    valid_exts = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".m4v"}
    ext = os.path.splitext(file_path)[1].lower()
    return ext in valid_exts

def is_image_file(file_path: str) -> bool:
    """Basic extension check for image files."""
    valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".avif"}
    ext = os.path.splitext(file_path)[1].lower()
    return ext in valid_exts

def ensure_dir(dir_path: str) -> str:
    """Ensures directory exists and returns absolute path."""
    abs_path = os.path.abspath(dir_path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path
