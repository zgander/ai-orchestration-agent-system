import ast
from pathlib import Path
from typing import List

from app.models.analysis_models import Symbol, SymbolKind, SymbolIndex
from app.config.settings import Settings
from app.utils.file_utils import find_files, safe_read_text, get_file_extension


class SymbolIndexBuilder:
    def __init__(self, settings: Settings):
        self.settings = settings

    def analyse(self, root_path: Path) -> SymbolIndex:
        symbols: List[Symbol] = []

        for file_path in find_files(root_path, self.settings):
            ext = get_file_extension(file_path)
            rel_path = str(file_path.relative_to(root_path)).replace('\\', '/')
            
            if ext == ".py":
                symbols.extend(self._analyse_python(file_path, rel_path))
                
            # For Phase 1, we only index Python symbols accurately using AST.
            # JS/TS regex indexing is too fragile for general symbols.

        return SymbolIndex(symbols=symbols)

    def _analyse_python(self, file_path: Path, rel_path: str) -> List[Symbol]:
        symbols: List[Symbol] = []
        content = safe_read_text(file_path)
        
        if not content:
            return symbols
            
        try:
            tree = ast.parse(content)
            
            # Module symbol
            module_name = Path(rel_path).stem
            symbols.append(Symbol(
                name=module_name,
                kind=SymbolKind.MODULE,
                file_path=rel_path,
                line_number=1
            ))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    symbols.append(Symbol(
                        name=node.name,
                        kind=SymbolKind.CLASS,
                        file_path=rel_path,
                        line_number=node.lineno
                    ))
                    
                    # Look for methods inside the class
                    for class_node in node.body:
                        if isinstance(class_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            symbols.append(Symbol(
                                name=class_node.name,
                                kind=SymbolKind.METHOD,
                                file_path=rel_path,
                                line_number=class_node.lineno,
                                parent_class=node.name
                            ))
                            
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Only add top-level functions (not methods or nested functions)
                    # We can approximate this by checking if it's in the top level of the AST
                    # Actually, ast.walk yields everything. A simple check is if it's in tree.body
                    if node in tree.body:
                        symbols.append(Symbol(
                            name=node.name,
                            kind=SymbolKind.FUNCTION,
                            file_path=rel_path,
                            line_number=node.lineno
                        ))
                        
        except SyntaxError:
            pass
            
        return symbols
