import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from app.models.analysis_models import EnvVariable
from app.config.settings import Settings
from app.utils.file_utils import find_files, safe_read_text, get_file_extension


class EnvDetector:
    def __init__(self, settings: Settings):
        self.settings = settings

    def analyse(self, root_path: Path) -> List[EnvVariable]:
        variables: List[EnvVariable] = []
        seen: Set[Tuple[str, str, int]] = set()

        def add_var(name, file_path, line_no, method, default=None):
            key = (name, file_path, line_no)
            if key not in seen:
                seen.add(key)
                variables.append(EnvVariable(
                    name=name,
                    file_path=file_path,
                    line_number=line_no,
                    access_method=method,
                    default_value=default
                ))

        for file_path in find_files(root_path, self.settings):
            ext = get_file_extension(file_path)
            rel_path = str(file_path.relative_to(root_path))
            filename = file_path.name
            
            # 1. Parse .env files (or examples)
            if ".env" in filename:
                content = safe_read_text(file_path)
                if content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            name = line.split('=', 1)[0].strip()
                            add_var(name, rel_path, i + 1, ".env file")
                continue

            # 2. Parse Code Files
            if ext == ".py":
                content = safe_read_text(file_path)
                if content:
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            # os.getenv("VAR") or os.environ.get("VAR")
                            if isinstance(node, ast.Call):
                                is_getenv = isinstance(node.func, ast.Attribute) and node.func.attr == "getenv"
                                is_environ_get = (isinstance(node.func, ast.Attribute) and node.func.attr == "get" and 
                                                  isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "environ")
                                
                                if (is_getenv or is_environ_get) and node.args and isinstance(node.args[0], ast.Constant):
                                    name = str(node.args[0].value)
                                    add_var(name, rel_path, node.lineno, "os.getenv / os.environ.get")
                                    
                            # os.environ["VAR"]
                            elif isinstance(node, ast.Subscript):
                                if isinstance(node.value, ast.Attribute) and node.value.attr == "environ":
                                    if isinstance(node.slice, ast.Constant):
                                        name = str(node.slice.value)
                                        add_var(name, rel_path, node.lineno, "os.environ[]")
                            
                            # BaseSettings classes (pydantic)
                            elif isinstance(node, ast.ClassDef):
                                is_settings = any(
                                    (isinstance(b, ast.Name) and b.id == "BaseSettings") or 
                                    (isinstance(b, ast.Attribute) and b.attr == "BaseSettings")
                                    for b in node.bases
                                )
                                if is_settings:
                                    # All annotations are treated as env vars
                                    for class_node in node.body:
                                        if isinstance(class_node, ast.AnnAssign) and isinstance(class_node.target, ast.Name):
                                            add_var(class_node.target.id, rel_path, class_node.lineno, "BaseSettings field")
                                            
                    except SyntaxError:
                        pass
                        
            elif ext in [".js", ".ts", ".jsx", ".tsx"]:
                content = safe_read_text(file_path)
                if content:
                    # process.env.VAR_NAME or process.env['VAR_NAME']
                    pattern = r"process\.env\.([a-zA-Z_][a-zA-Z0-9_]*)|process\.env\['([^']+)'\]|process\.env\[\"([^\"]+)\"\]"
                    for match in re.finditer(pattern, content):
                        name = match.group(1) or match.group(2) or match.group(3)
                        line_no = content[:match.start()].count('\n') + 1
                        add_var(name, rel_path, line_no, "process.env")

        return variables
