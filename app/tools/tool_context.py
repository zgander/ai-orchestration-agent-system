import threading

_context = threading.local()

def set_root_path(path: str):
    _context.root_path = path

def get_root_path() -> str:
    return getattr(_context, "root_path", ".")
