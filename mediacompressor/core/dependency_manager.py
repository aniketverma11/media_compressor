import sys
import subprocess
import importlib
from typing import Callable, List, Tuple

# Format: (import_name, pip_package_name)
REQUIRED_PACKAGES: List[Tuple[str, str]] = [
    ("PIL", "Pillow"),
    ("imageio_ffmpeg", "imageio-ffmpeg"),
]

def check_missing_dependencies() -> List[Tuple[str, str]]:
    """Returns list of missing (import_name, pip_name) packages."""
    missing = []
    for imp_name, pip_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(imp_name)
        except ImportError:
            missing.append((imp_name, pip_name))
    return missing

def install_missing_dependencies(progress_callback: Callable[[str], None] | None = None) -> bool:
    """Installs missing packages using sys.executable -m pip install."""
    missing = check_missing_dependencies()
    if not missing:
        if progress_callback:
            progress_callback("All Python dependencies are already installed.")
        return True

    for imp_name, pip_name in missing:
        msg = f"Installing missing dependency: {pip_name}..."
        if progress_callback:
            progress_callback(msg)
        try:
            cmd = [sys.executable, "-m", "pip", "install", pip_name]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            if process.stdout:
                for line in process.stdout:
                    if progress_callback:
                        progress_callback(line.strip())
            process.wait()
            if process.returncode != 0:
                if progress_callback:
                    progress_callback(f"Failed to install {pip_name} (exit code {process.returncode}).")
                return False
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error installing {pip_name}: {e}")
            return False

    if progress_callback:
        progress_callback("All missing dependencies installed successfully.")
    return True
