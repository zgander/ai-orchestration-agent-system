from app.analysis.entry_detector import EntryDetector

def test_entry_detector(tmp_path, mock_settings):
    # Setup
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    main_py = src_dir / "main.py"
    main_py.write_text("""
import sys

def main():
    print("Hello")

if __name__ == '__main__':
    main()
""")

    app_js = tmp_path / "server.js"
    app_js.write_text("""
const express = require('express');
const app = express();

app.listen(3000, () => console.log('started'));
""")

    detector = EntryDetector(mock_settings)
    entries = detector.analyse(tmp_path)
    
    assert len(entries) >= 4  # main.py (filename + content), server.js (filename + content)
    
    # Check Python content entry
    py_main = [e for e in entries if '__main__' in e.description]
    assert len(py_main) == 1
    assert py_main[0].line_number == 7
    assert py_main[0].confidence == 0.9
    
    # Check JS content entry
    js_main = [e for e in entries if 'app.listen' in e.description]
    assert len(js_main) == 1
    assert js_main[0].line_number == 5
    assert js_main[0].confidence == 0.9
    
    # Check filename entries
    filenames = [e.file_path for e in entries]
    assert "src\\main.py" in filenames or "src/main.py" in filenames
    assert "server.js" in filenames
