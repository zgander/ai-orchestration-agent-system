from app.analysis.symbol_index import SymbolIndexBuilder
from app.models.analysis_models import SymbolKind

def test_symbol_index_python(tmp_path, mock_settings):
    # Setup
    py_file = tmp_path / "models.py"
    py_file.write_text("""
def helper_function():
    pass

class User:
    def __init__(self):
        pass
        
    def save(self):
        def nested():
            pass
        pass

async def async_helper():
    pass
""")

    builder = SymbolIndexBuilder(mock_settings)
    index = builder.analyse(tmp_path)
    
    symbols = index.symbols
    
    # Module
    assert any(s.name == "models" and s.kind == SymbolKind.MODULE for s in symbols)
    
    # Functions
    assert any(s.name == "helper_function" and s.kind == SymbolKind.FUNCTION for s in symbols)
    assert any(s.name == "async_helper" and s.kind == SymbolKind.FUNCTION for s in symbols)
    
    # Class
    assert any(s.name == "User" and s.kind == SymbolKind.CLASS for s in symbols)
    
    # Methods
    assert any(s.name == "__init__" and s.kind == SymbolKind.METHOD and s.parent_class == "User" for s in symbols)
    assert any(s.name == "save" and s.kind == SymbolKind.METHOD and s.parent_class == "User" for s in symbols)
    
    # Nested function should not be top-level (we don't strictly test absence here unless we want to, 
    # but the logic specifically skips nested by checking `node in tree.body`)
    assert not any(s.name == "nested" and s.kind == SymbolKind.FUNCTION for s in symbols)
