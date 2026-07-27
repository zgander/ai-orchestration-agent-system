import ast
import re
from pathlib import Path
from typing import List, Tuple

from app.models.analysis_models import APIEndpoint
from app.config.settings import Settings
from app.utils.file_utils import find_files, safe_read_text, get_file_extension


class APIDetector:
    def __init__(self, settings: Settings):
        self.settings = settings

    def analyse(self, root_path: Path) -> List[APIEndpoint]:
        endpoints: List[APIEndpoint] = []

        for file_path in find_files(root_path, self.settings):
            ext = get_file_extension(file_path)
            rel_path = str(file_path.relative_to(root_path))
            
            if ext == ".py":
                endpoints.extend(self._analyse_python(file_path, rel_path))
            elif ext in [".js", ".ts", ".jsx", ".tsx"]:
                endpoints.extend(self._analyse_javascript(file_path, rel_path))

        return endpoints

    def _analyse_python(self, file_path: Path, rel_path: str) -> List[APIEndpoint]:
        endpoints: List[APIEndpoint] = []
        content = safe_read_text(file_path)
        if not content:
            return endpoints

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return endpoints

        # Look for FastAPI / Flask decorators
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    # e.g., @app.get("/path") or @router.post(...)
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        attr_name = decorator.func.attr
                        method = attr_name.upper()
                        if method in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]:
                            # Attempt to extract path
                            path = "unknown"
                            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                path = str(decorator.args[0].value)
                            
                            framework = "FastAPI" if "app" in str(decorator.func.value) or "router" in str(decorator.func.value) else "Python API"
                            
                            endpoints.append(APIEndpoint(
                                method=method,
                                path=path,
                                handler_name=node.name,
                                file_path=rel_path,
                                line_number=node.lineno,
                                framework=framework
                            ))
                        # e.g., @app.route("/path", methods=["GET", "POST"])
                        elif attr_name == "route":
                            path = "unknown"
                            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                path = str(decorator.args[0].value)
                            
                            methods = ["GET"] # default for Flask
                            for keyword in decorator.keywords:
                                if keyword.arg == "methods" and isinstance(keyword.value, ast.List):
                                    methods = [el.value.upper() for el in keyword.value.elts if isinstance(el, ast.Constant)]
                            
                            for m in methods:
                                endpoints.append(APIEndpoint(
                                    method=m,
                                    path=path,
                                    handler_name=node.name,
                                    file_path=rel_path,
                                    line_number=node.lineno,
                                    framework="Flask"
                                ))
                            
        return endpoints

    def _analyse_javascript(self, file_path: Path, rel_path: str) -> List[APIEndpoint]:
        endpoints: List[APIEndpoint] = []
        content = safe_read_text(file_path)
        if not content:
            return endpoints

        # Regex for Express.js / Next.js API routes
        # Matches: app.get('/path', ...) or router.post("/path", ...)
        pattern = r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
        
        for match in re.finditer(pattern, content):
            method = match.group(1).upper()
            path = match.group(2)
            line_no = content[:match.start()].count('\n') + 1
            
            endpoints.append(APIEndpoint(
                method=method,
                path=path,
                handler_name="anonymous", # Hard to extract statically with regex
                file_path=rel_path,
                line_number=line_no,
                framework="Express"
            ))

        return endpoints
