import json
import urllib.request
from typing import Tuple
from mediacompressor import __version__ as CURRENT_VERSION

PYPI_URL = "https://pypi.org/pypi/mediacompressor/json"

def parse_version_tuple(v_str: str) -> Tuple[int, ...]:
    """Converts version string '1.2.3' to numeric tuple (1, 2, 3)."""
    try:
        clean_v = v_str.strip().lstrip("v")
        return tuple(int(part) for part in clean_v.split(".") if part.isdigit())
    except Exception:
        return (0, 0, 0)

def check_for_updates(timeout_sec: float = 3.0) -> Tuple[bool, str, str]:
    """
    Queries PyPI API in background to check if a newer version is released.
    Returns: (has_update, latest_version, release_notes_url)
    """
    try:
        req = urllib.request.Request(PYPI_URL, headers={"User-Agent": "MediaCompressor-UpdateChecker"})
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                info = data.get("info", {})
                latest_v_str = info.get("version", CURRENT_VERSION)
                
                curr_t = parse_version_tuple(CURRENT_VERSION)
                latest_t = parse_version_tuple(latest_v_str)

                if latest_t > curr_t:
                    pypi_page = info.get("project_url", "https://pypi.org/project/mediacompressor/")
                    return True, latest_v_str, pypi_page

    except Exception:
        pass  # Silently ignore network errors / offline state

    return False, CURRENT_VERSION, ""
