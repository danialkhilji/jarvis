import os
import fnmatch
from pathlib import Path
import config

write_confirm_callback = None


def _resolve_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def _is_path_allowed(path: str) -> bool:
    abs_path = _resolve_path(path)
    return any(abs_path.startswith(d) for d in config.ALLOWED_DIRECTORIES)


def read_file(path: str) -> str:
    """Read the contents of a file. Returns the text content or an error message."""
    path = _resolve_path(path)
    if not _is_path_allowed(path):
        return f"Access denied: {path} is outside allowed directories. Allowed: {', '.join(config.ALLOWED_DIRECTORIES)}"
    p = Path(path)
    if not p.exists():
        return f"File not found: {path}"
    content = p.read_text(errors="replace")
    if len(content) > 10000:
        content = content[:10000] + "\n... (truncated)"
    return content


def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates the file if it doesn't exist, overwrites if it does."""
    path = _resolve_path(path)
    if not _is_path_allowed(path):
        return f"Access denied: {path} is outside allowed directories. Allowed: {', '.join(config.ALLOWED_DIRECTORIES)}"
    if write_confirm_callback:
        confirmed = write_confirm_callback(path, content)
        if not confirmed:
            return "Write cancelled by user."
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Successfully wrote {len(content)} characters to {path}"


def list_directory(path: str) -> str:
    """List files and folders in a directory with sizes."""
    path = _resolve_path(path)
    if not _is_path_allowed(path):
        return f"Access denied: {path} is outside allowed directories. Allowed: {', '.join(config.ALLOWED_DIRECTORIES)}"
    p = Path(path)
    if not p.is_dir():
        return f"Not a directory: {path}"
    entries = []
    for item in sorted(p.iterdir()):
        prefix = "[DIR]  " if item.is_dir() else "[FILE] "
        size = ""
        if item.is_file():
            s = item.stat().st_size
            if s < 1024:
                size = f" ({s} B)"
            elif s < 1024 * 1024:
                size = f" ({s // 1024} KB)"
            else:
                size = f" ({s // (1024 * 1024)} MB)"
        entries.append(f"{prefix}{item.name}{size}")
    if not entries:
        return "Directory is empty."
    return "\n".join(entries[:100])


def search_files(directory: str, pattern: str) -> str:
    """Search for files by name pattern (e.g. '*.md', 'report*') in a directory tree."""
    directory = _resolve_path(directory)
    if not _is_path_allowed(directory):
        return f"Access denied: {directory} is outside allowed directories. Allowed: {', '.join(config.ALLOWED_DIRECTORIES)}"
    matches = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                matches.append(os.path.join(root, name))
                if len(matches) >= 50:
                    break
        if len(matches) >= 50:
            break
    if not matches:
        return f"No files matching '{pattern}' found in {directory}"
    result = "\n".join(matches)
    if len(matches) == 50:
        result += "\n... (showing first 50 results)"
    return result
