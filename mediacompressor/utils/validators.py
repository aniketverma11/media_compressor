import os

def parse_target_size_mb(value_str: str) -> float | None:
    """Parses target size string into MB float."""
    try:
        val = float(value_str.strip().replace("MB", "").replace("mb", ""))
        return val if val > 0 else None
    except ValueError:
        return None

def parse_percentage(value_str: str) -> float | None:
    """Parses percentage string into float between 1 and 99."""
    try:
        val = float(value_str.strip().replace("%", ""))
        return val if 1 <= val < 100 else None
    except ValueError:
        return None

def validate_output_path(path: str) -> tuple[bool, str]:
    """Validates whether output path directory is writable."""
    if not path:
        return False, "Output path cannot be empty."
    dir_name = os.path.dirname(os.path.abspath(path))
    if not os.path.exists(dir_name):
        try:
            os.makedirs(dir_name, exist_ok=True)
        except Exception as e:
            return False, f"Cannot create directory: {e}"
    if not os.access(dir_name, os.W_OK):
        return False, f"Directory is not writable: {dir_name}"
    return True, ""
