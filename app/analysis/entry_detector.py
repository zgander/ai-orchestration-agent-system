import re
from pathlib import Path
from typing import List

from app.models.analysis_models import EntryPoint
from app.config.settings import Settings
from app.utils.file_utils import find_files, safe_read_text, get_file_extension


class EntryDetector:
    def __init__(self, settings: Settings):
        self.settings = settings
        
        self.filename_rules = [
            (r"^main\.py$", 0.7, "Python main script"),
            (r"^app\.py$", 0.7, "Python app script"),
            (r"^server\.js$", 0.7, "Node.js server entry"),
            (r"^index\.js$", 0.7, "Node.js index script"),
            (r"^main\.tsx?$", 0.7, "React/TS main file"),
            (r"^index\.tsx?$", 0.7, "React/TS index file"),
        ]

        self.content_rules = [
            (r"if\s+__name__\s*==\s*['\"]__main__['\"]\s*:", ".py", 0.9, "Python __main__ block"),
            (r"app\s*=\s*FastAPI\(", ".py", 0.95, "FastAPI application instance"),
            (r"Flask\(__name__\)", ".py", 0.9, "Flask application instance"),
            (r"app\.listen\(", ".js", 0.9, "Express app.listen call"),
            (r"app\.listen\(", ".ts", 0.9, "Express app.listen call"),
            (r"createRoot\(", ".jsx", 0.85, "React 18+ createRoot"),
            (r"createRoot\(", ".tsx", 0.85, "React 18+ createRoot"),
            (r"ReactDOM\.render\(", ".jsx", 0.85, "React 17- ReactDOM.render"),
            (r"ReactDOM\.render\(", ".tsx", 0.85, "React 17- ReactDOM.render"),
        ]

    def analyse(self, root_path: Path) -> List[EntryPoint]:
        entries: List[EntryPoint] = []

        for file_path in find_files(root_path, self.settings):
            rel_path = str(file_path.relative_to(root_path))
            filename = file_path.name
            ext = get_file_extension(file_path)

            # 1. Check filename rules
            for pattern, conf, desc in self.filename_rules:
                if re.match(pattern, filename):
                    entries.append(EntryPoint(
                        file_path=rel_path,
                        line_number=1,
                        pattern=pattern,
                        confidence=conf,
                        description=desc
                    ))
                    break # Usually only one filename rule matches

            # 2. Check content rules
            content = None
            for pattern, target_ext, conf, desc in self.content_rules:
                if ext == target_ext or target_ext == ".*":
                    if content is None:
                        content = safe_read_text(file_path)
                    
                    if content:
                        # Find all matches to get line numbers
                        for match in re.finditer(pattern, content):
                            # Calculate line number
                            line_no = content[:match.start()].count('\n') + 1
                            entries.append(EntryPoint(
                                file_path=rel_path,
                                line_number=line_no,
                                pattern=pattern,
                                confidence=conf,
                                description=desc
                            ))
                            break # Only record the first occurrence of a pattern per file

        # Sort by confidence descending
        entries.sort(key=lambda e: e.confidence, reverse=True)
        return entries
