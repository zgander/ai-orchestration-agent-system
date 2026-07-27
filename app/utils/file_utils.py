import os
from pathlib import Path
from typing import Optional, List, Generator
from app.config.settings import Settings


def is_ignored(path: Path, settings: Settings) -> bool:
    for part in path.parts:
        if part in settings.ignored_directories:
            return True
    return False


def is_binary(path: Path, settings: Settings) -> bool:
    if path.suffix.lower() in settings.binary_extensions:
        return True
    
    # Try reading magic bytes
    try:
        with open(path, 'tr') as check_file:
            check_file.read(1024)
            return False
    except UnicodeDecodeError:
        return True
    except Exception:
        # If we can't read it, treat it cautiously
        return False


def is_too_large(path: Path, max_mb: int) -> bool:
    try:
        return path.stat().st_size > (max_mb * 1024 * 1024)
    except OSError:
        return False


def safe_read_text(path: Path) -> Optional[str]:
    encodings = ['utf-8', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except Exception:
            break
            
    return None


def find_files(root: Path, settings: Settings) -> Generator[Path, None, None]:
    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)
        
        # Filter directories in-place to avoid walking ignored ones
        dirnames[:] = [d for d in dirnames if not is_ignored(current_dir / d, settings)]
        
        for filename in filenames:
            file_path = current_dir / filename
            if not is_ignored(file_path, settings):
                yield file_path


def get_file_extension(path: Path) -> str:
    return path.suffix.lower()


def calculate_dir_size(path: Path) -> int:
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size
